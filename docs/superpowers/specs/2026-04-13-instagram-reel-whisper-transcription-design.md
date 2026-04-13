# Instagram Reel — Whisper Audio Transcription

**Date:** 2026-04-13  
**Status:** Approved

## Problem

When a user sends an Instagram Reel URL, the bot extracts only the post caption. If the reel author verbally lists useful items (tools, tips, steps, etc.), that content is lost — it never reaches the summary or details fields.

## Goal

Transcribe the audio of Instagram Reels with OpenAI Whisper and include the transcript in the pre-extracted text, so the coordinator agent can surface the spoken content in the summary and details.

## Scope

Single file change: `bot/agents/instagram.py`

No changes to: coordinator, handlers, prompt, DB schema, or output model.

## Architecture

### Current flow (reels)

```
extract_instagram(url)
  → instaloader fetches post metadata
  → post.is_video == True → skip media extraction
  → returns {"text": "Caption: {caption}", "source_url": ..., "thumbnail_url": ...}
```

### New flow (reels)

```
extract_instagram(url)
  → instaloader fetches post metadata
  → post.is_video == True
      → download video to tempfile (.mp4)
      → openai.audio.transcriptions.create(model="whisper-1", file=mp4_file)
      → transcript = transcription result text
      → delete tempfile (finally block)
  → returns {"text": "Caption: {caption}\n\nTranscript: {transcript}", ...}
```

### Coordinator impact

The coordinator already has a rule for pre-extracted content:

> If text starts with "Caption:", "Slide", "[Telegram photo]", or "[Voice note]" — work directly with provided text; do NOT call tools.

Adding `\n\nTranscript: ...` to the existing "Caption: ..." string stays within this rule. No prompt change needed.

## Implementation Details

**File:** `bot/agents/instagram.py`

**New function:** `_transcribe_reel(post) -> str`
- Downloads the video URL from `post.video_url` using `requests` (already available or add)
- Writes to a `tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)`
- Calls `openai.audio.transcriptions.create(model="whisper-1", file=open(path, "rb"))`
- Deletes the temp file in a `finally` block
- Returns transcript text, or `""` on failure (logged as warning)

**Modification:** Inside the `is_video` branch of `extract_instagram()`:
- Call `_transcribe_reel(post)`
- If transcript is non-empty, append `\n\nTranscript: {transcript}` to the text

**OpenAI client:** Already instantiated in the file for OCR (`gpt-4o-mini`). Reuse same client for Whisper.

## Error Handling

- If video download fails: log warning, fall back to caption-only (current behavior)
- If Whisper API fails: log warning, fall back to caption-only
- Never raise — the coordinator must always receive something

## Dependencies

- `openai` — already installed
- `requests` — for downloading the video file (or use `urllib`)
- `tempfile` — stdlib, no install needed

## Out of Scope

- Carousel posts with video slides (rare edge case, not requested)
- YouTube (already handled via YouTubeTranscriptApi)
- Other video platforms
