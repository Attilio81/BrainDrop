import logging
import os

from openai import AsyncOpenAI

from bot.config import get_settings

logger = logging.getLogger(__name__)

_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB — OpenAI Whisper limit


async def transcribe(file_path: str) -> str | None:
    """Transcribe a voice note (OGG) using OpenAI Whisper.

    Returns the transcription text, or None on failure.
    """
    if os.path.getsize(file_path) > _MAX_FILE_SIZE:
        logger.warning(f"Voice file too large to transcribe: {file_path}")
        return None

    settings = get_settings()
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
        with open(file_path, "rb") as f:
            result = await client.audio.transcriptions.create(
                file=f,
                model="whisper-1",
            )
        return result.text
    except Exception as e:
        logger.error(f"Voice transcription failed for {file_path}: {e}")
        return None
