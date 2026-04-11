import logging

from dotenv import load_dotenv
load_dotenv()  # Export .env values into os.environ so third-party libs (Tavily, DeepSeek) can read them

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import bot.handlers as handlers
from bot.agents.coordinator import Coordinator
from bot.config import get_settings
from db.client import SupabaseClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application):
    """Initialize singletons after event loop is running."""
    settings = get_settings()
    handlers.coordinator = Coordinator()
    handlers.db = await SupabaseClient.create(
        url=settings.SUPABASE_URL,
        key=settings.SUPABASE_SERVICE_KEY.get_secret_value(),
    )
    logger.info("BrainDrop bot initialized.")


def main() -> None:
    settings = get_settings()

    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN.get_secret_value())
        .post_init(post_init)
        .build()
    )

    # Static commands
    app.add_handler(CommandHandler("start", handlers.handle_start))
    app.add_handler(CommandHandler("list", handlers.handle_list))
    app.add_handler(CommandHandler("clear", handlers.handle_clear))

    # Dynamic commands matched via regex (before generic text handler)
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^/publish_[a-f0-9]{8}$"),
            handlers.handle_publish,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^/delete_[a-f0-9]{8}$"),
            handlers.handle_delete,
        )
    )

    # Phase 2: media handlers (before generic text catch-all)
    app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handlers.handle_voice))

    # Generic text + URL messages
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message)
    )

    logger.info("Starting BrainDrop bot (polling mode)...")
    app.run_polling()


if __name__ == "__main__":
    main()
