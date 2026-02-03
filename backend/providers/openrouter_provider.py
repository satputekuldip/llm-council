"""OpenRouter API provider - fallback for models without native SDK support."""

import httpx
from typing import List, Dict, Any, Optional

from .base import BaseProvider
from ..config import OPENROUTER_API_KEY, OPENROUTER_API_URL


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider using httpx."""

    async def query(
        self,
        model: str,
        messages: List[Dict[str, str]],
        timeout: float = 120.0,
    ) -> Optional[Dict[str, Any]]:
        """Query OpenRouter API."""
        if not OPENROUTER_API_KEY:
            print("OpenRouter: OPENROUTER_API_KEY not set")
            return None

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                message = data["choices"][0]["message"]

                return {
                    "content": message.get("content"),
                    "reasoning_details": message.get("reasoning_details"),
                }

        except Exception as e:
            print(f"Error querying OpenRouter model {model}: {e}")
            return None
