import logging

from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)


def scrape_url(url: str) -> str:
    """
    Scrape the full text content of a URL using Firecrawl.
    Returns markdown content, or empty string on failure.
    Called by the Agno agent as a tool.
    """
    from bot.config import get_settings
    settings = get_settings()
    try:
        app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY.get_secret_value())
        result = app.scrape_url(url, formats=["markdown"])
        return result.markdown or ""
    except Exception as e:
        logger.warning(f"Firecrawl scraping failed for {url}: {e}")
        return ""
