import base64
import logging
from pathlib import Path

import httpx

from bot.config import get_settings

logger = logging.getLogger(__name__)

_PHOTO_PROMPT = (
    "Describe this image in detail. "
    "If it contains text, extract all visible text. "
    "Focus on content relevant for a knowledge base entry."
)


async def extract(file_path: str) -> str | None:
    """Send a local image file to GPT-4o-mini Vision for description/OCR.

    Returns the description string, or None on failure.
    """
    settings = get_settings()
    api_key = settings.OPENAI_API_KEY.get_secret_value()

    try:
        b64 = base64.b64encode(Path(file_path).read_bytes()).decode()
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": _PHOTO_PROMPT},
            ]}],
            "max_tokens": 1024,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Photo extraction failed for {file_path}: {e}")
        return None
