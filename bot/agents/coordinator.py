import asyncio
import logging

from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.tools.tavily import TavilyTools
from agno.tools.youtube import YouTubeTools

from bot.agents.tools import scrape_url
from db.models import EnrichedIdea

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a personal knowledge assistant. You receive raw text or URLs
and produce structured knowledge entries.

Processing rules:
1. If it's a YouTube URL, use get_youtube_video_data (title/channel/thumbnail) then
   get_youtube_video_captions (transcript). Do NOT use Tavily or scrape_url for YouTube.
2. If it's any other URL, use scrape_url to extract the full content. Do NOT use Tavily unless
   scrape_url returns empty or fails.
3. If it's pre-extracted content (starts with "Caption:", "Slide", "[Telegram photo]",
   "[Voice note]"), work directly with the provided text. Do NOT call any tools.
4. If it's short plain text (under 100 chars) with no URL and no extracted content, use Tavily
   once to find context. This is the ONLY case where Tavily should be called proactively.
5. CRITICAL: Always produce the structured output regardless of tool failures. If a tool fails,
   proceed with whatever information is already available. Never abort.

Output:
- title: concise English title, max 10 words
- summary: narrative prose IN ITALIAN covering ALL content (5-10 sentences, no bullet points,
  self-contained — reader should need nothing else)
- category: one of tech, programming, ai, crossfit, travel, food, business, personal, other
- tags: up to 5 lowercase specific tags (prefer "llm" over "ai", "react" over "javascript")
- source_url: original URL if present in the input. If the content's primary subject is a
  single GitHub repository (e.g. the post is specifically about github.com/user/repo), set
  source_url to that repository URL instead. If multiple repos are mentioned, keep the
  original input URL.
- thumbnail_url: if found (e.g. from get_youtube_video_data)"""

_MAX_RETRIES = 3


class Coordinator:
    def __init__(self) -> None:
        self._agent = Agent(
            model=DeepSeek(id="deepseek-chat"),
            tools=[
                TavilyTools(search_depth="advanced", include_answer=True),
                YouTubeTools(languages=["it", "en", "a.it", "a.en"]),
                scrape_url,
            ],
            instructions=SYSTEM_PROMPT,
            output_schema=EnrichedIdea,
        )

    async def process(self, text: str) -> EnrichedIdea:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._agent.arun(text)
                if not isinstance(response.content, EnrichedIdea):
                    raise ValueError(f"Agent returned unexpected output: {response.content!r}")
                return response.content
            except Exception as e:
                last_exc = e
                if attempt < _MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        f"Coordinator attempt {attempt + 1}/{_MAX_RETRIES} failed: {e}. "
                        f"Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
        raise last_exc  # type: ignore[misc]
