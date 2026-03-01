"""
Local Demo Runner

A simplified dispatcher simulation to trace routing, judging, fallback, and metrics locally
without requiring real LLMs or Ollama. This script mirrors the Smart LLM Router flow with stubbed
responses and deterministic judge checks so you can validate each component step-by-step.
"""

import time
from dataclasses import dataclass, field
from pprint import pprint
from typing import Dict, List, Tuple


FAST_RESPONSE = "Fast model gives a concise answer focused on key points."
STRONG_RESPONSE = "Strong model expands the answer with examples, reasoning, and any requested format."

PROMPTS = [
    {"content": "Explain quantum computing in simple terms.", "mode": "auto", "needs_citations": False},
    {
        "content": "Provide a JSON schema for a purchase order and explain each field.",
        "mode": "auto",
        "needs_citations": True,
    },
    {
        "content": "Debug this Python function:\n\n```python\ndef power(x, n):\n    return x * power(x, n - 1)\n```",
        "mode": "auto",
        "needs_citations": False,
    },
]


def determine_route(prompt: str, mode: str, needs_citations: bool) -> str:
    if mode in ("fast", "strong"):
        return mode
    heuristics = [
        (needs_citations, "needs citations"),
        ("json" in prompt.lower(), "contains JSON/schema vocabulary"),
        (len(prompt) > 200, "prompt length > 200"),
        (
            any(keyword in prompt.lower() for keyword in ["prove", "derive", "debug", "analyze", "compare"]),
            "analysis keyword detected",
        ),
    ]
    for condition, reason in heuristics:
        if condition:
            print(f"  -> Routing hint triggered: {reason}")
            return "strong"
    return "fast"


def call_stub(route: str, prompt: str) -> Tuple[str, float]:
    latency = 0.05 if route == "fast" else 0.15
    response = FAST_RESPONSE if route == "fast" else STRONG_RESPONSE
    return response, latency * 1000


def evaluate_response(response: str, mode: str) -> Dict[str, object]:
    base_score = 6 if mode == "fast" else 8
    completeness = base_score
    correctness = base_score
    format_ok = "json" not in response.lower()
    if "json schema" in response.lower():
        format_ok = True
    hallucination_risk = 3 if mode == "strong" else 5
    should_fallback = correctness < 7 or not format_ok
    return {
        "correctness": correctness,
        "completeness": completeness,
        "format_ok": format_ok,
        "hallucination_risk": hallucination_risk,
        "should_fallback": should_fallback,
        "notes": "Checker simulated based on response length and keywords",
    }


def calculate_cost(route: str, token_count: int, fallback_used: bool) -> float:
    base = 1.0 if route == "fast" else 3.0
    if fallback_used:
        base += 2.0
    return base * (token_count / 100)


class DemoMetrics:
    def __init__(self):
        self.total_requests = 0
        self.total_latency = 0.0
        self.total_cost = 0.0
        self.fallbacks = 0
        self.entries: List[Dict[str, object]] = []

    def log(self, data: Dict[str, object]):
        self.total_requests += 1
        self.total_latency += data["latency_ms"]
        self.total_cost += data["cost_units"]
        if data["fallback_used"]:
            self.fallbacks += 1
        self.entries.append(data)

    def summary(self) -> Dict[str, object]:
        return {
            "total_requests": self.total_requests,
            "avg_latency_ms": self.total_latency / self.total_requests if self.total_requests else 0,
            "avg_cost_units": self.total_cost / self.total_requests if self.total_requests else 0,
            "fallback_rate": self.fallbacks / self.total_requests if self.total_requests else 0,
        }


class DemoCache:
    def __init__(self):
        self.storage: Dict[str, Tuple[Dict[str, object], float]] = {}
        self.ttl = 120

    def get(self, key: str):
        entry = self.storage.get(key)
        if not entry:
            return None
        value, timestamp = entry
        if time.time() - timestamp < self.ttl:
            print("  -> Cache hit for prompt.")
            return value
        del self.storage[key]
        return None

    def set(self, key: str, value: Dict[str, object]):
        self.storage[key] = (value, time.time())


def run_demo():
    metrics = DemoMetrics()
    cache = DemoCache()

    print("\n=== Scaled-down Smart Dispatcher Demo ===\n")
    for idx, prompt_meta in enumerate(PROMPTS, start=1):
        prompt = prompt_meta["content"]
        mode = prompt_meta["mode"]
        needs_citations = prompt_meta["needs_citations"]
        cache_key = f"{prompt[:60]}_{mode}"

        print(f"\nRequest #{idx}")
        print(f"Prompt: {prompt.splitlines()[0]}")
        print(f"Mode: {mode} (needs_citations={needs_citations})")

        cached = cache.get(cache_key)
        if cached:
            metrics.log(cached["metrics"])
            print("  -> Returned cached response.")
            continue

        route = determine_route(prompt, mode, needs_citations)
        response, llm_latency = call_stub(route, prompt)
        judge_result = evaluate_response(response, route)
        fallback_used = False

        if judge_result["should_fallback"] and route == "fast":
            print("  -> Judge requested fallback. Switching to strong model.")
            fallback_used = True
            route = "strong"
            response, extra_latency = call_stub(route, prompt)
            llm_latency += extra_latency
            judge_result = evaluate_response(response, route)

        latency_ms = llm_latency + 30  # add judge processing pad
        cost_units = calculate_cost(route, len(response.split()), fallback_used)
        response_record = {
            "answer": response,
            "route": route,
            "model_used": "strong model" if route == "strong" else "fast model",
            "fallback_used": fallback_used,
            "judge": judge_result,
            "metrics": {
                "latency_ms": latency_ms,
                "llm_latency_ms": llm_latency,
                "judge_latency_ms": 30,
                "cache_hit": False,
                "cost_units": cost_units,
                "fallback_used": fallback_used,
            },
        }
        cache.set(cache_key, response_record)
        metrics.log(response_record["metrics"])

        pprint(
            {
                "route_selected": route,
                "fallback_used": fallback_used,
                "judge": judge_result,
                "metrics": response_record["metrics"],
            }
        )

    print("\n--- Demo Metrics Summary ---")
    pprint(metrics.summary())


if __name__ == "__main__":
    run_demo()
