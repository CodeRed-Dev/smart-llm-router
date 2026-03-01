"""
LLM Router Module

Handles the core routing logic for deciding between fast and strong models
based on request characteristics and implementing fallback mechanisms.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import uuid

from app.llm_client import LLMClient
from app.evaluator import JudgeEvaluator
from app.cache import Cache
from app.metrics import MetricsLogger

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    mode: str = "auto"  # auto, fast, strong
    needs_citations: bool = False
    response_format: str = "text"
    max_tokens: int = 512
    temperature: float = 0.2

class JudgeResult(BaseModel):
    correctness: int
    completeness: int
    format_ok: bool
    hallucination_risk: int
    should_fallback: bool
    notes: str

class ChatResponse(BaseModel):
    answer: str
    route: str
    model_used: str
    fallback_used: bool
    judge: JudgeResult
    metrics: Dict[str, Any]
    trace_id: str

@router.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint that routes requests to appropriate LLM models
    with quality evaluation and fallback.
    """
    trace_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        # Initialize components
        llm_client = LLMClient()
        evaluator = JudgeEvaluator()
        cache = Cache()
        metrics_logger = MetricsLogger()

        # Check cache first
        cache_key = f"{request.messages[-1].content}_{request.mode}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return ChatResponse(
                **cached_response,
                metrics={"latency_ms": (time.time() - start_time) * 1000, "cache_hit": True},
                trace_id=trace_id
            )

        # Determine routing
        route = request.mode
        if route == "auto":
            route = determine_route(request)

        # Get LLM response
        llm_start = time.time()
        response = await llm_client.call_model(route, request.messages, request.max_tokens, request.temperature)
        llm_latency = (time.time() - llm_start) * 1000

        # Evaluate response
        judge_start = time.time()
        judge_result = await evaluator.evaluate_response(request.messages, response)
        judge_latency = (time.time() - judge_start) * 1000

        # Fallback if needed
        fallback_used = False
        if judge_result.should_fallback and route == "fast":
            fallback_start = time.time()
            response = await llm_client.call_model("strong", request.messages, request.max_tokens, request.temperature)
            fallback_used = True
            judge_result = await evaluator.evaluate_response(request.messages, response)
            llm_latency += (time.time() - fallback_start) * 1000

        # Prepare response
        chat_response = ChatResponse(
            answer=response,
            route=route,
            model_used=llm_client.get_model_name(route),
            fallback_used=fallback_used,
            judge=judge_result,
            metrics={
                "latency_ms": (time.time() - start_time) * 1000,
                "llm_latency_ms": llm_latency,
                "judge_latency_ms": judge_latency,
                "cache_hit": False,
                "cost_units": calculate_cost_units(route, len(response.split()), fallback_used)
            },
            trace_id=trace_id
        )

        # Cache response
        cache.set(cache_key, chat_response.dict())

        # Log metrics
        await metrics_logger.log_request(chat_response)

        return chat_response

    except Exception as e:
        # Log error and return appropriate response
        await metrics_logger.log_error(trace_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

def determine_route(request: ChatRequest) -> str:
    """
    Determine routing based on heuristics from the product spec.
    """
    prompt = request.messages[-1].content

    # Route to strong if:
    if request.needs_citations:
        return "strong"
    if any(keyword in prompt.lower() for keyword in ["prove", "derive", "debug", "analyze", "compare"]):
        return "strong"
    if len(prompt) > 200:  # threshold
        return "strong"
    if "json" in prompt.lower() or "schema" in prompt.lower():
        return "strong"

    return "fast"

def calculate_cost_units(route: str, token_count: int, fallback_used: bool) -> float:
    """
    Calculate relative cost units (since we're using local Ollama).
    """
    base_cost = 1.0 if route == "fast" else 3.0
    if fallback_used:
        base_cost += 2.0  # additional cost for fallback
    return base_cost * (token_count / 100)  # rough estimate