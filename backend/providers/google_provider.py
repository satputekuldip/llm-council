"""Google Generative AI provider (google-genai SDK)."""

import os
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types
from .base import BaseProvider


class GoogleProvider(BaseProvider):
    """Google Generative AI provider using google-genai SDK."""

    async def query(
        self,
        model: str,
        messages: List[Dict[str, str]],
        timeout: float = 120.0,
    ) -> Optional[Dict[str, Any]]:
        """Query Google Generative AI API."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Google: GOOGLE_API_KEY or GEMINI_API_KEY not set")
            return None

        client = genai.Client(api_key=api_key)

        # Flatten: system content prepended to first user message; build prompt
        system_content = None
        user_content = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_content = content
            elif role == "user":
                user_content = content
                break

        if user_content is None:
            return None

        try:
            config = None
            if system_content:
                config = types.GenerateContentConfig(system_instruction=system_content)

            response = await client.aio.models.generate_content(
                model=model,
                contents=user_content,
                config=config,
            )

            text = getattr(response, "text", None) or ""
            return {
                "content": text,
                "reasoning_details": None,
            }

        except Exception as e:
            print(f"Error querying Google model {model}: {e}")
            return None
