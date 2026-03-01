"""
Metrics Module

Handles metrics collection, aggregation, and exposure for monitoring
the LLM router's performance and quality.
"""

from fastapi import APIRouter
from typing import Dict, Any
import time
from app.storage import MetricsStorage

router = APIRouter()
metrics_storage = MetricsStorage()

@router.get("/metrics")
async def get_metrics():
    """
    Get aggregated metrics for monitoring.
    Returns Prometheus-compatible format.
    """
    summary = metrics_storage.get_metrics_summary()

    # Format as Prometheus metrics
    metrics_output = f"""# HELP smart_llm_router_requests_total Total number of requests processed
# TYPE smart_llm_router_requests_total counter
smart_llm_router_requests_total {summary.get('total_requests', 0)}

# HELP smart_llm_router_latency_avg_ms Average request latency in milliseconds
# TYPE smart_llm_router_latency_avg_ms gauge
smart_llm_router_latency_avg_ms {summary.get('avg_latency_ms', 0)}

# HELP smart_llm_router_cost_avg_units Average cost in relative units
# TYPE smart_llm_router_cost_avg_units gauge
smart_llm_router_cost_avg_units {summary.get('avg_cost_units', 0)}

# HELP smart_llm_router_fallback_rate Rate of requests that used fallback
# TYPE smart_llm_router_fallback_rate gauge
smart_llm_router_fallback_rate {summary.get('fallback_rate', 0)}

# HELP smart_llm_router_judge_correctness_avg Average judge correctness score
# TYPE smart_llm_router_judge_correctness_avg gauge
smart_llm_router_judge_correctness_avg {summary.get('avg_judge_correctness', 0)}

# HELP smart_llm_router_error_rate Rate of requests that resulted in errors
# TYPE smart_llm_router_error_rate gauge
smart_llm_router_error_rate {summary.get('error_rate', 0)}
"""

    return metrics_output

class MetricsLogger:
    def __init__(self):
        self.storage = MetricsStorage()

    async def log_request(self, response_data: Dict[str, Any]):
        """Log a successful request."""
        self.storage.save_request(response_data["trace_id"], {
            "route": response_data["route"],
            "model_used": response_data["model_used"],
            "fallback_used": response_data["fallback_used"],
            "latency_ms": response_data["metrics"]["latency_ms"],
            "llm_latency_ms": response_data["metrics"]["llm_latency_ms"],
            "judge_latency_ms": response_data["metrics"]["judge_latency_ms"],
            "cache_hit": response_data["metrics"]["cache_hit"],
            "cost_units": response_data["metrics"]["cost_units"],
            "judge": response_data["judge"]
        })

    async def log_error(self, trace_id: str, error_message: str):
        """Log an error."""
        self.storage.save_error(trace_id, error_message)