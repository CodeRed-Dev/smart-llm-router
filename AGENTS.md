# Repository Guidelines

## Project Structure & Module Organization
- `run_router.py`: CLI entry point that wires `SmartRouter`, prompts, judge/evaluator, and the visualization/metrics output.
- `app/`: core modules (`router.py`, `llm_client.py`, `evaluator.py`, `metrics.py`, `cache.py`) that implement routing heuristics, evaluation, caching, and the pluggable backends (Ollama CLI by default, transformers when requested).
- `samples/` and `scripts/`: sample queries (`demo_queries.json`) and the lightweight `local_demo.py` that mirrors routing without real LLMs for quick sanity checks.
- `config/` holds simple environment-backed settings, while `docs/` documents learning guides and local workflow tips. Assets (models, Q&A) live outside the repository, so update env vars instead of vendoring binary files.

## Build, Test, and Development Commands
- `.\.venv\Scripts\pip.exe install -r requirements.txt`: install the minimal toolset (no HF/torch until you enable that backend).
- `.\.venv\Scripts\python.exe scripts/local_demo.py`: run the stubbed dispatcher to exercise routing, caching, fallback, and metrics locally.
- `.\.venv\Scripts\python.exe run_router.py --queries-file samples/demo_queries.json`: run the full CLI against sample prompts – set `LLM_BACKEND=ollama` and the Ollama model env vars before execution.
- `.\.venv\Scripts\python.exe run_router.py --prompt "..." --needs-citations`: sanity-check a single prompt via the dispatcher.

## Coding Style & Naming Conventions
- Python files follow 4-space indentation, snake_case for functions/variables, and PascalCase for dataclasses; adhere to the existing formatting (e.g., dataclasses in `router.py`, request/metrics dictionaries).
- Prefer descriptive names (`metrics_logger`, `judge_result`) and keep helper functions small. No additional formatter is enforced, but keep imports grouped (stdlib → third-party → local) and alphabetized per PEP8.
- For new modules, mirror the pattern in `app/`: split concerns (cache, metrics, llm_client) into their own files and expose public APIs via `__all__` only when necessary.

## Testing Guidelines
- Only `pytest` is installed; add tests under a new `tests/` directory if needed and name them `test_*.py`.
- No automated coverage enforcement currently exists, but new tests should assert routing decisions, cache hits, and metric aggregation so the visualization output remains reliable.
- Run `pytest` from the repo root (inside the virtualenv) after adding tests; keep fixtures lightweight.

## Commit & Pull Request Guidelines
- Follow conventional commits informally: use imperative verbs (`add`, `fix`, `update`) and mention the area touched (`router`, `llm`, `docs`).
- PRs should describe what workflow they exercise, list any env vars needed (`LLM_BACKEND`, `FAST_MODEL_PATH`, `STRONG_MODEL_PATH`, etc.), and summarize the observed CLI output or metrics when relevant.
- Include sample output/log excerpts (or screenshots for complex visual changes) if the change affects the router visualization or metrics logging.
