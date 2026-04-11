from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.tools.tavily import TavilyTools

from bot.agents.tools import scrape_url
from bot.config import get_settings
from db.models import EnrichedIdea

SYSTEM_PROMPT = """You are a personal knowledge assistant. You receive raw text or URLs
and produce structured knowledge entries.

For each input:
1. If it's a URL, use the scrape_url tool to extract its content, then search Tavily for additional context.
2. If it's plain text, search Tavily to find what it refers to and enrich it.
3. Produce a concise English title (max 10 words), a 2-3 sentence English summary explaining
   what it is and why it's interesting, a category from the allowed list, and up to 5 lowercase tags.

Categories: tech, programming, ai, crossfit, travel, food, business, personal, other
Tags: lowercase, max 5, specific (prefer "llm" over "ai", "react" over "javascript")"""


class Coordinator:
    def __init__(self) -> None:
        settings = get_settings()
        self._agent = Agent(
            model=DeepSeek(id="deepseek-reasoner"),
            tools=[
                TavilyTools(search_depth="advanced", include_answer=True),
                scrape_url,
            ],
            instructions=SYSTEM_PROMPT,
            output_model=EnrichedIdea,
        )

    async def process(self, text: str) -> EnrichedIdea:
        response = await self._agent.arun(text)
        return response.content
