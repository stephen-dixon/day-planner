"""Provider interface for structured LLM calls."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
    ) -> dict:
        """Return a JSON object matching the provided schema."""
