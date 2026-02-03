"""Anthropic API provider."""

import os
from typing import List, Dict, Any, Optional

from anthropic import AsyncAnthropic
from .base import BaseProvider


def _convert_messages(messages: List[Dict[str, str]]) -> tuple[str | None, List[Dict[str, str]]]:
    """
    Convert OpenAI-format messages to Anthropic format.
    Anthropic uses system prompt separately and doesn't support 'system' role in messages.
    """
    system_content = None
    anthropic_messages = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            system_content = content
        elif role in ("user", "assistant"):
            anthropic_messages.append({"role": role, "content": content})

    return system_content, anthropic_messages


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    async def query(
        self,
        model: str,
        messages: List[Dict[str, str]],
        timeout: float = 120.0,
    ) -> Optional[Dict[str, Any]]:
        """Query Anthropic API."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Anthropic: ANTHROPIC_API_KEY not set")
            return None

        system_content, anthropic_messages = _convert_messages(messages)
        if not anthropic_messages:
            return None

        client = AsyncAnthropic(api_key=api_key)

        try:
            kwargs = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": 8192,
            }
            if system_content:
                kwargs["system"] = system_content

            response = await client.messages.create(**kwargs)

            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return {
                "content": content or None,
                "reasoning_details": None,
            }

        except Exception as e:
            print(f"Error querying Anthropic model {model}: {e}")
            return None
