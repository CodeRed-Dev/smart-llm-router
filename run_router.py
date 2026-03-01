"""
Interactive runner for the Smart LLM Router (System1/System2 design).

It takes queries from a local file or from the command line, routes them through the
fast (System1) and strong (System2) models locally, evaluates output via the judge,
and prints a live visualization of routing + fallback + metrics.
"""

import argparse
import json
import logging
import math
import sys
from pathlib import Path
from typing import List, Dict, Any

from app.router import SmartRouter, RouterResult

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)


def load_queries_from_file(path: Path) -> List[Dict[str, Any]]:
    content = path.read_text()
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    queries = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        queries.append(json.loads(line))
    return queries


def visualize_flow(result: RouterResult, prompt_label: str):
    markers = []
    markers.append("[Router] System1" if result.route == "fast" else "[Router] System2")
    markers.append(f"[LLM] {result.model_used}")
    judge = result.judge
    judge_line = f"[Judge] correctness={judge['correctness']} fallback={judge['should_fallback']}"
    markers.append(judge_line)
    if result.fallback_used:
        markers.append("[Fallback] rerouted to strong model")
    metrics = result.metrics
    metrics_line = f"[Metrics] latency={metrics['latency_ms']:.0f}ms cost={metrics['cost_units']:.2f}"
    markers.append(metrics_line)

    print("\n".join(f"  {marker}" for marker in markers))
    print(f"  -> Prompt: {prompt_label}")
    print("  " + "-" * 48)
    print(f"  -> Routing reason: {result.routing_reason}")


def estimate_tokens(text: str) -> int:
    token_count = len(text.split())
    return max(1, token_count)


def render_token_graph(prompt_tokens: int, response_tokens: int):
    scale = 40
    total = max(1, prompt_tokens + response_tokens)
    def bar(count: int):
        length = min(scale, max(1, math.ceil((count / total) * scale)))
        return "#" * length + "-" * (scale - length)

    print("  Token breakdown:")
    print(f"    Prompt   ({prompt_tokens} tokens) |{bar(prompt_tokens)}|")
    print(f"    Response ({response_tokens} tokens) |{bar(response_tokens)}|")
    print(f"    Total     {prompt_tokens + response_tokens} tokens\n")


def run_router(queries: List[Dict[str, Any]]):
    router = SmartRouter()
    for idx, query in enumerate(queries, start=1):
        prompt = query["messages"][-1]["content"]
        result = router.process(
            query["messages"],
            mode=query.get("mode", "auto"),
            needs_citations=query.get("needs_citations", False),
            response_format=query.get("response_format", "text"),
            max_tokens=query.get("max_tokens", 512),
            temperature=query.get("temperature", 0.2),
        )

        print(f"\n=== Run {idx}: System1/System2 Routing ===")
        visualize_flow(result, prompt_label=prompt.splitlines()[0])
        print(f"  -> Answer: {result.answer}")
        print(f"  -> Trace ID: {result.trace_id}")
        print(f"  -> Judge notes: {result.judge['notes']}")
        prompt_tokens = result.metrics.get("prompt_tokens", estimate_tokens(prompt))
        response_tokens = result.metrics.get("response_tokens", estimate_tokens(result.answer))
        render_token_graph(prompt_tokens, response_tokens)

    summary = router.metrics_logger.get_metrics_summary()
    print("\n=== Session Metrics Summary ===")
    for key, value in summary.items():
        print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(description="Run the local Smart LLM Router simulation.")
    parser.add_argument(
        "--queries-file",
        type=Path,
        default=Path("samples/demo_queries.json"),
        help="Path to a JSON file or JSON lines file with query payloads.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Run a single prompt instead of reading from a file (CLI mode).",
    )
    parser.add_argument(
        "--needs-citations",
        action="store_true",
        help="Set needs_citations=true for the single prompt mode.",
    )

    args = parser.parse_args()
    if args.prompt:
        queries = [
            {
                "messages": [{"role": "user", "content": args.prompt}],
                "mode": "auto",
                "needs_citations": args.needs_citations,
                "response_format": "text",
                "max_tokens": 512,
                "temperature": 0.2,
            }
        ]
    else:
        queries = load_queries_from_file(args.queries_file)

    run_router(queries)


if __name__ == "__main__":
    main()
