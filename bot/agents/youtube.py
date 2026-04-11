import asyncio
import logging

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)

_YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
}


def _extract_sync(url: str) -> dict | None:
    try:
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        logger.warning(f"yt-dlp failed for {url}: {e}")
        return None

    title = info.get("title", "")
    description = (info.get("description") or "")[:500]
    channel = info.get("channel") or info.get("uploader", "")
    duration = info.get("duration", 0)
    thumbnail_url = info.get("thumbnail")
    video_id = info.get("id", "")

    transcript_text = ""
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        try:
            transcript = transcript_list.find_transcript(["it", "en"])
        except Exception:
            transcript = next(iter(transcript_list))
        entries = transcript.fetch()
        transcript_text = " ".join(e["text"] for e in entries)[:3000]
    except Exception as e:
        logger.info(f"No transcript for {video_id}: {e}")

    parts = [
        f"Title: {title}",
        f"Channel: {channel}",
        f"Duration: {duration}s",
        f"Description: {description}",
    ]
    if transcript_text:
        parts.append(f"\nTranscript:\n{transcript_text}")

    return {
        "text": "\n".join(parts),
        "source_url": url,
        "thumbnail_url": thumbnail_url,
    }


async def extract(url: str) -> dict | None:
    """Extract metadata and transcript from a YouTube URL.

    Returns dict with keys: text, source_url, thumbnail_url.
    Returns None on failure.
    """
    try:
        return await asyncio.to_thread(_extract_sync, url)
    except Exception as e:
        logger.error(f"YouTube extraction failed for {url}: {e}")
        return None
