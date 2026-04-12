from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.tools.tavily import TavilyTools
from agno.tools.youtube import YouTubeTools

from bot.agents.tools import scrape_url
from db.models import EnrichedIdea

SYSTEM_PROMPT = """You are a personal knowledge assistant. You receive raw text or URLs
and produce structured knowledge entries.

For each input:
1. If it's a YouTube URL, use get_youtube_video_data to get title/channel/thumbnail, then
   get_youtube_video_captions to get the transcript. Use Tavily only if no transcript is available.
2. If it's any other URL, use the scrape_url tool to extract its content, then search Tavily for
   additional context.
3. If it's plain text, search Tavily to find what it refers to and enrich it.
4. Produce a concise English title (max 10 words), a summary IN ITALIAN, a category from the
   allowed list, and up to 5 lowercase tags.
5. Always set source_url to the original URL if provided.
6. Always set thumbnail_url if you found one (e.g. from get_youtube_video_data).

Summary guidelines (IN ITALIAN):
Write a well-argued narrative text in Italian that covers ALL the specific content — do not omit any
item, command, tool, or step mentioned in the input. The text must be self-contained: someone reading
only the summary should understand everything the original content says, without needing to see the
original. Length: as long as needed to cover everything (typically 5-10 sentences for structured
content). Do not use bullet points — write flowing prose.

Categories: tech, programming, ai, crossfit, travel, food, business, personal, other
Tags: lowercase, max 5, specific (prefer "llm" over "ai", "react" over "javascript")"""


class Coordinator:
    def __init__(self) -> None:
        self._agent = Agent(
            model=DeepSeek(id="deepseek-reasoner"),
            tools=[
                TavilyTools(search_depth="advanced", include_answer=True),
                YouTubeTools(languages=["it", "en", "a.it", "a.en"]),
                scrape_url,
            ],
            instructions=SYSTEM_PROMPT,
            output_schema=EnrichedIdea,
        )

    async def process(self, text: str) -> EnrichedIdea:
        response = await self._agent.arun(text)
        if not isinstance(response.content, EnrichedIdea):
            raise ValueError(f"Agent returned unexpected output: {response.content!r}")
        return response.content
