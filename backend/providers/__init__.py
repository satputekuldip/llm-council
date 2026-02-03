"""LLM providers - native SDKs with OpenRouter fallback."""

from .router import (
    query_model,
    query_models_parallel,
    query_models_parallel_with_messages,
)

__all__ = [
    "query_model",
    "query_models_parallel",
    "query_models_parallel_with_messages",
]
