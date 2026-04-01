import os
from dotenv import load_dotenv

GENRES = ["Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "Comedy"]
CHROMA_DIR = "./chroma_store"
COLLECTION_NAME = "story_memory"

DEFAULT_MODELS = {
    "openai": "gpt-4.1-mini",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "openai/gpt-4.1-mini",
}


def init_env() -> None:
    load_dotenv()


def get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "openai").strip().lower()


def get_model_name() -> str:
    provider = get_provider()
    return os.getenv("MODEL_NAME", DEFAULT_MODELS.get(provider, "gpt-4.1-mini"))


def get_base_url() -> str | None:
    custom = os.getenv("CUSTOM_BASE_URL", "").strip()
    if custom:
        return custom

    provider = get_provider()
    if provider == "groq":
        return "https://api.groq.com/openai/v1"
    if provider == "openrouter":
        return "https://openrouter.ai/api/v1"
    return None


def get_api_key() -> str:
    provider = get_provider()
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "").strip()
    elif provider == "groq":
        key = os.getenv("GROQ_API_KEY", "").strip()
    elif provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    if not key:
        raise ValueError(f"Missing API key for provider '{provider}'. Check your .env file.")
    return key
