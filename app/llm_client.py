"""
LLM Client Module

Handles communication with different LLM models (fast, strong, judge)
using Ollama for local inference with timeouts and retries.
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any
from app.config import settings

class LLMClient:
    def __init__(self):
        self.fast_model = settings.FAST_MODEL_NAME
        self.strong_model = settings.STRONG_MODEL_NAME
        self.judge_model = settings.JUDGE_MODEL_NAME
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.timeout = settings.LLM_TIMEOUT_SECONDS
        self.max_retries = settings.MAX_RETRIES

    async def call_model(self, route: str, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
        """
        Call the appropriate model based on route.
        """
        model_name = self.get_model_name(route)

        # Prepare Ollama API request
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.ollama_base_url}/api/chat",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result["message"]["content"]
                        else:
                            raise Exception(f"Ollama API error: {response.status}")

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed to call {model_name} after {self.max_retries} attempts: {str(e)}")
                await asyncio.sleep(0.5 * (2 ** attempt))  # Exponential backoff

    def get_model_name(self, route: str) -> str:
        """Get the actual model name for a route."""
        if route == "fast":
            return self.fast_model
        elif route == "strong":
            return self.strong_model
        elif route == "judge":
            return self.judge_model
        else:
            raise ValueError(f"Unknown route: {route}")

    async def call_judge(self, prompt: str) -> Dict[str, Any]:
        """
        Call the judge model for evaluation.
        """
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_model("judge", messages, max_tokens=200, temperature=0.1)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if judge doesn't return valid JSON
            return {
                "correctness": 7,
                "completeness": 7,
                "format_ok": True,
                "hallucination_risk": 3,
                "should_fallback": False,
                "notes": "Judge response parsing failed, using defaults"
            }