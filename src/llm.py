from openai import OpenAI

from src.config import get_api_key, get_base_url


def get_client() -> OpenAI:
    base_url = get_base_url()
    api_key = get_api_key()

    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def generate_text(
    *,
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> str:
    try:
        response = client.responses.create(
            model=model,
            temperature=temperature,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.output_text.strip()
    except Exception as exc:
        message = str(exc).lower()
        if "rate" in message or "429" in message:
            raise RuntimeError("Rate limit reached, try again in a moment.") from exc
        raise
