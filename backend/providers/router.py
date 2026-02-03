"""Provider router - dispatches to native SDK or OpenRouter fallback."""

import os
from typing import List, Dict, Any, Optional

from .base import BaseProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .openrouter_provider import OpenRouterProvider

# Lazy-initialized provider instances
_openai_provider: OpenAIProvider | None = None
_xai_provider: OpenAIProvider | None = None
_anthropic_provider: AnthropicProvider | None = None
_google_provider: GoogleProvider | None = None
_openrouter_provider: OpenRouterProvider | None = None


def _get_provider(model: str) -> BaseProvider:
    """Get the appropriate provider for the model. Falls back to OpenRouter if native SDK key missing."""
    prefix = model.split("/")[0].lower() if "/" in model else ""

    if prefix == "openai":
        if os.getenv("OPENAI_API_KEY"):
            global _openai_provider
            if _openai_provider is None:
                _openai_provider = OpenAIProvider()
            return _openai_provider
    elif prefix == "x-ai":
        if os.getenv("XAI_API_KEY"):
            global _xai_provider
            if _xai_provider is None:
                _xai_provider = OpenAIProvider(
                    base_url="https://api.x.ai/v1",
                    api_key_env="XAI_API_KEY",
                )
            return _xai_provider
    elif prefix == "anthropic":
        if os.getenv("ANTHROPIC_API_KEY"):
            global _anthropic_provider
            if _anthropic_provider is None:
                _anthropic_provider = AnthropicProvider()
            return _anthropic_provider
    elif prefix == "google":
        if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            global _google_provider
            if _google_provider is None:
                _google_provider = GoogleProvider()
            return _google_provider

    # Fallback to OpenRouter
    global _openrouter_provider
    if _openrouter_provider is None:
        _openrouter_provider = OpenRouterProvider()
    return _openrouter_provider


def _strip_model_prefix(model: str) -> str:
    """Strip provider prefix for native APIs. e.g. openai/gpt-5.1 -> gpt-5.1"""
    if "/" in model:
        return model.split("/", 1)[1]
    return model


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
) -> Optional[Dict[str, Any]]:
    """
    Query a model via the appropriate provider (native SDK or OpenRouter).

    Args:
        model: Model identifier (e.g., "openai/gpt-5.1", "anthropic/claude-sonnet-4.5")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    provider = _get_provider(model)

    # OpenRouter uses full model ID; native APIs use stripped ID
    if isinstance(provider, OpenRouterProvider):
        api_model = model
    else:
        api_model = _strip_model_prefix(model)

    return await provider.query(api_model, messages, timeout)


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel with the same messages.

    Args:
        models: List of model identifiers
        messages: List of message dicts to send to each model
        timeout: Request timeout per model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    tasks = [query_model(m, messages, timeout) for m in models]
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}


async def query_models_parallel_with_messages(
    models: List[str],
    messages_list: List[List[Dict[str, str]]],
    timeout: float = 120.0,
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel, each with its own messages.

    Args:
        models: List of model identifiers
        messages_list: List of message lists, one per model
        timeout: Request timeout per model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    tasks = [
        query_model(models[i], messages_list[i], timeout)
        for i in range(len(models))
    ]
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}
