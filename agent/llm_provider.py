from openai import OpenAI
from config import (
    LLM_PROVIDER,
    LLM_API_KEY,
    LLM_MODEL,
    PROVIDER_BASE_URLS,
    PROVIDER_DEFAULT_MODELS,
)


def get_client() -> OpenAI:
    """Return an OpenAI-compatible client for the configured provider."""
    base_url = PROVIDER_BASE_URLS.get(LLM_PROVIDER)
    if not base_url:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. "
            f"Choose from: {list(PROVIDER_BASE_URLS.keys())}"
        )

    # Ollama runs locally — no API key needed
    api_key = LLM_API_KEY if LLM_API_KEY else "ollama"

    return OpenAI(api_key=api_key, base_url=base_url)


def get_model() -> str:
    """Return the model name, falling back to provider default if not set."""
    if LLM_MODEL:
        return LLM_MODEL
    return PROVIDER_DEFAULT_MODELS.get(LLM_PROVIDER, "llama-3.3-70b-versatile")
