# Local Learning Guide

This guide walks through the System1/System2 dispatcher in `run_router.py` so you can run the full flow locally (router → LLM client → judge → fallback → metrics) and see a real-time visualization without spinning up a server.

## What you will explore

1. **Routing decisions**: `SmartRouter` inspects the latest user prompt, mode, and heuristics (citations, keywords, length) to choose between the low-cost System1 (`fast`) path and the higher-trust System2 (`strong`) route.
2. **LLM client**: A local Hugging Face-backed client loads whichever checkpoint path you configured (`FAST_MODEL_PATH`, `STRONG_MODEL_PATH`, `JUDGE_MODEL_PATH`) and runs inference in-process instead of hitting an API.
3. **Judge evaluator**: Scores correctness, completeness, hallucination risk, and format. You can tweak the thresholds in `app/evaluator.py` to understand how they influence fallback.
4. **Metrics logging**: Each request is recorded inside `MetricsLogger`, which keeps the same latency, fallback, and cost insights in memory so you can inspect them immediately after the run.
5. **Visualization**: `run_router.py` prints an ASCII trace for each request showing the component sequence, fallback decisions, and metrics summary in real time.

## Components in the CLI runner

- **SmartRouter**: Mirrors the original FastAPI router without HTTP. It coordinates cache checking, LLM client calls, judge evaluation, fallback, and logging into metrics storage.
- **LLM client**: Uses `app.llm_client.LLMClient` to hydrate the checkpoints you provide (e.g., `llama2-7b`, `llama2-13b`). Each route only loads its model once so you can experiment with quantized weights without touching the router logic.
- **Cache**: In-memory TTL cache from `app.cache.Cache` short-circuits repeated prompts.
- **MetricsLogger**: Tracks routing/latency/cost data in memory. `run_router.py` prints the aggregated summary at the end of each session.
- **Visualization helper**: The CLI prints a short trace like `[Router] System1 → [LLM] llama2:7b → [Judge] correctness=8 fallback=False → [Metrics] latency=185ms cost=0.36` so you can follow the execution path per prompt.

## Running the CLI

1. Install dependencies: `pip install -r requirements.txt`.
2. Ensure your checkpoint paths are ready (download `llama2-7b` / `llama2-13b` via Hugging Face or your preferred source) and set `FAST_MODEL_PATH`, `STRONG_MODEL_PATH`, and `JUDGE_MODEL_PATH`. Set `MODEL_DEVICE=cuda` when a GPU is available.
3. Run the dispatcher with the sample bundle:

   ```bash
   python run_router.py --queries-file samples/demo_queries.json
   ```

4. Optionally run a single prompt interactively:

   ```bash
   python run_router.py --prompt "Explain how routers route requests" --needs-citations
   ```

The CLI prints the ASCII visualization for each request plus the final metrics summary. Repeat runs highlight cache hits (the router logs “cache hit” and skips LLM calls).

## What to look for

- **System1 vs System2**: Confirm `run_router.py` prints `[Router] System1` when heuristics are satisfied and triggers `[Fallback] rerouted to strong model` when the judge lowers the score.
- **Judge output**: The printed judge object shows `correctness`, `completeness`, `hallucination_risk`, `format_ok`, and `should_fallback`. Compare these values to the entries stored inside `MetricsLogger`.
- **Cost vs accuracy**: When fallback occurs, observe the jump in `cost_units` and the extra latency. This reflects the real-world tradeoff between speed (System1) and reliability (System2).
- **Cache hits**: Rerun the same prompt and make sure the router logs a cache hit and the metrics show `cache_hit: True`, verifying `app.cache.Cache` works as expected.

## Authenticity checklist

- [ ] Confirm router logs include the deterministic reason for choosing fast or strong (keyword, length, or citation flag).
- [ ] Verify fallback is triggered when judge scores dip below the threshold, and a second strong model response is re-evaluated.
- [ ] Cross-check CLI-printed `metrics` data with `router.metrics_logger.get_metrics_summary()` to ensure the in-memory summary matches what you observed live.
- [ ] Use the README Mermaid diagram to trace each event printed in the CLI back to the component that performed it (router, judge, metrics logger).

## Next steps

Once you can predict each decision in this local runner, start swapping the dummy outputs in `scripts/local_demo.py` with the real `LLMClient`, or point `run_router.py` at real sample prompts. Keep the visualization/logging pattern so you can verify System1/System2 routing before lifting the ratio to production.
