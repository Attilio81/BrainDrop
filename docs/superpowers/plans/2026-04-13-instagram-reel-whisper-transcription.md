# Instagram Reel — Whisper Audio Transcription — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transcribe the audio of Instagram Reels with OpenAI Whisper and include the transcript in the coordinator input, so spoken lists and tips are captured in the summary and details.

**Architecture:** Add a `_transcribe_reel(video_url, api_key) -> str` function to `bot/agents/instagram.py` that downloads the video with `httpx` and sends it to OpenAI Whisper. Wire it into `_extract_sync` for the reel branch — the transcript is appended to `parts` so the coordinator receives `"Caption: ...\n\nTranscript: ..."`. No changes to coordinator, handlers, or DB schema.

**Tech Stack:** `httpx` (already in use), `tempfile` (stdlib, already imported), OpenAI Whisper API (`POST /v1/audio/transcriptions`), `pytest` + `unittest.mock`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `bot/agents/instagram.py` | Modify | Add `_transcribe_reel`, wire into `_extract_sync` reel branch |
| `tests/test_instagram.py` | Modify | Add tests for `_transcribe_reel` and reel extraction with transcript |

---

### Task 1: Add `_transcribe_reel` and tests

**Files:**
- Modify: `bot/agents/instagram.py` (after line 54, before `_extract_sync`)
- Modify: `tests/test_instagram.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_instagram.py`:

```python
def test_transcribe_reel_returns_text_on_success(mock_settings):
    from bot.agents.instagram import _transcribe_reel

    mock_download_resp = MagicMock()
    mock_download_resp.raise_for_status = MagicMock()
    mock_download_resp.content = b"fake-mp4-bytes"

    mock_whisper_resp = MagicMock()
    mock_whisper_resp.raise_for_status = MagicMock()
    mock_whisper_resp.json = MagicMock(return_value={"text": "First tip. Second tip."})

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get = MagicMock(return_value=mock_download_resp)
    mock_client.post = MagicMock(return_value=mock_whisper_resp)

    with patch("bot.agents.instagram.httpx.Client", return_value=mock_client):
        result = _transcribe_reel("https://cdn.instagram.com/reel.mp4", "fake-key")

    assert result == "First tip. Second tip."


def test_transcribe_reel_returns_empty_on_download_error(mock_settings):
    from bot.agents.instagram import _transcribe_reel

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get = MagicMock(side_effect=Exception("connection error"))

    with patch("bot.agents.instagram.httpx.Client", return_value=mock_client):
        result = _transcribe_reel("https://cdn.instagram.com/reel.mp4", "fake-key")

    assert result == ""


def test_transcribe_reel_returns_empty_on_whisper_error(mock_settings):
    from bot.agents.instagram import _transcribe_reel

    mock_download_resp = MagicMock()
    mock_download_resp.raise_for_status = MagicMock()
    mock_download_resp.content = b"fake-mp4-bytes"

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get = MagicMock(return_value=mock_download_resp)
    mock_client.post = MagicMock(side_effect=Exception("whisper error"))

    with patch("bot.agents.instagram.httpx.Client", return_value=mock_client):
        result = _transcribe_reel("https://cdn.instagram.com/reel.mp4", "fake-key")

    assert result == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_instagram.py::test_transcribe_reel_returns_text_on_success tests/test_instagram.py::test_transcribe_reel_returns_empty_on_download_error tests/test_instagram.py::test_transcribe_reel_returns_empty_on_whisper_error -v
```

Expected: FAIL with `ImportError: cannot import name '_transcribe_reel'`

- [ ] **Step 3: Implement `_transcribe_reel` in `bot/agents/instagram.py`**

Add this function after `_ocr_image` (after line 54), before `_extract_sync`:

```python
def _transcribe_reel(video_url: str, api_key: str) -> str:
    """Download a reel video and transcribe its audio with Whisper.

    Returns transcript text, or empty string on any failure.
    """
    try:
        with httpx.Client(timeout=60) as client:
            r = client.get(video_url)
            r.raise_for_status()
            video_bytes = r.content

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(video_bytes)
            tmp_path = Path(f.name)

        try:
            with httpx.Client(timeout=120) as client:
                with tmp_path.open("rb") as audio_file:
                    resp = client.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        data={"model": "whisper-1"},
                        files={"file": ("reel.mp4", audio_file, "video/mp4")},
                    )
                resp.raise_for_status()
                return resp.json().get("text", "").strip()
        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        logger.warning(f"Whisper transcription failed for reel: {e}")
        return ""
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_instagram.py::test_transcribe_reel_returns_text_on_success tests/test_instagram.py::test_transcribe_reel_returns_empty_on_download_error tests/test_instagram.py::test_transcribe_reel_returns_empty_on_whisper_error -v
```

Expected: all 3 PASS

- [ ] **Step 5: Commit**

```bash
git add bot/agents/instagram.py tests/test_instagram.py
git commit -m "feat: add _transcribe_reel with Whisper API"
```

---

### Task 2: Wire transcript into reel extraction

**Files:**
- Modify: `bot/agents/instagram.py` (lines 81–127, `_extract_sync`)
- Modify: `tests/test_instagram.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_instagram.py`:

```python
async def test_extract_reel_includes_transcript(mock_settings):
    from bot.agents.instagram import extract

    mock_post = MagicMock()
    mock_post.caption = "Watch this!"
    mock_post.url = "https://cdn.instagram.com/thumb.jpg"
    mock_post.video_url = "https://cdn.instagram.com/reel.mp4"
    mock_post.typename = "GraphVideo"
    mock_post.is_video = True

    with patch("bot.agents.instagram.instaloader.Post.from_shortcode", return_value=mock_post), \
         patch("bot.agents.instagram._transcribe_reel", return_value="Tip 1. Tip 2. Tip 3."):
        result = await extract("https://www.instagram.com/reel/ABC123xyz/")

    assert result is not None
    assert "Caption: Watch this!" in result["text"]
    assert "Transcript:" in result["text"]
    assert "Tip 1. Tip 2. Tip 3." in result["text"]


async def test_extract_reel_falls_back_to_caption_when_transcript_empty(mock_settings):
    from bot.agents.instagram import extract

    mock_post = MagicMock()
    mock_post.caption = "Watch this!"
    mock_post.url = "https://cdn.instagram.com/thumb.jpg"
    mock_post.video_url = "https://cdn.instagram.com/reel.mp4"
    mock_post.typename = "GraphVideo"
    mock_post.is_video = True

    with patch("bot.agents.instagram.instaloader.Post.from_shortcode", return_value=mock_post), \
         patch("bot.agents.instagram._transcribe_reel", return_value=""):
        result = await extract("https://www.instagram.com/reel/ABC123xyz/")

    assert result is not None
    assert "Caption: Watch this!" in result["text"]
    assert "Transcript:" not in result["text"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_instagram.py::test_extract_reel_includes_transcript tests/test_instagram.py::test_extract_reel_falls_back_to_caption_when_transcript_empty -v
```

Expected: FAIL — `_transcribe_reel` not called yet in extraction flow

- [ ] **Step 3: Wire transcript into `_extract_sync`**

In `bot/agents/instagram.py`, modify `_extract_sync`:

**Before** (lines 81–83, 96–97):
```python
    caption = post.caption or ""
    thumbnail_url = post.url
    slide_texts: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        if post.typename == "GraphSidecar":
            image_urls = [
                node.display_url
                for node in post.get_sidecar_nodes()
                if not node.is_video
            ]
        elif not post.is_video:
            image_urls = [post.url]
        else:
            image_urls = []  # Reel — no images, use caption only
```

**After:**
```python
    caption = post.caption or ""
    thumbnail_url = post.url
    slide_texts: list[str] = []
    transcript: str = ""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        if post.typename == "GraphSidecar":
            image_urls = [
                node.display_url
                for node in post.get_sidecar_nodes()
                if not node.is_video
            ]
        elif not post.is_video:
            image_urls = [post.url]
        else:
            image_urls = []  # Reel — no images
            transcript = _transcribe_reel(post.video_url, api_key)
```

Also update the `parts` assembly block at the bottom of `_extract_sync`.

**Before** (lines 114–121):
```python
    parts: list[str] = []
    if caption:
        parts.append(f"Caption: {caption}")
    parts.extend(slide_texts)

    if not parts:
        logger.warning(f"No content extracted from {shortcode}")
        return None
```

**After:**
```python
    parts: list[str] = []
    if caption:
        parts.append(f"Caption: {caption}")
    parts.extend(slide_texts)
    if transcript:
        parts.append(f"Transcript:\n{transcript}")

    if not parts:
        logger.warning(f"No content extracted from {shortcode}")
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_instagram.py::test_extract_reel_includes_transcript tests/test_instagram.py::test_extract_reel_falls_back_to_caption_when_transcript_empty -v
```

Expected: both PASS

- [ ] **Step 5: Run the full test suite**

```bash
pytest tests/test_instagram.py -v
```

Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add bot/agents/instagram.py tests/test_instagram.py
git commit -m "feat: transcribe Instagram Reel audio with Whisper and include in summary"
```

---

## Notes

- `post.video_url` is a standard instaloader property on video posts — no extra download config needed (the `Instaloader` object's `download_videos=False` only affects the `download_post()` method, not the `.video_url` property).
- The Whisper API timeout is set to 120s — reels are short, but the upload can be slow on a connection.
- If the reel has no caption and transcription fails, `parts` is empty → `return None` → bot falls back to saving raw text (existing behaviour in `handlers.py`).
