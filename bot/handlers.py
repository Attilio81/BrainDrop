import asyncio
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from bot.agents.coordinator import Coordinator
from bot.config import get_settings
from db.client import SupabaseClient
from db.models import IdeaCreate

logger = logging.getLogger(__name__)

# Module-level singletons — initialized in main.py via post_init()
coordinator: Coordinator = None  # type: ignore
db: SupabaseClient = None  # type: ignore

URL_RE = re.compile(r"^https?://\S+$")


def is_authorized(update: Update) -> bool:
    # get_settings() is lru_cache — fast after first call, safe in tests
    return update.effective_user.id == get_settings().AUTHORIZED_USER_ID


def detect_source_type(text: str) -> str:
    return "url" if URL_RE.match(text.strip()) else "text"


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "👋 BrainDrop attivo!\n\n"
        "Inviami un'idea, un link o un testo — lo salvo e arricchisco automaticamente.\n\n"
        "Comandi:\n"
        "/list — ultimi 10 elementi\n"
        "/publish_<id> — pubblica/nascondi\n"
        "/delete_<id> — elimina"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    text = update.message.text.strip()
    source_type = detect_source_type(text)

    processing_msg = await update.message.reply_text("⏳ Elaborazione in corso...")

    try:
        enriched = await asyncio.wait_for(
            coordinator.process(text),
            timeout=get_settings().AGENT_TIMEOUT_SECONDS,
        )
        idea_create = IdeaCreate(
            title=enriched.title,
            summary=enriched.summary,
            original_content=text,
            source_type=enriched.source_type,
            category=enriched.category,
            tags=enriched.tags,
            source_url=enriched.source_url,
            thumbnail_url=enriched.thumbnail_url,
        )
        saved = await db.save_idea(idea_create)
        short_id = str(saved.id)[:8]
        tags_str = " ".join(f"#{t}" for t in enriched.tags)

        reply = (
            f"✅ Salvato: {enriched.title}\n"
            f"📂 {enriched.category} | 🏷 {tags_str}\n"
            f"📝 {enriched.summary}\n"
            f"🔗 /publish_{short_id}"
        )

    except (asyncio.TimeoutError, Exception) as e:
        logger.error(f"Enrichment failed: {e}")
        saved = await db.save_raw(text, source_type)
        short_id = str(saved.id)[:8]
        reply = f"⚠️ Salvato senza arricchimento (id: {short_id}). Riprova a inviare il messaggio."

    await processing_msg.delete()
    await update.message.reply_text(reply)


async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    ideas = await db.list_ideas(limit=10)
    if not ideas:
        await update.message.reply_text("Nessun elemento salvato.")
        return

    lines = []
    for idea in ideas:
        status = "✅" if idea.published else "📤"
        short_id = str(idea.id)[:8]
        lines.append(f"{status} {idea.title} — /publish_{short_id} | /delete_{short_id}")

    await update.message.reply_text("\n".join(lines))


async def handle_publish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    text = update.message.text.strip()
    match = re.match(r"^/publish_([a-f0-9]{8})$", text)
    if not match:
        return

    short_id = match.group(1)
    try:
        idea = await db.toggle_publish(short_id)
        status = "✅ Pubblicato" if idea.published else "📤 Nascosto"
        await update.message.reply_text(f"{status}: {idea.title}")
    except Exception as e:
        logger.error(f"Publish toggle failed: {e}")
        await update.message.reply_text("❌ Errore. Riprova.")


async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    text = update.message.text.strip()
    match = re.match(r"^/delete_([a-f0-9]{8})$", text)
    if not match:
        return

    short_id = match.group(1)
    try:
        await db.soft_delete(short_id)
        await update.message.reply_text(f"🗑 Eliminato ({short_id}).")
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        await update.message.reply_text("❌ Errore. Riprova.")
