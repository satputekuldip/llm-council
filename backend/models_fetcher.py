"""
Fetch available models from provider APIs/SDKs.
Falls back to static config only when a provider has no list API or fetch fails.
"""

import os
import asyncio
import time
from typing import Dict, List

# Cache TTL in seconds (5 minutes)
_CACHE_TTL = 300
_cache: Dict[str, List[str]] | None = None
_cache_time: float = 0


def clear_models_cache():
    """Clear the models cache (e.g. to force refresh)."""
    global _cache, _cache_time
    _cache = None
    _cache_time = 0


async def get_providers_models() -> Dict[str, List[str]]:
    """
    Get providers and models. Uses API fetch with 5-min cache.
    Falls back to static config when fetch fails.
    """
    global _cache, _cache_time
    if _cache is not None and (time.time() - _cache_time) < _CACHE_TTL:
        return _cache
    _cache = await fetch_providers_models()
    _cache_time = time.time()
    return _cache

# Static fallback - used only when API fetch fails or provider has no list API
STATIC_FALLBACK: Dict[str, List[str]] = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-5.1",
    ],
    "anthropic": [
        "claude-sonnet-4",
        "claude-sonnet-4.5",
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ],
    "google": [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-3-pro-preview",
    ],
    "x-ai": [
        "grok-4",
        "grok-3",
        "grok-2",
    ],
    "openrouter": [
        "openai/gpt-4o",
        "anthropic/claude-sonnet-4",
        "google/gemini-2.5-flash",
    ],
}


async def _fetch_openai_models() -> List[str]:
    """Fetch models from OpenAI API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return STATIC_FALLBACK["openai"]

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        models = []
        async for model in client.models.list():
            mid = getattr(model, "id", None) or getattr(model, "name", None)
            if mid and not mid.startswith("ft:"):  # Skip fine-tuned
                models.append(mid)
        return sorted(set(models)) if models else STATIC_FALLBACK["openai"]
    except Exception as e:
        print(f"OpenAI models fetch failed: {e}")
        return STATIC_FALLBACK["openai"]


async def _fetch_xai_models() -> List[str]:
    """Fetch models from xAI API (OpenAI-compatible)."""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        return STATIC_FALLBACK["x-ai"]

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        models = []
        async for model in client.models.list():
            mid = getattr(model, "id", None) or getattr(model, "name", None)
            if mid:
                models.append(mid)
        return sorted(set(models)) if models else STATIC_FALLBACK["x-ai"]
    except Exception as e:
        print(f"xAI models fetch failed: {e}")
        return STATIC_FALLBACK["x-ai"]


async def _fetch_anthropic_models() -> List[str]:
    """Fetch models from Anthropic API."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return STATIC_FALLBACK["anthropic"]

    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key)
        models = []
        async for m in client.models.list(limit=100):
            mid = getattr(m, "id", None)
            if mid:
                models.append(mid)
        return sorted(set(models)) if models else STATIC_FALLBACK["anthropic"]
    except Exception as e:
        print(f"Anthropic models fetch failed: {e}")
        return STATIC_FALLBACK["anthropic"]


async def _fetch_google_models() -> List[str]:
    """Fetch models from Google Generative AI (google-genai SDK)."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return STATIC_FALLBACK["google"]

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        models = []
        for m in client.models.list():
            name = getattr(m, "name", None)
            if name:
                # name is like "models/gemini-1.5-pro" - strip "models/"
                mid = name.replace("models/", "") if name.startswith("models/") else name
                # Exclude embedding/code models; include if supported_methods has generateContent
                methods = getattr(m, "supported_generation_methods", []) or []
                if "embedding" in mid.lower() or "code" in mid.lower():
                    continue
                if not methods or "generateContent" in methods:
                    models.append(mid)
        return sorted(set(models)) if models else STATIC_FALLBACK["google"]
    except Exception as e:
        print(f"Google models fetch failed: {e}")
        return STATIC_FALLBACK["google"]


async def _fetch_openrouter_models() -> List[str]:
    """Fetch models from OpenRouter API."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return STATIC_FALLBACK["openrouter"]

    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            data = r.json()
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            return sorted(set(models))[:200] if models else STATIC_FALLBACK["openrouter"]
    except Exception as e:
        print(f"OpenRouter models fetch failed: {e}")
        return STATIC_FALLBACK["openrouter"]


async def fetch_providers_models() -> Dict[str, List[str]]:
    """
    Fetch models from all provider APIs in parallel.
    Falls back to static config when API fails or key is missing.
    """
    results = await asyncio.gather(
        _fetch_openai_models(),
        _fetch_xai_models(),
        _fetch_anthropic_models(),
        _fetch_google_models(),
        _fetch_openrouter_models(),
        return_exceptions=True,
    )

    providers = ["openai", "x-ai", "anthropic", "google", "openrouter"]
    out = {}
    for provider, result in zip(providers, results):
        if isinstance(result, Exception):
            print(f"{provider} models fetch error: {result}")
            out[provider] = STATIC_FALLBACK[provider]
        else:
            out[provider] = result

    return out
