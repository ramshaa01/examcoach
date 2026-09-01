"""Model-agnostic LLM provider layer.

Every agent talks to an `LLMProvider` instead of a specific SDK, so the
active model (Gemini / Claude / OpenAI) can be swapped from the UI or
environment config without touching agent logic.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

PROVIDER_ENV_VAR = "EXAMCOACH_LLM_PROVIDER"

# tier "fast" -> quick/cheap model used for generation, tracking, hints
# tier "pro"  -> stronger model used for evaluation and rubric scoring
PROVIDER_MODELS = {
    "gemini": {"fast": "gemini-2.5-flash", "pro": "gemini-2.5-pro"},
    "claude": {"fast": "claude-3-5-sonnet-latest", "pro": "claude-3-7-sonnet-latest"},
    "openai": {"fast": "gpt-4o-mini", "pro": "gpt-4o"},
}

PROVIDER_KEY_ENV = {
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}

PROVIDER_LABELS = {
    "gemini": "Google Gemini",
    "claude": "Anthropic Claude",
    "openai": "OpenAI GPT-4o",
}


class LLMError(RuntimeError):
    """Raised when a provider fails to configure or respond."""


def _mask(key: str) -> str:
    if len(key) > 10:
        return f"{key[:5]}...{key[-5:]}"
    return "EMPTY/SHORT"


class LLMProvider(ABC):
    name: str = "base"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(PROVIDER_KEY_ENV[self.name], "")

    @abstractmethod
    def generate(self, prompt: str, tier: str = "fast", system: Optional[str] = None) -> str:
        """Send `prompt` to the model for the given tier and return the text response."""

    def _require_key(self) -> None:
        if not self.api_key:
            raise LLMError(
                f"{PROVIDER_LABELS[self.name]} API key not configured "
                f"(set {PROVIDER_KEY_ENV[self.name]})."
            )


class GeminiProvider(LLMProvider):
    name = "gemini"

    def generate(self, prompt: str, tier: str = "fast", system: Optional[str] = None) -> str:
        self._require_key()
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            PROVIDER_MODELS["gemini"][tier], system_instruction=system
        )
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            raise LLMError(f"Gemini error (key {_mask(self.api_key)}): {exc}") from exc


class ClaudeProvider(LLMProvider):
    name = "claude"

    def generate(self, prompt: str, tier: str = "fast", system: Optional[str] = None) -> str:
        self._require_key()
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        kwargs = {
            "model": PROVIDER_MODELS["claude"][tier],
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        try:
            response = client.messages.create(**kwargs)
            return "".join(block.text for block in response.content if block.type == "text")
        except Exception as exc:
            raise LLMError(f"Claude error (key {_mask(self.api_key)}): {exc}") from exc


class OpenAIProvider(LLMProvider):
    name = "openai"

    def generate(self, prompt: str, tier: str = "fast", system: Optional[str] = None) -> str:
        self._require_key()
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            response = client.chat.completions.create(
                model=PROVIDER_MODELS["openai"][tier], messages=messages
            )
            return response.choices[0].message.content
        except Exception as exc:
            raise LLMError(f"OpenAI error (key {_mask(self.api_key)}): {exc}") from exc


_PROVIDER_CLASSES = {
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}


def available_providers() -> list[str]:
    return list(_PROVIDER_CLASSES)


def get_llm_provider(name: Optional[str] = None, api_key: Optional[str] = None) -> LLMProvider:
    """Factory: resolve the active provider name from arg -> env -> default 'gemini'."""
    provider_name = (name or os.environ.get(PROVIDER_ENV_VAR, "gemini")).lower()
    cls = _PROVIDER_CLASSES.get(provider_name)
    if cls is None:
        raise LLMError(
            f"Unknown LLM provider '{provider_name}'. Choose from {available_providers()}."
        )
    return cls(api_key=api_key)
