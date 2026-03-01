"""Wrapper that runs `run_router` with structured logging and a rich terminal summary."""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.router import SmartRouter

LOG_PATH = Path("logs/router_sessions.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("router.session")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger.addHandler(handler)


def load_queries_from_file(path: Path) -> List[Dict[str, Any]]:
    content = path.read_text(encoding="utf-8")
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    result: List[Dict[str, Any]] = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        result.append(json.loads(line))
    return result


def estimate_tokens(text: str) -> int:
    token_count = len(text.split())
    return max(1, token_count)


def render_token_graph(prompt_tokens: int, response_tokens: int) -> str:
    scale = 40
    total = max(1, prompt_tokens + response_tokens)

    def bar(count: int) -> str:
        length = min(scale, max(1, math.ceil((count / total) * scale)))
        return "#" * length + "-" * (scale - length)

    prompt_row = f"    Prompt   ({prompt_tokens} tokens) |{bar(prompt_tokens)}|"
    response_row = f"    Response ({response_tokens} tokens) |{bar(response_tokens)}|"
    total_row = f"    Total     {prompt_tokens + response_tokens} tokens"
    return "\n".join([prompt_row, response_row, total_row])


def rich_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"{title}")
    print("=" * 72)


def pretty_time(ts: datetime | None = None) -> str:
    return (ts or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")


def log_system_info() -> None:
    system = {
        "session_started_at": pretty_time(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cwd": os.getcwd(),
    }
    logger.info(json.dumps({"type": "session_start", "payload": system}))
    print("System info:")
    for key, value in system.items():
        print(f"  {key}: {value}")


def summarize_metrics(summary: Dict[str, Any]) -> None:
    print("\nSession metrics summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    logger.info(json.dumps({"type": "session_summary", "metrics": summary}))


def run_session(queries: List[Dict[str, Any]], session_label: str) -> None:
    router = SmartRouter()

    for idx, query in enumerate(queries, start=1):
        prompt = query["messages"][-1]["content"].strip()
        result = router.process(
            query["messages"],
            mode=query.get("mode", "auto"),
            needs_citations=query.get("needs_citations", False),
            response_format=query.get("response_format", "text"),
            max_tokens=query.get("max_tokens", 512),
            temperature=query.get("temperature", 0.2),
        )

        tokens_prompt = result.metrics.get("prompt_tokens", estimate_tokens(prompt))
        tokens_response = result.metrics.get("response_tokens", estimate_tokens(result.answer))
        token_graph = render_token_graph(tokens_prompt, tokens_response)

        entry = {
            "type": "run",
            "session": session_label,
            "index": idx,
            "trace_id": result.trace_id,
            "prompt": prompt.splitlines()[0],
            "route": result.route,
            "model": result.model_used,
            "reason": result.routing_reason,
            "fallback": result.fallback_used,
            "metrics": result.metrics,
            "judge": result.judge,
        }
        logger.info(json.dumps(entry))

        rich_header(f"Run {idx}: {prompt.splitlines()[0][:60]}")
        print(f"Prompt snippet : {prompt.splitlines()[0]}")
        print(f"Route          : {result.route} ({result.model_used})")
        print(f"Reason         : {result.routing_reason}")
        print(f"Fallback used  : {result.fallback_used}")
        print(f"Latency        : {result.metrics['latency_ms']:.1f} ms")
        print(f"Cost units     : {result.metrics['cost_units']:.2f}")
        print(f"Judge          : correctness={result.judge['correctness']} fallback={result.judge['should_fallback']}")
        print(f"Trace ID       : {result.trace_id}")
        print("Token breakdown:")
        print(token_graph)
        print(f"Answer:\n{result.answer}\n")

    summary = router.metrics_logger.get_metrics_summary()
    rich_header("Session Metrics Summary")
    summarize_metrics(summary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Terminal wrapper for the Smart LLM Router with structured logs.")
    parser.add_argument("--queries-file", type=Path, default=Path("samples/demo_queries.json"), help="Query file path (JSON list or JSON lines).")
    parser.add_argument("--prompt", type=str, help="Run a single prompt interactively.")
    parser.add_argument("--session", type=str, default="default", help="Short label for the current session (used in logs).")

    args = parser.parse_args()

    if args.prompt:
        queries = [
            {
                "messages": [{"role": "user", "content": args.prompt}],
                "mode": "auto",
                "needs_citations": False,
                "response_format": "text",
                "max_tokens": 512,
                "temperature": 0.2,
            }
        ]
    else:
        queries = load_queries_from_file(args.queries_file)

    log_system_info()
    run_session(queries, args.session)


if __name__ == "__main__":
    main()
