import asyncio
import base64
import logging
import re
import tempfile
import time
from pathlib import Path

import httpx
import instaloader

from bot.config import get_settings

logger = logging.getLogger(__name__)

_SHORTCODE_RE = re.compile(r"instagram\.com/(?:p|reel)/([A-Za-z0-9_-]+)")
_OCR_PROMPT = (
    "Extract all visible text from this image. "
    "Return only the text, preserving reading order. "
    "If there is no text, return an empty string."
)


def _get_shortcode(url: str) -> str | None:
    m = _SHORTCODE_RE.search(url)
    return m.group(1) if m else None


def _ocr_image(image_path: Path, api_key: str) -> str:
    b64 = base64.b64encode(image_path.read_bytes()).decode()
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": _OCR_PROMPT},
        ]}],
        "max_tokens": 1024,
    }
    for attempt in range(3):
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if resp.status_code == 429:
            wait = 2 ** attempt + 1
            logger.warning(f"OpenAI 429 rate limit, retrying in {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    resp.raise_for_status()  # raise after exhausting retries
    return ""


def _extract_sync(url: str) -> dict | None:
    shortcode = _get_shortcode(url)
    if not shortcode:
        return None

    settings = get_settings()
    api_key = settings.OPENAI_API_KEY.get_secret_value()

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except Exception as e:
        logger.warning(f"instaloader failed for shortcode {shortcode}: {e}")
        return None

    caption = post.caption or ""
    thumbnail_url = post.url
    slide_texts: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        if post.typename == "GraphSidecar":
            image_urls = [
                node.display_url
                for node in post.get_sidecar_nodes()
                if not node.is_video
            ]
        elif not post.is_video:
            image_urls = [post.url]
        else:
            image_urls = []  # Reel — no images, use caption only

        for i, img_url in enumerate(image_urls):
            if i > 0:
                time.sleep(0.5)  # avoid OpenAI rate limit on caroselli with many slides
            try:
                with httpx.Client(timeout=30) as client:
                    r = client.get(img_url)
                    r.raise_for_status()
                img_path = tmpdir_path / f"slide_{i}.jpg"
                img_path.write_bytes(r.content)
                text = _ocr_image(img_path, api_key)
                if text:
                    slide_texts.append(f"Slide {i + 1}:\n{text}")
            except Exception as e:
                logger.warning(f"OCR failed for slide {i} of {shortcode}: {e}")

    parts: list[str] = []
    if caption:
        parts.append(f"Caption: {caption}")
    parts.extend(slide_texts)

    if not parts:
        logger.warning(f"No content extracted from {shortcode}")
        return None

    return {
        "text": "\n\n".join(parts),
        "source_url": url,
        "thumbnail_url": thumbnail_url,
    }


async def extract(url: str) -> dict | None:
    """Extract caption and OCR text from an Instagram post URL.

    Returns dict with keys: text, source_url, thumbnail_url.
    Returns None on failure (private post, blocked, etc.).
    """
    try:
        return await asyncio.to_thread(_extract_sync, url)
    except Exception as e:
        logger.error(f"Instagram extraction failed for {url}: {e}")
        return None
