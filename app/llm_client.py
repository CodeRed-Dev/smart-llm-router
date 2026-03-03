"""
Local LLM client that can target either Hugging Face checkpoints or an Ollama CLI-managed model.

The router selects the backend via the `LLM_BACKEND` setting so you can point to locally cached
Hugging Face models (`transformers`) or to Ollama models via the CLI.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

from config import settings

MODEL_ROUTES = {"fast", "strong", "judge"}

logger = logging.getLogger(__name__)


def _resolve_device():
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise RuntimeError("The transformers backend requires torch. Install it before using that backend.") from exc

    preferred = settings.MODEL_DEVICE.lower()
    if preferred == "auto":
        return torch, torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if preferred in {"cpu", "cuda"}:
        return torch, torch.device(preferred)
    logger.warning("Unknown MODEL_DEVICE=%s falling back to auto", settings.MODEL_DEVICE)
    return torch, torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _build_prompt(messages: List[Dict[str, str]]) -> str:
    lines = []
    for message in messages:
        role = message.get("role", "user").capitalize()
        content = message.get("content", "")
        lines.append(f"{role}: {content}")
    lines.append("Assistant:")
    return "\n".join(lines)


class _TransformersLocalModel:
    def __init__(self, model_path: str, device: Any, torch_mod: Any):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model_path = model_path
        self.device = device
        self.torch = torch_mod
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id or 0

        dtype = self.torch.float16 if self.device.type == "cuda" else self.torch.float32
        load_kwargs = {"torch_dtype": dtype, "low_cpu_mem_usage": True}
        self.model = AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs)
        self.model.to(self.device)

    def generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        output_ids = self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            use_cache=True,
        )
        generated = output_ids[0][input_ids.shape[-1] :]
        text = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
        return text or "<no response>"


class _TransformersLLMClient:
    def __init__(self):
        self.torch, self.device = _resolve_device()
        self._model_registry: Dict[str, _TransformersLocalModel] = {}
        self._route_models = {
            "fast": settings.FAST_MODEL_PATH,
            "strong": settings.STRONG_MODEL_PATH,
            "judge": settings.JUDGE_MODEL_PATH,
        }

    def _get_model(self, route: str) -> _TransformersLocalModel:
        if route not in MODEL_ROUTES:
            raise ValueError(f"Unknown route: {route}")
        if route not in self._model_registry:
            self._model_registry[route] = _TransformersLocalModel(
                self._route_models[route], self.device, self.torch
            )
        return self._model_registry[route]

    def call_model(self, route: str, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
        model = self._get_model(route)
        prompt = _build_prompt(messages)
        return model.generate(prompt, max_tokens, temperature)

    def call_judge(self, prompt: str) -> Dict[str, str]:
        judge_messages = [{"role": "user", "content": prompt}]
        raw = self.call_model("judge", judge_messages, max_tokens=512, temperature=0.1)
        return {"notes": raw}

    def get_model_name(self, route: str) -> str:
        return self._route_models.get(route, "<unknown>")


class _OllamaLLMClient:
    def __init__(self):
        self._route_models = {
            "fast": settings.FAST_MODEL_PATH,
            "strong": settings.STRONG_MODEL_PATH,
            "judge": settings.JUDGE_MODEL_PATH,
        }
        self._binary = settings.OLLAMA_BIN_PATH or "ollama"
        if not shutil.which(self._binary):
            raise FileNotFoundError(f"Ollama binary not found at '{self._binary}'")

    def _extract_from_payload(self, payload: Dict[str, Any]) -> Optional[str]:
        if not isinstance(payload, dict):
            return None
        for key in ("message", "response", "text", "output"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        if isinstance(payload.get("choices"), list):
            for choice in payload["choices"]:
                if isinstance(choice, dict):
                    content = choice.get("message") or {}
                    text = content.get("text") or content.get("content")
                    if isinstance(text, str):
                        return text
                    content_text = choice.get("text")
                    if isinstance(content_text, str):
                        return content_text
        return None

    def _extract_message(self, raw: str) -> str:
        cleaned_lines = []
        for line in raw.splitlines():
            clean = line.strip()
            if clean and not clean.startswith(""):
                cleaned_lines.append(clean)

        parsed_payloads = []
        for clean in cleaned_lines:
            try:
                parsed_payloads.append(json.loads(clean))
            except json.JSONDecodeError:
                continue

        for payload in parsed_payloads:
            result = self._extract_from_payload(payload)
            if isinstance(result, str):
                return result

        if cleaned_lines:
            return "\n".join(cleaned_lines)
        return "<no response>"

    def _run_model(self, route: str, prompt: str) -> str:
        model_name = self._route_models.get(route)
        if not model_name:
            raise ValueError(f"No Ollama model configured for route '{route}'")
        cmd = [self._binary, "run", model_name, prompt, "--hidethinking", "--format", "json"]
        logger.debug("Running Ollama command: %s", " ".join(cmd))
        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            message = exc.stderr.strip() or exc.stdout.strip()
            logger.error("Ollama command failed after %.1fms: %s", duration_ms, message)
            raise RuntimeError(f"Ollama command failed: {message}") from exc
        duration_ms = (time.perf_counter() - start_time) * 1000
        stdout_len = len(proc.stdout or "")
        stderr_len = len(proc.stderr or "")
        logger.debug(
            "Ollama route=%s completed in %.1fms (stdout=%d bytes, stderr=%d bytes)",
            route,
            duration_ms,
            stdout_len,
            stderr_len,
        )
        snippet = (proc.stdout or "").strip().replace("\n", "\\n")
        if snippet:
            logger.debug("Ollama route=%s response snippet: %s", route, snippet[:320])
        return self._extract_message(proc.stdout)

    def call_model(self, route: str, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
        prompt = _build_prompt(messages)
        return self._run_model(route, prompt)

    def call_judge(self, prompt: str) -> Dict[str, str]:
        return {"notes": self._run_model("judge", prompt)}

    def get_model_name(self, route: str) -> str:
        return self._route_models.get(route, "<unknown>")


class LLMClient:
    """
    Facade that delegates to either the Hugging Face-backed client or Ollama CLI client.
    """

    def __init__(self):
        backend = settings.LLM_BACKEND.lower()
        if backend == "transformers":
            self._client = _TransformersLLMClient()
        else:
            self._client = _OllamaLLMClient()

    def call_model(self, route: str, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
        return self._client.call_model(route, messages, max_tokens, temperature)

    def get_model_name(self, route: str) -> str:
        return self._client.get_model_name(route)

    def call_judge(self, prompt: str) -> Dict[str, str]:
        return self._client.call_judge(prompt)
