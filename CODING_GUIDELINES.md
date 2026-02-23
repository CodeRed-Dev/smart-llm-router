# Smart LLM Router - Coding Guidelines and Development Practices

## Overview
This document outlines the coding practices, implementation instructions, and Git workflow guidelines for the **Smart LLM Router** project. These guidelines ensure high-quality, maintainable code for an intelligent LLM routing system that optimizes cost, latency, and quality through automated evaluation and fallback mechanisms.

## Project Context
The Smart LLM Router is a FastAPI-based service that intelligently routes LLM requests between fast (cheap) and strong (expensive) models, evaluates responses for quality, and provides fallback mechanisms. It includes caching, metrics logging, and an offline evaluation harness.

## Industry-Level Coding Practices

### 1. Code Quality
- **Clean Code**: Follow PEP 8 and "Clean Code" principles. Write readable, maintainable Python code.
- **DRY Principle**: Eliminate code duplication through functions, classes, and modules.
- **SOLID Principles**: Design classes and modules with single responsibility, open for extension but closed for modification.
- **KISS Principle**: Prefer simple solutions; avoid over-engineering.

### 2. Python-Specific Conventions
- **Naming**:
  - Variables/Functions: `snake_case` (e.g., `route_request`, `calculate_cost`)
  - Classes: `PascalCase` (e.g., `LLMRouter`, `JudgeEvaluator`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_TOKENS`, `FAST_MODEL_NAME`)
  - Files/Modules: `snake_case` (e.g., `llm_router.py`, `metrics_logger.py`)
- **Imports**: Group imports (standard library, third-party, local) with blank lines.
- **Type Hints**: Use type annotations for function parameters and return values.
- **Docstrings**: Use Google-style docstrings for all public functions and classes.

### 3. Code Structure
- **Modularization**: Break down into focused modules: `router`, `llm_client`, `evaluator`, `cache`, `metrics`, `storage`.
- **Async/Await**: Use asynchronous programming for LLM calls, timeouts, and I/O operations.
- **Error Handling**: Implement comprehensive error handling with custom exceptions (e.g., `LLMTimeoutError`, `JudgeEvaluationError`).
- **Logging**: Use Python's `logging` module with appropriate levels; log metrics, errors, and routing decisions.
- **Configuration**: Use environment variables or config files for model endpoints, timeouts, thresholds.

### 4. Documentation
- **Docstrings**: Document all public APIs, classes, and functions with purpose, parameters, returns, and examples.
- **README**: Maintain comprehensive README with setup, usage, API docs, and architecture.
- **API Documentation**: Use FastAPI's automatic OpenAPI docs; add examples and error responses.
- **Code Comments**: Comment complex routing logic, judge criteria, and fallback conditions.
- **Inline Eval Harness**: Document evaluation datasets and scoring methodologies.

### 5. Security (LLM-Specific)
- **Input Validation**: Sanitize all user prompts to prevent injection attacks.
- **Prompt Engineering Security**: Avoid exposing system prompts; validate response formats.
- **Data Protection**: Never log sensitive user data; anonymize metrics.
- **Rate Limiting**: Implement rate limiting to prevent abuse of LLM endpoints.
- **Dependency Security**: Regularly audit and update Python packages; use `safety` or `pip-audit`.

### 6. Performance (LLM Optimization)
- **Efficient Routing**: Minimize unnecessary LLM calls through smart heuristics and caching.
- **Resource Management**: Properly manage async tasks, connections to Ollama, and memory usage.
- **Caching**: Implement TTL caching for repeated queries to reduce latency and cost.
- **Profiling**: Use `cProfile` or `line_profiler` to identify bottlenecks in routing and evaluation.
- **Concurrency**: Handle multiple concurrent requests efficiently with async patterns.

### 7. LLM-Specific Best Practices
- **Prompt Design**: Store prompts as constants or config; version control prompt changes.
- **Model Management**: Abstract model clients for easy switching between Ollama and API models.
- **Evaluation Reliability**: Ensure judge prompts are robust and consistent.
- **Metrics Granularity**: Log detailed metrics for routing decisions, fallbacks, and quality scores.
- **Testing with LLMs**: Use mock responses for unit tests; integration tests with actual models sparingly.

## Implementation Instructions

Before implementing any feature, follow these steps:

### 1. Requirements Analysis
- Review the product spec and identify the specific use case/feature.
- Break down into subtasks aligned with project phases (MVP, Evaluation, Intelligent Routing).
- Identify dependencies (e.g., new Ollama models, database schema changes).

### 2. Design and Planning
- Sketch the component architecture and data flow.
- Plan async patterns for LLM calls and timeouts.
- Estimate token usage, latency impact, and cost implications.

### 3. Code Review Preparation
- Ensure code follows PEP 8 and project conventions.
- Write unit tests with mocked LLM responses.
- Add integration tests for end-to-end routing flows.

### 4. Testing
- **Unit Tests**: Test individual functions (routing logic, judge evaluation) with `pytest`.
- **Integration Tests**: Test full request flows with real Ollama models.
- **Performance Tests**: Benchmark latency, throughput, and cost for different routing scenarios.
- **Eval Harness**: Run offline evaluations to measure quality improvements.

### 5. Documentation
- Update API docs, README, and architecture diagrams.
- Document new configuration options, environment variables.
- Add examples for new features in the README.

### 6. Peer Review
- Submit PR with clear description of changes and testing results.
- Address review feedback, especially around routing logic and error handling.

## Git Workflow and Branching Strategy

### Branching Strategy
- **Main Branch**: `main` - Production-ready code, deployed versions.
- **Development Branch**: `develop` - Integration branch for ongoing development.
- **Feature Branches**: `feature/<feature-name>` - For new features (e.g., `feature/adaptive-routing`).
- **Phase Branches**: `phase/<phase-name>` - For major phases (e.g., `phase/mvp-core`, `phase/evaluation-discipline`).
- **Bugfix Branches**: `bugfix/<description>` - For bug fixes (e.g., `bugfix/judge-timeout`).
- **Experiment Branches**: `experiment/<experiment>` - For testing new routing strategies or models.

### Commit Guidelines
- **Atomic Commits**: Each commit represents one logical change (e.g., "Add routing heuristics", "Implement judge evaluation").
- **Descriptive Messages**: Use conventional commits:
  ```
  type(scope): description

  [optional body with details]

  [optional footer with issue references]
  ```
  Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
  Scopes: `router`, `llm`, `judge`, `metrics`, `api`, `eval`
- **Frequent Commits**: Commit after completing small, testable units.

### Pull Request Process
1. Create feature branch from `develop` or relevant phase branch.
2. Implement with proper commits and tests.
3. Push branch and create PR with description, screenshots of metrics, and eval results.
4. Ensure CI passes (linting, tests, type checking).
5. Request review from team.
6. Merge after approval (squash for clean history).

### Git Best Practices
- **Never commit to main directly**: All changes via PRs.
- **Branch Naming**: Use descriptive, hyphen-separated names.
- **Rebase for Updates**: Rebase feature branches on latest develop before PR.
- **Clean Merges**: Use squash merges for feature branches to keep main history clean.
- **Tag Releases**: Tag versions on main (e.g., `v1.0.0-mvp`).
- **Protect Branches**: Use branch protection rules for main/develop.

## Agent Usage Guidelines

When using AI agents for coding assistance:

1. **Provide Context**: Include the product spec, relevant code files, and current architecture.
2. **Specify Constraints**: Reference these guidelines, especially Python conventions and LLM best practices.
3. **Review LLM Code**: Carefully review generated code for prompt injection risks, async patterns, and error handling.
4. **Test Generated Code**: Always run tests and eval harness after AI-generated changes.
5. **Document AI Contributions**: Note AI usage in commit messages and PR descriptions.
6. **Iterate with Feedback**: Use AI for rapid prototyping, but validate with human review.

## Tools and Technologies

- **Language**: Python 3.9+
- **Framework**: FastAPI for API, Uvicorn for server
- **LLM Integration**: Ollama for local models, httpx for async HTTP calls
- **Database**: SQLite with SQLAlchemy for metrics storage
- **Caching**: Redis or in-memory cache (cachetools)
- **Code Quality**: Black (formatter), isort (import sorter), mypy (type checker), pylint (linter)
- **Testing**: pytest, pytest-asyncio, responses (for mocking HTTP)
- **CI/CD**: GitHub Actions for linting, testing, and deployment
- **Documentation**: MkDocs or FastAPI docs, Mermaid for diagrams
- **Metrics**: Prometheus client for metrics collection
- **Evaluation**: Custom harness with JSON Lines datasets

## Project-Specific Guidelines

### Routing Logic
- Implement routing heuristics based on prompt analysis (length, keywords, constraints).
- Ensure fallback logic is transparent and logged.
- Test routing decisions with diverse prompt examples.

### Judge Evaluation
- Design judge prompts for consistent, numerical scoring.
- Handle judge failures gracefully (e.g., assume high quality if judge times out).
- Validate judge outputs for required JSON structure.

### Metrics and Logging
- Log all routing decisions, latencies, and costs.
- Implement `/metrics` endpoint with aggregated statistics.
- Use structured logging (JSON format) for easy analysis.

### Evaluation Harness
- Maintain `eval_set.jsonl` with diverse prompts and expected quality criteria.
- Run harness regularly to track improvements.
- Include baseline comparisons in reports.

### Configuration Management
- Use Pydantic models for configuration validation.
- Separate development and production configs.
- Document all configuration options.

## Continuous Improvement

- **Code Reviews**: Focus on routing logic accuracy, async patterns, and LLM integration.
- **Retrospectives**: Review phase outcomes, routing performance, and quality metrics.
- **Metrics-Driven Development**: Use logged metrics to guide optimizations.
- **Stay Updated**: Monitor LLM advancements, security best practices, and Python ecosystem.

---

*This document evolves with the project. Update it as new patterns emerge or requirements change.*