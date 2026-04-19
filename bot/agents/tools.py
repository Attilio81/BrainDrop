import asyncio
import logging

from firecrawl.v1 import V1FirecrawlApp

logger = logging.getLogger(__name__)

_app: V1FirecrawlApp | None = None


def _get_app() -> V1FirecrawlApp:
    global _app
    if _app is None:
        from bot.config import get_settings
        _app = V1FirecrawlApp(api_key=get_settings().FIRECRAWL_API_KEY.get_secret_value())
    return _app


def _scrape_url_sync(url: str) -> str:
    try:
        result = _get_app().scrape_url(url, formats=["markdown"])
        return result.markdown or ""
    except Exception as e:
        logger.warning(f"Firecrawl scraping failed for {url}: {e}")
        return ""


async def scrape_url(url: str) -> str:
    """
    Scrape the full text content of a URL using Firecrawl.
    Returns markdown content, or empty string on failure.
    Runs the blocking Firecrawl call in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _scrape_url_sync, url)
