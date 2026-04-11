import asyncio
import logging
import os
import re
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from bot.agents.coordinator import Coordinator
from bot.agents.instagram import extract as extract_instagram
from bot.agents.photo import extract as extract_photo
from bot.agents.voice import transcribe as transcribe_voice
from bot.agents.youtube import extract as extract_youtube
from bot.config import get_settings
from db.client import SupabaseClient
from db.models import IdeaCreate

logger = logging.getLogger(__name__)

# Module-level singletons — initialized in main.py via post_init()
coordinator: Coordinator = None  # type: ignore
db: SupabaseClient = None  # type: ignore

URL_RE = re.compile(r"^https?://\S+$")
_INSTAGRAM_RE = re.compile(r"https?://(www\.)?instagram\.com/(p|reel)/[A-Za-z0-9_-]+")
_YOUTUBE_RE = re.compile(
    r"https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[A-Za-z0-9_\-]+"
)


def is_authorized(update: Update) -> bool:
    return update.effective_user.id == get_settings().AUTHORIZED_USER_ID


def detect_source_type(text: str) -> str:
    return "url" if URL_RE.match(text.strip()) else "text"


def is_instagram_url(text: str) -> bool:
    return bool(_INSTAGRAM_RE.match(text.strip()))


def is_youtube_url(text: str) -> bool:
    return bool(_YOUTUBE_RE.match(text.strip()))


async def _save_and_reply(
    update: Update,
    processing_msg,
    raw_text: str,
    original_text: str,
    source_type: str,
    source_url: str | None,
    thumbnail_url: str | None,
) -> None:
    """Run coordinator enrichment, save to DB, and reply. Shared by all handlers."""
    try:
        enriched = await asyncio.wait_for(
            coordinator.process(raw_text),
            timeout=get_settings().AGENT_TIMEOUT_SECONDS,
        )
        enrichment_data = {}
        if raw_text != original_text:
            enrichment_data["extracted_text"] = raw_text
        idea_create = IdeaCreate(
            title=enriched.title,
            summary=enriched.summary,
            original_content=original_text,
            source_type=source_type,
            category=enriched.category,
            tags=enriched.tags,
            source_url=source_url or enriched.source_url,
            thumbnail_url=thumbnail_url or enriched.thumbnail_url,
            enrichment_data=enrichment_data,
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
        logger.error(f"Enrichment failed ({source_type}): {e}")
        saved = await db.save_raw(original_text, source_type)
        short_id = str(saved.id)[:8]
        reply = f"⚠️ Salvato senza arricchimento (id: {short_id}). Riprova a inviare il messaggio."

    await processing_msg.delete()
    await update.message.reply_text(reply)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "👋 *BrainDrop attivo!*\n\n"
        "Mandami qualsiasi cosa da salvare:\n"
        "🔗 Link o URL\n"
        "📸 Post Instagram (carosello incluso)\n"
        "▶️ Video YouTube\n"
        "🖼 Foto\n"
        "🎙 Nota vocale\n"
        "💬 Testo libero\n\n"
        "Ogni contenuto viene arricchito con AI e salvato nella tua knowledge base.\n\n"
        "─────────────────\n"
        "📋 *Comandi*\n"
        "/list — ultimi 10 elementi salvati\n"
        "/publish\\_<id> — pubblica o nascondi\n"
        "/delete\\_<id> — elimina\n"
        "/clear — 🗑 svuota tutto il database",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    text = update.message.text.strip()
    processing_msg = await update.message.reply_text("⏳ Elaborazione in corso...")

    # Detect special media URLs and extract content
    media_result = None
    media_source_type = None

    if is_instagram_url(text):
        media_result = await extract_instagram(text)
        media_source_type = "instagram"
    elif is_youtube_url(text):
        media_result = await extract_youtube(text)
        media_source_type = "youtube"

    # Extraction attempted but failed
    if media_source_type is not None and media_result is None:
        saved = await db.save_raw(text, media_source_type)
        short_id = str(saved.id)[:8]
        await processing_msg.delete()
        await update.message.reply_text(
            f"⚠️ Impossibile estrarre il contenuto (id: {short_id}). Riprova."
        )
        return

    raw_text = media_result["text"] if media_result else text
    source_type = media_source_type or detect_source_type(text)
    source_url = media_result["source_url"] if media_result else None
    thumbnail_url = media_result["thumbnail_url"] if media_result else None

    await _save_and_reply(
        update, processing_msg, raw_text, text,
        source_type, source_url, thumbnail_url,
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    processing_msg = await update.message.reply_text("⏳ Analisi foto in corso...")

    photo = update.message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        await tg_file.download_to_drive(tmp_path)
        description = await extract_photo(tmp_path)
    finally:
        os.unlink(tmp_path)

    if description is None:
        saved = await db.save_raw("[Telegram photo]", "photo")
        short_id = str(saved.id)[:8]
        await processing_msg.delete()
        await update.message.reply_text(
            f"⚠️ Impossibile analizzare la foto (id: {short_id}). Riprova."
        )
        return

    raw_text = f"[Telegram photo]\n\n{description}"
    await _save_and_reply(
        update, processing_msg, raw_text, raw_text,
        "photo", None, None,
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    processing_msg = await update.message.reply_text("⏳ Trascrizione in corso...")

    voice = update.message.voice
    tg_file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        await tg_file.download_to_drive(tmp_path)
        transcription = await transcribe_voice(tmp_path)
    finally:
        os.unlink(tmp_path)

    if transcription is None:
        saved = await db.save_raw("[Voice note]", "voice")
        short_id = str(saved.id)[:8]
        await processing_msg.delete()
        await update.message.reply_text(
            f"⚠️ Impossibile trascrivere la nota vocale (id: {short_id}). Riprova."
        )
        return

    raw_text = f"[Voice note]\n\n{transcription}"
    await _save_and_reply(
        update, processing_msg, raw_text, raw_text,
        "voice", None, None,
    )


async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    ideas = await db.list_ideas(limit=10)
    if not ideas:
        await update.message.reply_text("Nessun elemento salvato.")
        return

    lines = []
    for idea in ideas:
        status = "✅ pubblicato" if idea.published else "📤 bozza"
        short_id = str(idea.id)[:8]
        lines.append(f"{status} — {idea.title} | /publish_{short_id} | /delete_{short_id}")

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


async def handle_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    try:
        count = await db.clear_all()
        await update.message.reply_text(f"🗑 Database svuotato ({count} elementi eliminati).")
    except Exception as e:
        logger.error(f"Clear failed: {e}")
        await update.message.reply_text("❌ Errore durante lo svuotamento. Riprova.")


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
