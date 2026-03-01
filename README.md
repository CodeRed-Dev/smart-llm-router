# Smart LLM Router

*Cheapest model that meets quality, with automated evaluation + fallback.*

A FastAPI-based service that intelligently routes Large Language Model (LLM) requests between fast (cheap) and strong (expensive) models, evaluates response quality, and provides automatic fallback mechanisms.

## Features

- **Intelligent Routing**: Automatically chooses between fast and strong models based on query complexity
- **Quality Evaluation**: Uses a judge model to assess response quality and trigger fallbacks
- **Caching**: In-memory TTL caching for repeated queries
- **Metrics & Monitoring**: Comprehensive logging and Prometheus-compatible metrics
- **Offline Evaluation**: Test harness for measuring performance against datasets
- **Local-First**: Uses Ollama for cost-free local LLM inference

## Architecture

```
User Request → FastAPI → Router → LLM Client → Response
                    ↓         ↓
               Evaluator ← Judge Model
                    ↓
               Metrics Logger → SQLite
```

### Components

1. **API Gateway (FastAPI)**: Main entry point with REST endpoints
2. **Router**: Core logic for model selection and fallback handling
3. **LLM Client**: Handles communication with Ollama models (fast, strong, judge)
4. **Evaluator**: Quality assessment using judge model
5. **Cache**: In-memory caching with TTL
6. **Storage**: SQLite database for metrics persistence
7. **Metrics**: Aggregation and Prometheus endpoint
8. **Eval Harness**: Offline testing and benchmarking

## Quick Start

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) installed and running
- Models: `llama2:7b` (fast), `llama2:13b` (strong)

### Installation

```bash
git clone <repository-url>
cd smart-llm-router
pip install -r requirements.txt
```

### Configuration

Edit `config/__init__.py` or set environment variables:

```bash
export FAST_MODEL_NAME="llama2:7b"
export STRONG_MODEL_NAME="llama2:13b"
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Running

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

## API Usage

### POST /v1/chat

```bash
curl -X POST "http://localhost:8000/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "mode": "auto"
  }'
```

Response:
```json
{
  "answer": "Quantum computing uses quantum mechanics...",
  "route": "fast",
  "model_used": "llama2:7b",
  "fallback_used": false,
  "judge": {
    "correctness": 8,
    "completeness": 7,
    "format_ok": true,
    "hallucination_risk": 2,
    "should_fallback": false,
    "notes": "Good technical explanation"
  },
  "metrics": {
    "latency_ms": 1250.5,
    "llm_latency_ms": 980.2,
    "judge_latency_ms": 180.3,
    "cache_hit": false,
    "cost_units": 1.2
  },
  "trace_id": "abc-123-def"
}
```

### GET /metrics

Returns Prometheus-formatted metrics for monitoring.

### GET /health

Simple health check endpoint.

## Evaluation

Run the evaluation harness:

```bash
python eval/harness.py --num-samples 20
```

This will test the router against sample prompts and generate a performance report.

## Development

### Project Structure

```
├── app/                    # Main application code
│   ├── main.py            # FastAPI app entry point
│   ├── router.py          # Routing logic
│   ├── llm_client.py      # Ollama client
│   ├── evaluator.py       # Quality evaluation
│   ├── cache.py           # Caching layer
│   ├── storage.py         # SQLite storage
│   └── metrics.py         # Metrics collection
├── config/                # Configuration
├── eval/                  # Evaluation system
│   ├── harness.py         # Test runner
│   └── eval_set.jsonl     # Test dataset
├── tests/                 # Unit tests
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Testing

```bash
pytest tests/
```

### Contributing

1. Follow the coding guidelines in `CODING_GUIDELINES.md`
2. Create feature branches from `develop`
3. Write tests for new functionality
4. Ensure evaluation harness passes
5. Submit PR with comprehensive description

## License

MIT License