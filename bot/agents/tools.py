import logging

from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)

_app: FirecrawlApp | None = None


def _get_app() -> FirecrawlApp:
    global _app
    if _app is None:
        from bot.config import get_settings
        _app = FirecrawlApp(api_key=get_settings().FIRECRAWL_API_KEY.get_secret_value())
    return _app


def scrape_url(url: str) -> str:
    """
    Scrape the full text content of a URL using Firecrawl.
    Returns markdown content, or empty string on failure.
    Called by the Agno agent as a tool (sync, runs in thread pool).
    """
    try:
        result = _get_app().scrape_url(url, formats=["markdown"])
        return result.markdown or ""
    except Exception as e:
        logger.warning(f"Firecrawl scraping failed for {url}: {e}")
        return ""
