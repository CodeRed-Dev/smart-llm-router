# From Router Experiments to GPU Whispers: My Local LLM Adventure 🚀

## The itch
- I was tired of guessing when to use a “fast but fuzzy” model vs. a “slow and smart” one. Why not build a local traffic cop that routes prompts automatically, judges the answers, and tells me exactly what it cost?

## The build (IRL)
- Crafted a **System1/System2 router**: heuristics pick the fast lane unless the prompt screams “analysis, JSON schema, citations, or long-winded rant,” then it jumps to System2.
- Dropped in a **judge model** that scores correctness/completeness and yells “fallback!” when things look shaky.
- Wired **metrics + telemetry** so every run spits out latency, token counts, cost units, cache hits, plus CPU/RAM and GPU (via `nvidia-smi`) — because vibes aren’t observability.
- Kept it **local-first**: Ollama by default, transformers if I want; no API bills, works on a plane.

## What happened in the lab
- **System1 test** (`llama2:7b`): 228 tokens, judge happy (no fallback), ~64s wall time — GPU spikes up to ~94% util and ~5.3 GiB VRAM, then chills back to idle.
- **System2 test** (`llama2:13b`): 70 tokens, no fallback, ~60s wall time — GPU hovers ~26% with bursts to ~93–94%, holds ~5.2 GiB VRAM and stays resident afterward; judge liked the structure but nagged me for missing source URLs.
- All the gritty details live in `docs/run_report.md` (metrics, commands, risks).

## Why it matters
- Faster demos: I get immediate answers when they’re “easy,” and safer answers when they’re “hard,” without hand-switching models.
- Auditability: Every run has a trace ID, judge notes, routing reason, and resource footprint. Great for sharing benchmarks or debugging why a reply went sideways.
- Portability: Works offline; swap models as hardware changes.

## If you want to try it
1) Clone, create `.env` from `.env.example`, set `FAST_MODEL_PATH`/`STRONG_MODEL_PATH`/`JUDGE_MODEL_PATH`, point `OLLAMA_BIN_PATH` if needed.
2) Run a quick spin:  
   `python run_router.py --prompt "Explain the routing architecture"`
3) Stress System2:  
   `python run_router.py --prompt "Provide a JSON schema and detailed step-by-step derivation for proving the Optimal Transport duality, compare Sinkhorn vs. linear programming solvers, and cite at least three references with source URLs." --needs-citations`
4) Watch the GPU gossip in another shell:  
   `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 1`

## Shout-outs to future me
- Install `psutil` when the network behaves to get CPU/RAM in every run.
- Trim latency: warm the models, lower `MAX_TOKENS`, or pick a smaller fast model.
- Log whole sessions with `scripts/log_router_session.py --session <name>` to grab structured JSON for posts.

Feel free to lift this for a LinkedIn post — just add screenshots of the token bars and judge verdicts. 🎛️🤖💡
