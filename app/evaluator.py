"""
Evaluator Module

Handles quality evaluation of LLM responses using the judge model.
Implements the judge criteria from the product spec.
"""

from typing import List, Dict, Any
from app.llm_client import LLMClient

class JudgeEvaluator:
    def __init__(self):
        self.llm_client = LLMClient()

    async def evaluate_response(self, messages: List[Dict[str, str]], response: str) -> Dict[str, Any]:
        """
        Evaluate the quality of an LLM response using the judge model.
        """
        # Create judge prompt
        user_prompt = messages[-1]["content"]
        judge_prompt = self._create_judge_prompt(user_prompt, response)

        # Get judge evaluation
        judge_raw = await self.llm_client.call_judge(judge_prompt)

        # Parse and validate judge response
        return self._parse_judge_response(judge_raw)

    def _create_judge_prompt(self, user_prompt: str, response: str) -> str:
        """
        Create the evaluation prompt for the judge model.
        """
        return f"""Evaluate the following AI response for quality. Return ONLY a JSON object with these exact fields:

{{
  "correctness": <0-10 integer, how factually accurate and correct the answer is>,
  "completeness": <0-10 integer, how complete and comprehensive the answer is>,
  "format_ok": <boolean, true if format matches request (e.g., JSON if requested)>,
  "hallucination_risk": <0-10 integer, risk of made-up information>,
  "should_fallback": <boolean, true if this answer is poor enough to warrant fallback to stronger model>,
  "notes": "<brief explanation of the evaluation>"
}}

User Query: {user_prompt}

AI Response: {response}

Evaluation:"""

    def _parse_judge_response(self, judge_raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate the judge response, providing defaults if needed.
        """
        try:
            # Ensure all required fields are present with correct types
            result = {
                "correctness": int(judge_raw.get("correctness", 7)),
                "completeness": int(judge_raw.get("completeness", 7)),
                "format_ok": bool(judge_raw.get("format_ok", True)),
                "hallucination_risk": int(judge_raw.get("hallucination_risk", 3)),
                "should_fallback": bool(judge_raw.get("should_fallback", False)),
                "notes": str(judge_raw.get("notes", "Evaluation completed"))
            }

            # Clamp values to valid ranges
            result["correctness"] = max(0, min(10, result["correctness"]))
            result["completeness"] = max(0, min(10, result["completeness"]))
            result["hallucination_risk"] = max(0, min(10, result["hallucination_risk"]))

            # Additional fallback logic based on thresholds
            if result["correctness"] < 5 or not result["format_ok"]:
                result["should_fallback"] = True

            return result

        except (ValueError, TypeError):
            # If parsing fails, return conservative defaults
            return {
                "correctness": 5,
                "completeness": 5,
                "format_ok": False,
                "hallucination_risk": 5,
                "should_fallback": True,
                "notes": "Judge evaluation failed, triggering fallback"
            }