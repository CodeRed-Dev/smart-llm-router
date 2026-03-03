# Smart LLM Router – Run Report (2026-03-03)

## Motive
- Provide a local, metrics-rich System1/System2 router for LLM prompts that can fall back to a stronger model when judged low quality.
- Keep runs auditable with cached metrics, judge verdicts, and resource telemetry (CPU/GPU/RAM).

## Problem & Need
- Users want fast answers when possible, but stronger reasoning or citation-heavy tasks demand higher-quality models.
- Manual model selection is error-prone; automated routing plus a judge reduces bad answers and reruns.
- Local-first (Ollama or transformers) avoids external API costs/latency and supports offline workflows.

## Implementation Snapshot
- Routing heuristics: manual mode override; otherwise citations, JSON/schema keywords, long prompts, or analysis verbs → System2; default → System1.
- Judge: JSON-structured rubric; triggers fallback if correctness below threshold or format fails.
- Metrics: latency (total/LLM/judge), token counts, cost heuristic, cache hit, routing reason.
- Telemetry hook: samples proc CPU %, proc RSS MB, system RAM %, and if available `nvidia-smi` GPU util/memory; failures are silent.
- Caching: in-memory TTL keyed on prompt + mode.
- Entrypoints: `run_router.py` (CLI), `scripts/log_router_session.py` (structured logs), `ui/dashboard.py` (Flask UI).

## Execution Flow
1) Intake messages → routing decision (System1 vs System2).
2) Call chosen model via `LLMClient` (Ollama or transformers backend).
3) Judge scores response; optional fallback to System2.
4) Metrics + telemetry merged; cached; emitted to logger/summary.
5) Session summary aggregates latency, cost, fallback rate, judge correctness, error rate.

## Environment & Config
- Key envs (see `.env.example`): `LLM_BACKEND`, `FAST_MODEL_PATH`, `STRONG_MODEL_PATH`, `JUDGE_MODEL_PATH`, `MODEL_DEVICE`, `OLLAMA_BIN_PATH`, `ROUTING_PROMPT_LENGTH_THRESHOLD`, `JUDGE_CORRECTNESS_THRESHOLD`, `MAX_TOKENS`, `CACHE_TTL_SECONDS`.
- Dependency for telemetry: `psutil` (best-effort metrics without it).

## Latest Run (2026-03-03) – System1
- Command: `python run_router.py --prompt "Explain the routing architecture"`
- Route/model: System1 → `llama2:7b`; no fallback.
- Tokens: prompt 4, response 224 (total 228).
- Latency: ~64.5 s; cost_units: 2.24 (heuristic).
- Judge: correctness 7; notes indicated comprehensive answer; no fallback requested.
- GPU trace (parallel `nvidia-smi`): util 0–94%, memory 8–5.3 GiB; sustained bursts around 26% util with spikes to >90%, confirming GPU engagement during generation, then idling to 0% post-run.
- Telemetry fields are attached in metrics if sampling succeeded; omitted on failure.

## Latest Run (2026-03-03) – System2
- Command: `python run_router.py --prompt "Provide a JSON schema and detailed step-by-step derivation for proving the Optimal Transport duality, compare Sinkhorn vs. linear programming solvers, and cite at least three references with source URLs."`
- Route/model: System2 → `llama2:13b` (heuristic: schema keyword); no fallback.
- Tokens: prompt 29, response 41 (total 70) — answer truncated/duplicated in stdout but judge still scored.
- Latency: ~60.3 s; cost_units: 1.23.
- Judge: correctness 7 (header) / notes report correctness 8, completeness 9; notes flagged missing source URLs; no fallback triggered.
- GPU: util baseline ~26% with spikes to ~93–94%; VRAM held ~5.2 GiB throughout and stayed resident after run (see System2 trace).

## Additional Observation – System2 GPU trace (user run)
- Second `nvidia-smi` stream (System2 test): util mostly ~26% with spikes to 93–94%; VRAM hovered ~5.2 GiB throughout, then idled at 0% util while memory stayed resident. Router stdout for this run was not captured; re-run with `scripts/log_router_session.py --session sys2-test --prompt "<prompt>" --needs-citations` to persist route/latency/judge alongside the GPU trace.

## Pending Test – System2 (planned)
- Prompt: “Provide a JSON schema and detailed step-by-step derivation for proving the Optimal Transport duality, compare Sinkhorn vs. linear programming solvers, and cite at least three references with source URLs.” (`--needs-citations` recommended)
- Expect route: System2 (`llama2:13b`), higher latency/cost; observe judge verdict and telemetry.

## Observed Risks / Next Actions
- High latency on System1 run; investigate Ollama server warm-up, model size, or reduce `MAX_TOKENS`.
- Ensure `psutil` is installed to capture CPU/RAM consistently.
- If GPU memory is constrained, consider a smaller fast model for System1 to cut latency and VRAM.
- Log structured runs with `scripts/log_router_session.py --session <label>` to persist metrics.

## Quick Commands
- Fast sanity run: `python run_router.py --prompt "Explain the routing architecture"`
- System2-forcing run: `python run_router.py --prompt "<complex prompt above>" --needs-citations`
- GPU watch (separate shell): `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 1`
