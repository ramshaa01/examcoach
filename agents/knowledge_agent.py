"""Knowledge Agent for synthesizing retrieved RAG document chunks."""
from __future__ import annotations

from typing import Optional

from core.llm_provider import get_llm_provider
from prompts.agent_prompts import KNOWLEDGE_AGENT_PROMPT


def summarize_context(
    chunks: list[str],
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Synthesizes raw retrieved text chunks into a cohesive reference note."""
    if not chunks:
        return ""

    chunks_text = "\n\n---\n\n".join(chunks)
    prompt = KNOWLEDGE_AGENT_PROMPT.format(chunks=chunks_text)

    try:
        provider = get_llm_provider(name=provider_name, api_key=api_key)
        return provider.generate(prompt, tier="fast")
    except Exception as exc:
        print(f"Knowledge agent fallback to raw chunks: {exc}")
        return chunks_text
