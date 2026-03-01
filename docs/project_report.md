# Smart Router Command Line Experience

This concise report is tailored for sharing on LinkedIn, summarizing the local Smart Router project, why the terminal-first workflow is now the focus, and the logging/reporting conveniences that were added.

## Why this project matters
- **System1/System2 design**: Automatically routes prompts between a fast model (System1) and a more accurate strong model (System2) using heuristics (prompt length, keywords, citations). The judge evaluates every response and can trigger fallbacks when correctness is flagged low.
- **Metric-aware**: A metrics logger captures latency, costs, fallback decisions, cache hits, and judge scores so every run feeds a measurable session history.
- **Local-first**: The code relies on locally installed models (Ollama CLI by default, with an optional transformers backend), enabling offline experimentation without third-party APIs.

## What changed
1. **Dropped the UI dashboard** – the looped Flask server was redundant because the CLI already exposes the router behavior more transparently. Removing it simplified the repo and avoided needing the Ollama binary just for the dashboard.
2. **Introduced `scripts/log_router_session.py`** – this wrapper:
   - Logs system metadata, request details, and metrics as structured JSON into `logs/router_sessions.log`.
   - Prints a fixed-width terminal summary per run, including routing reason, fallback status, judge verdict, token breakdown, and full answers.
   - Signs off with a session metrics summary so each demo run yields a consistent record for sharing.
3. **Retained core router logic** – `run_router.py` and every `app/*` component remain untouched so the routing heuristics, caching, judges, and evaluators continue to behave the same.

## How to reproduce
1. Activate the virtualenv from the repo root (`.venv\Scripts\Activate.ps1`).
2. Run the wrapper directly:
   ```powershell
   python scripts/log_router_session.py --queries-file samples/demo_queries.json --session daily-demo
   ```
3. For a single prompt:
   ```powershell
   python scripts/log_router_session.py --prompt "Summarize the architecture" --session demo
   ```
4. Check `logs/router_sessions.log` for structured JSON entries covering every run and the session summary.

## Metrics & Reporting
- Each log entry records `route`, `model`, `reason`, `fallback`, `metrics` (latency, cost, token counts), and `judge` verdicts.
- The final summary prints `total_requests`, `avg_latency_ms`, `avg_cost_units`, `fallback_rate`, `avg_judge_correctness`, and `error_rate` (if errors occur).
- CLI output includes token breakdown charts, trace IDs, and answer text for rapid review.

## Next steps for a LinkedIn post
- Highlight the move from Flask dashboard to a terminal-first, log-native workflow to emphasize portability.
- Mention metrics-first observability, the judge/fallback story, and that the system is ready for Ollama or transformers backends.
- Share the `logs/router_sessions.log` artifact or a snippet of the session summary to demonstrate the deterministic output.
- Link to this repo and describe how others can clone, configure the models, and run the wrapper script.
