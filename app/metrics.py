"""
In-memory metrics logging for the Smart LLM Router.
"""

from typing import Any, Dict, List


class MetricsLogger:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def log_request(self, response_data: Dict[str, Any]):
        entry = {
            "trace_id": response_data["trace_id"],
            "route": response_data["route"],
            "model_used": response_data["model_used"],
            "fallback_used": response_data["fallback_used"],
            "latency_ms": response_data["metrics"]["latency_ms"],
            "llm_latency_ms": response_data["metrics"]["llm_latency_ms"],
            "judge_latency_ms": response_data["metrics"]["judge_latency_ms"],
            "cache_hit": response_data["cache_hit"],
            "cost_units": response_data["metrics"]["cost_units"],
            "judge": response_data["judge"],
            "routing_reason": response_data["metrics"].get("routing_reason"),
            "prompt_tokens": response_data["metrics"].get("prompt_tokens"),
            "response_tokens": response_data["metrics"].get("response_tokens"),
        }
        self.records.append(entry)

    def log_error(self, trace_id: str, error_message: str):
        self.records.append({"trace_id": trace_id, "error_message": error_message})

    def get_metrics_summary(self) -> Dict[str, Any]:
        successful = [r for r in self.records if "latency_ms" in r]
        total_requests = len(successful)
        if total_requests == 0:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0,
                "avg_cost_units": 0,
                "fallback_rate": 0,
                "avg_judge_correctness": 0,
                "error_rate": len([r for r in self.records if "error_message" in r]) or 0,
            }

        total_latency = sum(r["latency_ms"] for r in successful)
        total_cost = sum(r["cost_units"] for r in successful)
        total_fallbacks = sum(1 for r in successful if r["fallback_used"])
        avg_correctness = sum(r["judge"]["correctness"] for r in successful) / total_requests
        error_count = len([r for r in self.records if "error_message" in r])

        return {
            "total_requests": total_requests,
            "avg_latency_ms": total_latency / total_requests,
            "avg_cost_units": total_cost / total_requests,
            "fallback_rate": total_fallbacks / total_requests,
            "avg_judge_correctness": avg_correctness,
            "error_rate": error_count / (total_requests + error_count) if total_requests + error_count else 0,
        }
