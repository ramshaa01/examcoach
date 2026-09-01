"""Unit tests for the LLM Provider abstraction layer."""
import pytest
from core.llm_provider import (
    available_providers,
    get_llm_provider,
    LLMError,
    GeminiProvider,
    ClaudeProvider,
    OpenAIProvider,
)


def test_available_providers():
    providers = available_providers()
    assert "gemini" in providers
    assert "claude" in providers
    assert "openai" in providers


def test_provider_factory_instantiation():
    gemini = get_llm_provider("gemini", api_key="dummy_key_1234567890")
    assert isinstance(gemini, GeminiProvider)
    assert gemini.api_key == "dummy_key_1234567890"

    claude = get_llm_provider("claude", api_key="dummy_key_1234567890")
    assert isinstance(claude, ClaudeProvider)

    openai = get_llm_provider("openai", api_key="dummy_key_1234567890")
    assert isinstance(openai, OpenAIProvider)


def test_unknown_provider_raises_error():
    with pytest.raises(LLMError):
        get_llm_provider("invalid_provider_name")


def test_missing_api_key_raises_error():
    prov = get_llm_provider("gemini", api_key="")
    with pytest.raises(LLMError):
        prov.generate("Hello")
