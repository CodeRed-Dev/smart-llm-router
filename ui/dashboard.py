"""Flask dashboard that surfaces SmartRouter routing, judge, and metrics output."""

from pathlib import Path
import sys

from datetime import datetime
from flask import Flask, request, render_template_string

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.router import SmartRouter

app = Flask(__name__)
router = SmartRouter()
history: list[dict] = []

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Smart Router Dashboard</title>
  <style>
    body { margin: 0; font-family: "Segoe UI", system-ui, sans-serif; background: #f4f6fb; color: #0f172a; min-height: 100vh; }
    header { padding: 1.5rem; background: linear-gradient(135deg,#0f172a,#1e293b); color: #fff; }
    header h1 { margin: 0; font-size: 2rem; }
    main { padding: 2rem 3vw 2rem 3vw; width: 100%; max-width: 1600px; margin: 0 auto; }
    form { background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 10px 25px rgba(15,23,42,.12); margin-bottom: 2rem; display: flex; flex-direction: column; gap: 1rem; }
    textarea { height: 200px; }
    section { width: 100%; }
    .card { min-height: 120px; }
    @media (max-width: 1020px) {
      main { padding: 1rem; }
      .log-row { grid-template-columns: 80px 1fr 1fr; grid-auto-rows: auto; }
      .log-row div:nth-child(4) { display: none; }
      .flow-chart { grid-template-columns: 1fr; }
    }
    textarea { width: 100%; border: 1px solid #cbd5f5; border-radius: 8px; padding: .75rem; font-size: 1rem; resize: vertical; min-height: 140px; }
    label { font-size: .9rem; display: block; margin-top: .5rem; }
    button { margin-top: 1rem; padding: .75rem 1.5rem; border: none; border-radius: 8px; background: #2563eb; color: #fff; font-size: 1rem; cursor: pointer; }
    .card { background: #fff; border-radius: 12px; padding: 1.25rem; box-shadow: 0 8px 25px rgba(15,23,42,.1); margin-bottom: 1.25rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(240px,1fr)); gap: 1rem; }
    .pill { display: inline-flex; align-items: center; padding: .25rem .75rem; border-radius: 999px; font-size: .85rem; background: #c7d2fe; color: #312e81; margin-right: .5rem; }
    .metrics { font-size: .9rem; color: #475569; }
    .metric-card { background: #f8fafc; padding: 1rem; border-radius: 10px; border: 1px solid #e0e7ff; min-height: 120px; }
    .metric-card strong { display: block; font-size: .85rem; color: #64748b; }
    .metric-value { font-size: 1.4rem; font-weight: 600; color: #0f172a; }
    .log-table { display: flex; flex-direction: column; gap: .75rem; }
    .log-row { display: grid; grid-template-columns: 110px 1fr 120px 100px; gap: .75rem; padding: .75rem 1rem; border-radius: 10px; background: #f8fafc; border: 1px solid #e2e8f0; }
    .log-row.head { background: #e0e7ff; font-size: .8rem; letter-spacing: .05em; text-transform: uppercase; color: #1e293b; }
    .flow-chart { display: grid; grid-template-columns: repeat(auto-fit,minmax(200px,1fr)); gap: 1rem; margin-top: 1rem; }
    .flow-step { border-radius: 12px; padding: 1rem; background: #0f172a; color: #fff; box-shadow: 0 8px 20px rgba(15,23,42,.2); min-height: 120px; }
    .flow-step.secondary { background: #1e293b; }
    .flow-step span { display: block; font-size: .85rem; color: #cbd5f5; margin-bottom: .25rem; }
    pre { background: #0f172a; color: #f8fafc; padding: .75rem; border-radius: 8px; overflow-x: auto; }
    footer { text-align: center; margin-top: 2rem; color: #475569; font-size: .85rem; }
  </style>
</head>
<body>
  <header>
    <h1>Smart Router Dashboard</h1>
    <p>Use System1/System2 heuristics + judge metrics to trace each LLM call in a terminal-native UI.</p>
  </header>
  <main>
    <form method="post">
      <textarea name="prompt" required placeholder="Describe what you want the router to do">{{ prompt }}</textarea>
      <label><input type="checkbox" name="needs_citations" {% if needs_citations %}checked{% endif %}> Needs citations (forces System2)</label>
      <button type="submit">Run Prompt</button>
    </form>

    {% if info %}
      <section class="card">
        <div class="grid">
          <div>
            <div class="pill">Route: {{ info.route }}</div>
            <div class="pill">Model: {{ info.model }}</div>
            <div class="pill">Score: {{ info.judge.correctness }}/10</div>
            <div class="pill">Fallback: {{ info.fallback_used }}</div>
          </div>
          <div>
            <p><strong>Routing reason:</strong> {{ info.routing_reason }}</p>
            <p><strong>Judge analysis:</strong> {{ info.judge.notes }}</p>
            <p class="metrics">Latency: {{ info.metrics.latency_ms|round(1) }} ms &middot; Cost: {{ info.metrics.cost_units|round(2) }} &middot; Tokens (prompt/response): {{ info.metrics.prompt_tokens }}/{{ info.metrics.response_tokens }}</p>
            <p class="metrics">Trace ID: {{ info.trace_id }}</p>
          </div>
        </div>
        <div style="margin-top: 1rem;">
          <strong>Answer:</strong>
          <pre>{{ info.answer }}</pre>
        </div>
      </section>
    {% endif %}

    <section class="card">
      <h2>Session metrics summary</h2>
      <div class="grid">
        {% for key, value in summary.items() %}
          <div class="metric-card">
            <strong>{{ key.replace('_',' ') | capitalize }}</strong>
            <p class="metric-value">{{ value }}</p>
          </div>
        {% endfor %}
      </div>
    </section>

    <section class="card">
      <h2>Recent router logs</h2>
      {% if history %}
        <div class="log-table">
          <div class="log-row head">
            <div>Time</div>
            <div>Prompt + Trace</div>
            <div>Route · Model</div>
            <div>Latency</div>
          </div>
          {% for entry in history[:5] %}
            <div class="log-row">
              <div>{{ entry.timestamp }}</div>
              <div>
                <strong>{{ entry.prompt[:60] }}{% if entry.prompt|length > 60 %}…{% endif %}</strong>
                <div class="metrics">Trace {{ entry.trace_id }}</div>
              </div>
              <div class="metrics">
                <div>Route: {{ entry.route }}</div>
                <div>Model: {{ entry.model }}</div>
                <div>Judge: {{ entry.judge.correctness }}/10</div>
              </div>
              <div class="metrics">
                <div>Latency: {{ entry.metrics.latency_ms|round(1) }} ms</div>
                <div>Tokens: {{ entry.metrics.prompt_tokens }}/{{ entry.metrics.response_tokens }}</div>
              </div>
            </div>
          {% endfor %}
        </div>
      {% else %}
        <p>No routed prompts yet. Submit one above.</p>
      {% endif %}
    </section>

    <section class="card">
      <h2>Project flow visualization</h2>
      <p class="metrics">Latest route: {{ info.route if info else "waiting for input" }} · Judge fallback: {{ info.fallback_used if info else "—" }}</p>
      <div class="flow-chart">
        <div class="flow-step">
          <span>Step 1 · Intake</span>
          Prompt ingestion & routing heuristic (System1/System2 controller)
        </div>
        <div class="flow-step secondary">
          <span>Step 2 · Model</span>
          {{ info.model if info else "Fetches fast or strong LLM via LLMClient" }}
        </div>
        <div class="flow-step">
          <span>Step 3 · Judge</span>
          Evaluates correctness, triggers fallback when needed
        </div>
        <div class="flow-step secondary">
          <span>Step 4 · Metrics</span>
          logger records latency, cost, prompts, trace, plus caching
        </div>
      </div>
    </section>

    <section>
      <h2>History</h2>
      {% if history %}
        {% for entry in history %}
          <article class="card">
            <div class="metrics" style="display:flex;gap:1rem;flex-wrap:wrap;">
              <div><strong>{{ entry.timestamp }}</strong></div>
              <div class="pill">Route: {{ entry.route }}</div>
              <div class="pill">Model: {{ entry.model }}</div>
              <div class="pill">Reason: {{ entry.reason }}</div>
            </div>
            <div class="metrics" style="margin-top:.5rem;">
              Judge: correctness={{ entry.judge.correctness }} &middot; fallback={{ entry.judge.should_fallback }} &middot; latency={{ entry.metrics.latency_ms|round(1) }}ms
            </div>
            <p style="margin: .5rem 0;"><strong>Prompt:</strong> {{ entry.prompt }}</p>
            <pre>{{ entry.answer }}</pre>
          </article>
        {% endfor %}
      {% else %}
        <p>No prompts yet. Submit one above.</p>
      {% endif %}
    </section>
  </main>
  <footer>Logs remain in memory per session; refresh resets the history.</footer>
</body>
</html>
"""


@app.template_filter("capitalize")
def capitalize_filter(value: str) -> str:
    if not value:
        return value
    return value[0].upper() + value[1:]


@app.route("/", methods=("GET", "POST"))
def index():
    prompt = ""
    needs_citations = False
    info = None

    if request.method == "POST":
        prompt = request.form["prompt"].strip()
        needs_citations = "needs_citations" in request.form
        messages = [{"role": "user", "content": prompt}]
        result = router.process(messages, needs_citations=needs_citations)
        info = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "prompt": prompt,
            "route": result.route,
            "model": result.model_used,
            "reason": result.routing_reason,
            "metrics": result.metrics,
            "judge": result.judge,
            "answer": result.answer,
            "trace_id": result.trace_id,
            "fallback_used": result.fallback_used,
        }
        history.insert(0, info)
        history[:] = history[:20]

    summary = router.metrics_logger.get_metrics_summary()
    return render_template_string(
        TEMPLATE,
        prompt=prompt,
        needs_citations=needs_citations,
        info=info,
        summary=summary,
        history=history,
    )


if __name__ == "__main__":
    app.run(port=8501, debug=False)
