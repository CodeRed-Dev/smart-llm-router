# MARK-1

The current terminal-first workflow (MARK-1) preserves the CLI-focused Smart Router: `run_router.py` for prompt runs, `scripts/log_router_session.py` for richer terminal/log output, the `.env` defaults for Ollama models, the `app/` package with SmartRouter + metrics/logger/cache, and the project documentation in `README.md`/`docs/*.md`.

MARK-1 notes:
1. The runner uses the Ollama CLI models defined in `.env` (`llama2:7b`, `llama2:13b`).
2. `scripts/log_router_session.py` logs JSON sessions to `logs/router_sessions.log` and prints token breakdowns, judge verdicts, and per-run headers.
3. No Flask UI is present; the repo keeps everything local so the terminal output handles routing, judge, fallback, cost, and latency summaries.
4. Keep `python-dotenv` so `.env` loads automatically at startup via `config/__init__.py`.

If you ever branch toward a new interface, you can compare future states against MARK-1 as the baseline.
