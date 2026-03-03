"""
Smart LLM Router

Intelligently routes prompts between fast (System 1) and strong (System 2) models,
evaluates quality via the judge, applies fallback, and logs metrics.
"""

import subprocess
import time
import uuid
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

from app.cache import Cache
from app.evaluator import JudgeEvaluator
from app.metrics import MetricsLogger
from config import settings


@dataclass
class RouterResult:
    answer: str
    route: str
    model_used: str
    fallback_used: bool
    judge: Dict[str, Any]
    metrics: Dict[str, Any]
    trace_id: str
    cache_hit: bool
    routing_reason: str


class SmartRouter:
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        evaluator: Optional[JudgeEvaluator] = None,
        cache: Optional[Cache] = None,
        metrics_logger: Optional[MetricsLogger] = None,
    ):
        self.llm_client = llm_client or self._create_llm_client()
        self.evaluator = evaluator or JudgeEvaluator()
        self.cache = cache or Cache()
        self.metrics_logger = metrics_logger or MetricsLogger()

    def _create_llm_client(self):
        from app.llm_client import LLMClient

        return LLMClient()

    def _call_model(self, route: str, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
        return self.llm_client.call_model(route, messages, max_tokens, temperature)

    def _evaluate(self, messages: List[Dict[str, str]], response: str) -> Dict[str, Any]:
        return self.evaluator.evaluate_response(messages, response)

    def process(
        self,
        messages: List[Dict[str, str]],
        mode: str = "auto",
        needs_citations: bool = False,
        response_format: str = "text",
        max_tokens: int = settings.MAX_TOKENS,
        temperature: float = 0.2,
    ) -> RouterResult:
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        cache_key = f"{messages[-1]['content']}_{mode}"

        cached = self.cache.get(cache_key)
        if cached:
            cached["trace_id"] = trace_id
            cached["metrics"]["latency_ms"] = (time.time() - start_time) * 1000
            cached["cache_hit"] = True
            self.metrics_logger.log_request(cached)
            return RouterResult(cache_hit=True, **cached)

        prompt_text = messages[-1]["content"]
        route, reason = mode_reason(mode, prompt_text, needs_citations)

        llm_start = time.time()
        response = self._call_model(route, messages, max_tokens, temperature)
        llm_latency = (time.time() - llm_start) * 1000

        judge_result = self._evaluate(messages, response)
        fallback_used = False

        if judge_result["should_fallback"] and route == "fast":
            fallback_used = True
            fallback_start = time.time()
            response = self._call_model("strong", messages, max_tokens, temperature)
            llm_latency += (time.time() - fallback_start) * 1000
            judge_result = self._evaluate(messages, response)
            route = "strong"

        latency_ms = (time.time() - start_time) * 1000
        cost_units = calculate_cost_units(route, len(response.split()), fallback_used)

        response_tokens = count_tokens(response)
        metrics = {
            "latency_ms": latency_ms,
            "llm_latency_ms": llm_latency,
            "judge_latency_ms": 30,
            "cache_hit": False,
            "cost_units": cost_units,
            "fallback_used": fallback_used,
            "prompt_tokens": count_tokens(prompt_text),
            "response_tokens": response_tokens,
            "routing_reason": reason,
        }
        metrics.update(sample_resources())

        result = RouterResult(
            answer=response,
            route=route,
            model_used=self.llm_client.get_model_name(route),
            fallback_used=fallback_used,
            judge=judge_result,
            metrics=metrics,
            trace_id=trace_id,
            cache_hit=False,
            routing_reason=reason,
        )

        self.cache.set(cache_key, asdict(result))
        self.metrics_logger.log_request(asdict(result))
        return result


def count_tokens(text: str) -> int:
    return max(1, len(text.strip().split()))


def mode_reason(mode: str, prompt: str, needs_citations: bool) -> Tuple[str, str]:
    prompt_lower = prompt.lower()
    if mode in {"fast", "strong"}:
        return mode, f"mode override ({mode})"
    if needs_citations:
        return "strong", "needs citations"
    if "json" in prompt_lower or "schema" in prompt_lower:
        return "strong", "schema keyword"
    if len(prompt) > settings.ROUTING_PROMPT_LENGTH_THRESHOLD:
        return "strong", "prompt length"
    if any(keyword in prompt_lower for keyword in ["prove", "derive", "debug", "analyze", "compare"]):
        return "strong", "analysis keyword"
    return "fast", "default fast heuristics"


def calculate_cost_units(route: str, token_count: int, fallback_used: bool) -> float:
    base_cost = 1.0 if route == "fast" else 3.0
    if fallback_used:
        base_cost += 2.0
    return base_cost * (token_count / 100)


def sample_resources() -> Dict[str, Any]:
    """
    Best-effort capture of process/system resource usage.
    Returns only fields that were successfully measured.
    """
    measurements: Dict[str, Any] = {}

    # CPU and RAM (process + system)
    try:
        import psutil  # lightweight dependency, declared in requirements

        proc = psutil.Process()
        with proc.oneshot():
            # cpu_percent needs a prior call to give meaningful data; using interval=0 for immediate sample.
            measurements["proc_cpu_percent"] = proc.cpu_percent(interval=0)
            measurements["proc_rss_mb"] = round(proc.memory_info().rss / (1024 * 1024), 2)
        vm = psutil.virtual_memory()
        measurements["system_mem_percent"] = vm.percent
    except Exception:
        # Swallow errors so routing never fails on telemetry
        pass

    # GPU (NVIDIA only, via nvidia-smi)
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=1,
        )
        line = output.strip().splitlines()[0]
        util_str, mem_str = [part.strip() for part in line.split(",")]
        measurements["gpu_util_percent"] = float(util_str)
        measurements["gpu_mem_mb"] = float(mem_str)
    except Exception:
        pass

    return measurements
