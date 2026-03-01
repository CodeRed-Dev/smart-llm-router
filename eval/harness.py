"""
Evaluation Harness

Offline evaluation system for testing the LLM router's performance
against a dataset of prompts with quality expectations.
"""

import json
import asyncio
import time
from typing import List, Dict, Any
from pathlib import Path
from app.router import ChatRequest, ChatMessage
from app.main import app
from fastapi.testclient import TestClient

class EvaluationHarness:
    def __init__(self, eval_set_path: str = "eval/eval_set.jsonl"):
        self.eval_set_path = Path(eval_set_path)
        self.client = TestClient(app)

    def load_eval_set(self) -> List[Dict[str, Any]]:
        """Load evaluation prompts from JSONL file."""
        eval_set = []
        with open(self.eval_set_path, 'r') as f:
            for line in f:
                eval_set.append(json.loads(line.strip()))
        return eval_set

    async def run_evaluation(self, num_samples: int = None) -> Dict[str, Any]:
        """
        Run evaluation on the dataset and return comprehensive results.
        """
        eval_set = self.load_eval_set()
        if num_samples:
            eval_set = eval_set[:num_samples]

        results = []
        total_start_time = time.time()

        for i, prompt_data in enumerate(eval_set):
            print(f"Evaluating prompt {i+1}/{len(eval_set)}: {prompt_data['prompt'][:50]}...")

            # Create request
            request = ChatRequest(
                messages=[ChatMessage(role="user", content=prompt_data["prompt"])],
                mode="auto"
            )

            # Make request
            start_time = time.time()
            try:
                response = self.client.post("/v1/chat", json=request.dict())
                latency = time.time() - start_time

                if response.status_code == 200:
                    result = response.json()
                    result["expected_quality"] = prompt_data.get("expected_quality", {})
                    result["actual_latency"] = latency
                    results.append(result)
                else:
                    print(f"Error for prompt {i+1}: {response.text}")
                    results.append({
                        "error": response.text,
                        "prompt": prompt_data["prompt"],
                        "actual_latency": latency
                    })

            except Exception as e:
                print(f"Exception for prompt {i+1}: {str(e)}")
                results.append({
                    "error": str(e),
                    "prompt": prompt_data["prompt"],
                    "actual_latency": time.time() - start_time
                })

        # Calculate summary statistics
        summary = self._calculate_summary(results)
        summary["total_evaluation_time"] = time.time() - total_start_time
        summary["num_prompts_evaluated"] = len(results)

        return {
            "summary": summary,
            "results": results
        }

    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from evaluation results."""
        successful_results = [r for r in results if "error" not in r]

        if not successful_results:
            return {"error": "No successful evaluations"}

        # Basic metrics
        total_requests = len(successful_results)
        fallback_rate = sum(1 for r in successful_results if r.get("fallback_used", False)) / total_requests
        avg_latency = sum(r.get("actual_latency", 0) for r in successful_results) / total_requests
        avg_cost = sum(r["metrics"].get("cost_units", 0) for r in successful_results) / total_requests

        # Judge metrics
        avg_correctness = sum(r["judge"].get("correctness", 0) for r in successful_results) / total_requests
        avg_completeness = sum(r["judge"].get("completeness", 0) for r in successful_results) / total_requests
        format_ok_rate = sum(1 for r in successful_results if r["judge"].get("format_ok", False)) / total_requests

        # Route distribution
        route_counts = {}
        for r in successful_results:
            route = r.get("route", "unknown")
            route_counts[route] = route_counts.get(route, 0) + 1

        return {
            "total_requests": total_requests,
            "fallback_rate": fallback_rate,
            "avg_latency_seconds": avg_latency,
            "avg_cost_units": avg_cost,
            "avg_judge_correctness": avg_correctness,
            "avg_judge_completeness": avg_completeness,
            "format_ok_rate": format_ok_rate,
            "route_distribution": route_counts
        }

    def save_results(self, results: Dict[str, Any], output_path: str = "eval/results.json"):
        """Save evaluation results to file."""
        Path(output_path).parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_path}")

# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run LLM Router Evaluation")
    parser.add_argument("--num-samples", type=int, help="Number of samples to evaluate")
    parser.add_argument("--output", default="eval/results.json", help="Output file path")

    args = parser.parse_args()

    harness = EvaluationHarness()
    results = asyncio.run(harness.run_evaluation(args.num_samples))
    harness.save_results(results, args.output)

    # Print summary
    summary = results["summary"]
    print("\n=== Evaluation Summary ===")
    print(f"Prompts evaluated: {summary['num_prompts_evaluated']}")
    print(".2f")
    print(".2f")
    print(".3f")
    print(".2f")
    print(".2f")
    print(".3f")
    print(f"Route distribution: {summary['route_distribution']}")