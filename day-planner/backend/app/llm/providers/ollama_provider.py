"""Ollama provider using its OpenAI-compatible chat endpoint.

Expected local setup:
1. Run `ollama serve`.
2. Pull a JSON-capable chat model, for example `ollama pull llama3.1`.
3. Set `LLM_PROVIDER=ollama`, `LLM_MODEL=llama3.1`, and optionally
   `LLM_BASE_URL=http://127.0.0.1:11434/v1`.
"""

from app.llm.providers.openai_provider import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    def __init__(self, model: str, base_url: str | None = None):
        super().__init__(
            api_key="ollama",
            model=model,
            base_url=base_url or "http://127.0.0.1:11434/v1",
        )
