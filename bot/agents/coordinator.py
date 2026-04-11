from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.tools.tavily import TavilyTools

from bot.agents.tools import scrape_url
from db.models import EnrichedIdea

SYSTEM_PROMPT = """You are a personal knowledge assistant. You receive raw text or URLs
and produce structured knowledge entries.

For each input:
1. If it's a URL, use the scrape_url tool to extract its content, then search Tavily for additional context.
2. If it's plain text, search Tavily to find what it refers to and enrich it.
3. Produce a concise English title (max 10 words), a summary IN ITALIAN, a category from the
   allowed list, and up to 5 lowercase tags.
4. Set source_type to "url" if the input was a URL (starts with http:// or https://), or "text" if it was plain text.

Summary guidelines (IN ITALIAN):
- For simple content (article, idea, quote): 2-3 sentences explaining what it is and why it's interesting.
- For structured content (lists, tools, commands, steps, carousels): start with 1 sentence of context,
  then list the key items as a bullet list (- item: description). Include all specific names, commands,
  or steps — do not omit them. End with 1 sentence on why it's useful.

Categories: tech, programming, ai, crossfit, travel, food, business, personal, other
Tags: lowercase, max 5, specific (prefer "llm" over "ai", "react" over "javascript")"""


class Coordinator:
    def __init__(self) -> None:
        self._agent = Agent(
            model=DeepSeek(id="deepseek-reasoner"),
            tools=[
                TavilyTools(search_depth="advanced", include_answer=True),
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
