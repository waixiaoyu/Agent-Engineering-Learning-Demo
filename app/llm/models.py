from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
import os

import requests

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - dotenv is optional at runtime.
    load_dotenv = None

if load_dotenv:
    load_dotenv()


DEFAULT_GLM_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_GLM_MODEL = "glm-5.1"
DEFAULT_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class LlmConfig:
    provider: str
    endpoint: str
    model: str
    api_key: str
    temperature: float
    max_tokens: int
    timeout_seconds: int


def build_chat_model() -> "OpenAICompatibleChatModel | None":
    config = get_llm_config()
    if not config:
        return None
    return OpenAICompatibleChatModel(config)


def get_llm_config() -> LlmConfig | None:
    if not _env_flag("LLM_ENABLED", default=True):
        return None

    provider = _normalize_provider(os.getenv("LLM_PROVIDER", "glm"))
    endpoint = (
        os.getenv("LLM_API_URL")
        or os.getenv("GLM_API_URL")
        or os.getenv("OPENAI_API_URL")
        or DEFAULT_GLM_ENDPOINT
    )
    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("GLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    ).strip()
    model = (
        os.getenv("LLM_MODEL")
        or os.getenv("GLM_MODEL")
        or os.getenv("OPENAI_MODEL")
        or DEFAULT_GLM_MODEL
    )

    if provider in {"glm", "zhipu", "bigmodel"}:
        provider = "glm"
    if not api_key:
        return None

    return LlmConfig(
        provider=provider,
        endpoint=endpoint,
        model=model,
        api_key=api_key,
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1600")),
        timeout_seconds=int(int(os.getenv("LLM_REQUEST_TIMEOUT_MS", str(DEFAULT_TIMEOUT_SECONDS * 1000))) / 1000),
    )


def llm_status() -> dict[str, Any]:
    config = get_llm_config()
    if not config:
        return {
            "enabled": False,
            "provider": _normalize_provider(os.getenv("LLM_PROVIDER", "glm")),
            "model": os.getenv("LLM_MODEL") or os.getenv("GLM_MODEL") or DEFAULT_GLM_MODEL,
            "endpoint": os.getenv("LLM_API_URL") or os.getenv("GLM_API_URL") or DEFAULT_GLM_ENDPOINT,
        }
    return {
        "enabled": True,
        "provider": config.provider,
        "model": config.model,
        "endpoint": config.endpoint,
    }


class OpenAICompatibleChatModel:
    def __init__(self, config: LlmConfig) -> None:
        self.config = config

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, str] | None = None,
        max_tokens: int | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        response = requests.post(
            self.config.endpoint,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"LLM request failed with {response.status_code}: {response.text[:300]}")

        data = response.json()
        return _text_from_response(data)

    def complete_json(self, messages: list[dict[str, str]], *, max_tokens: int | None = None) -> dict[str, Any]:
        text = self.complete(
            messages,
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"LLM did not return valid JSON: {text[:300]}") from exc


def _text_from_response(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        if isinstance(message.get("content"), str):
            return message["content"]
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    return ""


def _normalize_provider(provider: str | None) -> str:
    value = (provider or "").strip().lower()
    if value in {"zhipu", "zhipuai", "bigmodel"}:
        return "glm"
    if value in {"glm", "openai"}:
        return value
    return "glm"


def _env_flag(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}
