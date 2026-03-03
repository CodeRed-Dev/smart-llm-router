# Smart LLM Router (Local CLI)

**System1/System2 routing with structured logging, judge-based quality checks, and a terminal-first experience.**

This repo keeps the entire routing stack local: prompts flow through the fast (System1) model, the router applies heuristics, the strong (System2) model kicks in when the judge requests higher quality, and every run emits metrics so you can track latency, cost, fallback decisions, and judge scores.

## Getting started

### 1. Create the virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Install Ollama and pull the models

1. Install Ollama by following the instructions at https://ollama.com/docs. After installation, make sure the `ollama` binary is on your `PATH` or set `OLLAMA_BIN_PATH` to the executable path (e.g., `C:\Users\ragha\AppData\Local\Programs\Ollama\ollama.exe`).
2. Pull the models you want to use:
   ```powershell
   ollama pull llama2:7b
   ollama pull llama2:13b
   ```
3. (Optional) For the judge consider pointing to the strong model, unless you have a smaller dedicated judge model.

### 3. Configure the router

Set the environment variables so the router points to your Ollama models:

```powershell
$env:LLM_BACKEND = "ollama"
$env:FAST_MODEL_PATH = "llama2:7b"
$env:STRONG_MODEL_PATH = "llama2:13b"
$env:JUDGE_MODEL_PATH = "llama2:13b"
$env:OLLAMA_BIN_PATH = "C:\Users\<you>\AppData\Local\Programs\Ollama\ollama.exe"
```

If you prefer the `transformers` backend instead of Ollama, install PyTorch and Transformers (`pip install torch transformers`), set `LLM_BACKEND=transformers`, and point the `*_MODEL_PATH` values to local checkpoints (or HF repo IDs).

*Tip: copy `.env.example` to `.env` and populate the same variables so `python-dotenv` loads them automatically each session (the repo already loads `.env` before applying defaults).*

## Running the router

### Standard runner (existing behavior)

Use the built-in runner to load `samples/demo_queries.json` or pass your own prompt:

```powershell
python run_router.py --queries-file samples/demo_queries.json
python run_router.py --prompt "Explain how routers work"
```

Each prompt prints the routing decision, model, judge verdict, fallback status, latency/cost metrics, token counts, and answer. The in-memory metrics logger keeps a running summary that is printed at the end of the session.

### Structured logging wrapper (new)

`python scripts/log_router_session.py` now wraps the router with richer terminal output and JSON logging. It:

- Logs system metadata (platform, Python version, working directory).
- Prints per-run headers, token breakdown graphs, judge verdicts, and answers.
- Dumps structured JSON entries to `logs/router_sessions.log` for later sharing.
- Prints the session metrics summary (total requests, avg latency/cost, fallback rate, judge correctness, error rate).

Run it like this:

```powershell
python scripts/log_router_session.py --session daily-demo --queries-file samples/demo_queries.json
python scripts/log_router_session.py --session quick-test --prompt "Summarize the architecture"
```

The logs are stored in `logs/router_sessions.log` (created automatically). Share snippets from this log or the terminal output when documenting your results.

## Logging & metrics

- Every router result is logged with `route`, `model`, `reason`, `metrics`, `judge`, and `trace_id` (useful for retrospective analysis).
- Metrics include `latency_ms`, `cost_units`, `prompt_tokens`, `response_tokens`, and fallback flags.
- The summary at the end of a run shows `total_requests`, `avg_latency_ms`, `avg_cost_units`, `fallback_rate`, `avg_judge_correctness`, and `error_rate`.

## Samples & diagnostics

- `samples/demo_queries.json` contains a set of prompts that exercise System1/System2 routing, citations, and fallback logic.
- `scripts/local_demo.py` offers a lighter way to inspect the heuristics without launching a real LLM (useful for dry runs).
- `docs/project_report.md` explains the terminal-first direction, logging additions, and how to share the project story publicly.

## Interactive dashboard

- The Flask-based dashboard (run via `python ui/dashboard.py`) lets you fire prompts from a browser while showing route/model decisions, judge analysis, tokens, and full answers in one place.
- It pulls from the same `SmartRouter` instance as the CLI and keeps a short history so you can compare responses and judge notes without repeating commands.
- Use the same `.env`/Ollama settings before launching the UI.

## Next steps

1. Run the logging wrapper and capture `logs/router_sessions.log` for sharing on LinkedIn or in documentation.
2. Keep your Ollama models updated (`ollama pull <model> --force` when new versions land).
3. If needed, add tests under `tests/` covering routing decisions, cache hits, and metrics aggregation.
4. When you make changes, stage them and `git push` to share your updated router logic.
