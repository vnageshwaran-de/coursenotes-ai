import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Provider ---
# Supported: groq | gemini | ollama | openrouter
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_API_KEY  = os.getenv("LLM_API_KEY", "")
LLM_MODEL    = os.getenv("LLM_MODEL", "llama3-groq-70b-8192-tool-use-preview")

# Provider base URLs (OpenAI-compatible)
PROVIDER_BASE_URLS = {
    "groq":       "https://api.groq.com/openai/v1",
    "gemini":     "https://generativelanguage.googleapis.com/v1beta/openai/",
    "ollama":     "http://localhost:11434/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

# Default models per provider (used if LLM_MODEL not set)
PROVIDER_DEFAULT_MODELS = {
    "groq":       "llama3-groq-70b-8192-tool-use-preview",
    "gemini":     "gemini-2.0-flash",
    "ollama":     "llama3",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
}

# --- Download settings ---
OUTPUT_DIR     = os.getenv("OUTPUT_DIR", "./output")
COOKIE_BROWSER = os.getenv("COOKIE_BROWSER", "firefox")

