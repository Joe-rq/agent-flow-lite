import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from .config import settings
from .paths import BACKEND_DATA_DIR

logger = logging.getLogger(__name__)

TOKEN_USAGE_LOG = BACKEND_DATA_DIR / "token_usage.log"
_token_usage_lock = Lock()

SUPPORTED_PROVIDERS = ("deepseek", "openai", "qwen", "ollama")


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    api_key: str
    base_url: str
    default_model: str
    context_window: int


def _provider_configs() -> dict[str, ProviderConfig]:
    s = settings()
    return {
        "deepseek": ProviderConfig(
            provider="deepseek",
            api_key=s.deepseek_api_key,
            base_url=s.deepseek_api_base,
            default_model=s.deepseek_model,
            context_window=s.deepseek_context_window,
        ),
        "openai": ProviderConfig(
            provider="openai",
            api_key=s.openai_api_key,
            base_url=s.openai_api_base,
            default_model=s.openai_model,
            context_window=s.openai_context_window,
        ),
        "qwen": ProviderConfig(
            provider="qwen",
            api_key=s.qwen_api_key,
            base_url=s.qwen_api_base,
            default_model=s.qwen_model,
            context_window=s.qwen_context_window,
        ),
        "ollama": ProviderConfig(
            provider="ollama",
            api_key=s.ollama_api_key,
            base_url=s.ollama_api_base,
            default_model=s.ollama_model,
            context_window=s.ollama_context_window,
        ),
    }


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def estimate_text_tokens(text: str) -> int:
    return _estimate_tokens(text)


def _extract_message_text(message: dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return " ".join(parts)
    return ""


def _estimate_input_tokens(messages: list[dict[str, Any]]) -> int:
    return sum(_estimate_tokens(_extract_message_text(message)) for message in messages)


def estimate_message_tokens(messages: list[dict[str, Any]]) -> int:
    return _estimate_input_tokens(messages)


def _normalize_messages(
    messages: list[dict[str, Any]],
) -> list[ChatCompletionMessageParam]:
    normalized: list[ChatCompletionMessageParam] = []
    for message in messages:
        role = str(message.get("role", "user")).lower()
        content = _extract_message_text(message)
        if role == "system":
            normalized.append({"role": "system", "content": content})
        elif role == "assistant":
            normalized.append({"role": "assistant", "content": content})
        elif role == "tool":
            normalized.append(
                {"role": "tool", "tool_call_id": "tool", "content": content}
            )
        else:
            normalized.append({"role": "user", "content": content})
    return normalized


def _normalize_provider_name(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported provider '{provider}'. Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    return normalized


def _split_model_id(model: str) -> tuple[str | None, str]:
    candidate = model.strip()
    if ":" not in candidate:
        return None, candidate
    provider, model_name = candidate.split(":", 1)
    provider_name = provider.strip().lower()
    if provider_name in SUPPORTED_PROVIDERS and model_name.strip():
        return provider_name, model_name.strip()
    return None, candidate


def _first_provider_with_key(
    configs: dict[str, ProviderConfig],
) -> ProviderConfig | None:
    for provider in SUPPORTED_PROVIDERS:
        cfg = configs[provider]
        if cfg.api_key.strip() and cfg.default_model.strip():
            return cfg
    return None


def _resolve_provider_and_model(
    model: str | None,
    *,
    require_api_key: bool,
) -> tuple[ProviderConfig, str]:
    s = settings()
    configs = _provider_configs()

    preferred_provider = _normalize_provider_name(s.default_llm_provider)
    default_model = s.default_llm_model.strip()

    explicit_provider: str | None = None
    explicit_model: str | None = None

    if model and model.strip():
        explicit_provider, explicit_model = _split_model_id(model)
        if explicit_model is None:
            explicit_model = model.strip()
    elif default_model:
        explicit_provider, explicit_model = _split_model_id(default_model)
        if explicit_model is None:
            explicit_model = default_model

    provider_name = explicit_provider or preferred_provider
    cfg = configs[provider_name]

    if require_api_key and not cfg.api_key.strip():
        if explicit_provider is None:
            fallback = _first_provider_with_key(configs)
            if fallback is not None:
                logger.warning(
                    "Provider '%s' has no API key configured; falling back to '%s'",
                    provider_name,
                    fallback.provider,
                )
                cfg = fallback
            else:
                raise ValueError("No LLM provider API key configured")
        else:
            raise ValueError(f"Provider '{provider_name}' API key is not configured")

    target_model = (explicit_model or cfg.default_model).strip()
    if not target_model:
        raise ValueError(f"Provider '{cfg.provider}' model is not configured")
    return cfg, target_model


def resolve_model(model: str | None = None) -> tuple[str, str]:
    cfg, target_model = _resolve_provider_and_model(model, require_api_key=True)
    return cfg.provider, target_model


def get_model_context_window(model: str | None = None) -> int:
    s = settings()
    cfg, _ = _resolve_provider_and_model(model, require_api_key=False)
    return max(1024, int(cfg.context_window or s.llm_default_context_window))


def get_available_models() -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for provider in SUPPORTED_PROVIDERS:
        cfg = _provider_configs()[provider]
        model_name = cfg.default_model.strip()
        if not model_name:
            continue
        models.append(
            {
                "id": f"{provider}:{model_name}",
                "provider": provider,
                "model": model_name,
                "enabled": bool(cfg.api_key.strip()),
            }
        )
    return models


@lru_cache(maxsize=8)
def _create_client(provider: str, base_url: str, api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


def get_client(model: str | None = None) -> AsyncOpenAI:
    cfg, _ = _resolve_provider_and_model(model, require_api_key=True)
    return _create_client(cfg.provider, cfg.base_url, cfg.api_key)


def _write_token_usage(
    *,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    user_id: int | str | None,
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "input_tokens": max(0, int(input_tokens)),
        "output_tokens": max(0, int(output_tokens)),
        "user_id": str(user_id) if user_id is not None else "anonymous",
    }

    try:
        TOKEN_USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _token_usage_lock:
            with open(TOKEN_USAGE_LOG, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.warning("Failed to write token usage log", exc_info=True)


async def chat_completion(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    user_id: int | str | None = None,
) -> str:
    cfg, target_model = _resolve_provider_and_model(model, require_api_key=True)
    client = _create_client(cfg.provider, cfg.base_url, cfg.api_key)
    estimated_input_tokens = _estimate_input_tokens(messages)
    payload_messages = _normalize_messages(messages)

    try:
        response = await client.chat.completions.create(
            model=target_model,
            messages=payload_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty response from LLM provider")

        content = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        input_tokens = (
            getattr(usage, "prompt_tokens", estimated_input_tokens)
            if usage
            else estimated_input_tokens
        )
        output_tokens = (
            getattr(usage, "completion_tokens", _estimate_tokens(content))
            if usage
            else _estimate_tokens(content)
        )
        _write_token_usage(
            provider=cfg.provider,
            model=target_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
        )
        return content

    except Exception as exc:
        logger.warning(
            "LLM API call failed for provider '%s'", cfg.provider, exc_info=True
        )
        raise RuntimeError(f"LLM API call failed: {exc}") from exc


async def chat_completion_stream(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.7,
    user_id: int | str | None = None,
) -> AsyncGenerator[str, None]:
    cfg, target_model = _resolve_provider_and_model(model, require_api_key=True)
    client = _create_client(cfg.provider, cfg.base_url, cfg.api_key)
    estimated_input_tokens = _estimate_input_tokens(messages)
    output_parts: list[str] = []
    payload_messages = _normalize_messages(messages)

    try:
        stream = await client.chat.completions.create(
            model=target_model,
            messages=payload_messages,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                output_parts.append(token)
                yield token

    except Exception as exc:
        logger.warning(
            "LLM streaming failed for provider '%s'", cfg.provider, exc_info=True
        )
        raise RuntimeError(f"LLM streaming failed: {exc}") from exc
    finally:
        output_tokens = _estimate_tokens("".join(output_parts)) if output_parts else 0
        _write_token_usage(
            provider=cfg.provider,
            model=target_model,
            input_tokens=estimated_input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
        )
