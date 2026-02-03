"""OpenAI API provider - also used for xAI via base_url."""

import os
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    def __init__(self, base_url: str | None = None, api_key_env: str = "OPENAI_API_KEY"):
        self.base_url = base_url
        self.api_key_env = api_key_env

    async def query(
        self,
        model: str,
        messages: List[Dict[str, str]],
        timeout: float = 120.0,
    ) -> Optional[Dict[str, Any]]:
        """Query OpenAI API."""
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            print(f"OpenAI: {self.api_key_env} not set")
            return None

        client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=timeout,
            )
            message = response.choices[0].message

            return {
                "content": message.content,
                "reasoning_details": getattr(message, "reasoning_details", None),
            }

        except Exception as e:
            print(f"Error querying OpenAI model {model}: {e}")
            return None
