import pytest

from app.core import config
from app.core import llm as llm_module


def test_split_model_id() -> None:
    assert llm_module._split_model_id("gpt-4") == (None, "gpt-4")
    assert llm_module._split_model_id("openai:gpt-4") == ("openai", "gpt-4")
    assert llm_module._split_model_id("OPENAI:gpt-4") == ("openai", "gpt-4")
    assert llm_module._split_model_id("openai:") == (None, "openai:")
    assert llm_module._split_model_id("unknown:model") == (None, "unknown:model")


def test_normalize_provider_name() -> None:
    assert llm_module._normalize_provider_name(" OpenAI ") == "openai"
    with pytest.raises(ValueError):
        llm_module._normalize_provider_name("not-a-provider")


def test_extract_and_normalize_messages() -> None:
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": [{"text": "a"}, {"text": "b"}]},
        {"role": "tool", "content": "tool"},
        {"role": "user", "content": "hi"},
    ]

    assert llm_module._extract_message_text(messages[1]) == "a b"
    normalized = llm_module._normalize_messages(messages)
    assert normalized[0]["role"] == "system"
    assert normalized[1]["role"] == "assistant"
    assert normalized[2]["role"] == "tool"
    assert normalized[3]["role"] == "user"


def test_resolve_model_uses_fallback_when_default_provider_has_no_key() -> None:
    original = config._settings
    try:
        config._settings = config.Settings(
            default_llm_provider="deepseek",
            default_llm_model="",
            deepseek_api_key="",
            openai_api_key="key-openai",
            qwen_api_key="",
            openai_model="gpt-4o-mini",
        )
        provider, model = llm_module.resolve_model(None)
        assert provider == "openai"
        assert model == "gpt-4o-mini"
    finally:
        config._settings = original


def test_resolve_model_raises_when_no_keys_configured() -> None:
    original = config._settings
    try:
        config._settings = config.Settings(
            default_llm_provider="deepseek",
            deepseek_api_key="",
            openai_api_key="",
            qwen_api_key="",
        )
        with pytest.raises(ValueError):
            llm_module.resolve_model(None)
    finally:
        config._settings = original
