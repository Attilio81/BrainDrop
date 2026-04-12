import logging

import httpx

logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> list[float] | None:
    """Generate a 1536-dim embedding using OpenAI text-embedding-3-small.

    Returns None on failure — embedding is optional, search degrades gracefully.
    """
    from bot.config import get_settings

    api_key = get_settings().OPENAI_API_KEY.get_secret_value()
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                json={"model": "text-embedding-3-small", "input": text[:8000]},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        return None
