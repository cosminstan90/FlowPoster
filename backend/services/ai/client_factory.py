"""
Returns the correct AI client (Claude or OpenAI) based on model name prefix.

Usage:
    client = get_ai_client("gpt-4o")          # → OpenAIClient
    client = get_ai_client("claude-sonnet-4-6")  # → ClaudeClient
"""
from __future__ import annotations

_OPENAI_PREFIXES = ("gpt-", "o1-", "o1", "o3-", "o3")

# Fast/cheap fallback per provider — used for utility steps (intent, SEO, schema, validator)
_FAST_MODEL: dict[str, str] = {
    "openai":    "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-6",
}


def get_ai_client(model: str):
    """Return ClaudeClient or OpenAIClient for the given model name."""
    if _is_openai(model):
        from backend.services.ai.openai_client import OpenAIClient
        return OpenAIClient(model)
    from backend.services.ai.claude_client import ClaudeClient
    return ClaudeClient(model)


def get_fast_client(campaign_model: str):
    """
    Return a cheap/fast client from the same provider as the campaign model.
    Used for classification, SEO metadata, schema, and validation steps.
    """
    provider = "openai" if _is_openai(campaign_model) else "anthropic"
    return get_ai_client(_FAST_MODEL[provider])


def _is_openai(model: str) -> bool:
    return any(model.startswith(p) for p in _OPENAI_PREFIXES)
