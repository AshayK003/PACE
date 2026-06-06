# PACE

**Precise Analysis and Compilation of Extracts** — an AI analysis engine that turns long-form content (YouTube videos, PDFs, articles, audio, raw text) into structured, actionable reports.

Paste a URL or drop a file. Get a 10-section analysis in seconds.

```
YouTube / PDF / Article / Audio / Text
    ↓
Ingestion → Cleaning → Chunking → Parallel LLM Analysis → Report
    ↓
Markdown + PDF output
```

---

## Architecture

```
app/
├── main.py                 # Streamlit entry point, tab routing
├── config.py               # API keys, constants, safe_filename()
├── security.py             # SSRF protection, rate limiting, input sanitization
├── ingestors/              # Content extraction (one per source type)
│   ├── base.py             # Abstract base class
│   ├── youtube.py          # youtube-transcript-api
│   ├── pdf.py              # PyMuPDF4LLM + pdfplumber (tables)
│   ├── article.py          # trafilatura
│   └── audio.py            # faster-whisper (local only)
├── processors/             # Text processing
│   ├── cleaner.py          # Dedup, filler removal, URL stripping
│   └── chunker.py          # semchunk semantic chunking
├── analyzers/              # LLM pipeline
│   ├── llm_client.py       # OpenAI-compatible client + response cache
│   ├── pipeline.py         # Parallel batch execution (3 batches + 2 serial)
│   ├── prompts.py          # All prompt templates
│   └── parser.py           # Batched response parser
├── output/                 # Report generation
│   ├── markdown.py         # Jinja2 → Markdown
│   ├── pdf.py              # fpdf2 → PDF (DejaVu Sans for Unicode)
│   └── templates/          # Jinja2 templates
└── ui/                     # Streamlit components
    ├── sidebar.py          # Settings, LLM presets
    └── components.py       # Display helpers
```

### Why parallel batches?

The 10 analysis steps split into 3 independent batches (A, B, C) that run concurrently via `ThreadPoolExecutor(max_workers=3)`. Steps 9-10 (missing_important, final_synthesis) depend on all prior results and run serially. This cuts wall-clock time by ~60% vs sequential execution.

### Why these libraries?

| Choice | Why |
|---|---|
| Streamlit | Zero deployment cost via Community Cloud, multi-user built-in |
| OpenAI SDK | Any OpenAI-compatible provider works (Gemini, Groq, DeepSeek, etc.) |
| semchunk | Semantic chunking without an embedding model — production-proven |
| fpdf2 | Pure Python PDF output, no system dependencies |
| PyMuPDF4LLM | Fastest cloud-friendly PDF parser (0.09s/page, 1GB RAM) |
| trafilatura | Highest F1-score article extractor in benchmarks |
| tenacity | Retry with exponential backoff, no custom retry code |

---

## Setup

### Prerequisites

- Python 3.12+
- `ffmpeg` (only for local audio transcription)
- Java 11+ (only for `opendataloader-pdf`, local PDF fallback)

### Install

```bash
git clone https://github.com/AshayK003/PACE.git
cd PACE
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Run

```bash
streamlit run app/main.py
```

Opens at `http://localhost:8501`.

---

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENCODE_ZEN_KEY` | No | Built-in free key | Default LLM API key. Overridden by sidebar input. |

Set via environment, `.env` file, or Streamlit secrets (`.streamlit/secrets.toml`).

**Using your own API key**: Open the sidebar → LLM Settings → select a preset (e.g., "Gemini 2.5 Flash") → enter your API key. The key is stored only in session state — never persisted to disk.

### Supported presets

| Preset | Base URL | Model | Free Limits |
|---|---|---|---|
| Default (OpenCode Zen) | Built-in | `deepseek-v4-flash-free` | Built-in free tier |
| Gemini 2.5 Flash | `generativelanguage.googleapis.com` | `gemini-2.5-flash` | 250 req/day |
| Gemini 2.5 Flash-Lite | `generativelanguage.googleapis.com` | `gemini-2.5-flash-lite` | 1,000 req/day |
| Groq Llama 3.3 70B | `api.groq.com` | `llama-3.3-70b-versatile` | 1,000 req/day |
| Cerebras | `api.cerebras.ai` | `llama-3.3-70b-versatile` | 14,400 req/day |
| OpenRouter (free) | `openrouter.ai` | `deepseek/deepseek-chat-v3.1:free` | 50 req/day |
| Mistral Small | `api.mistral.ai` | `mistral-small-latest` | ~1B tokens/month |
| DeepSeek V4 Flash | `api.deepseek.com` | `deepseek-v4-flash` | 5M tokens free |

---

## Local Development

### Project structure for contributors

```
pace/
├── app/                    # Source code
│   ├── main.py
│   ├── config.py
│   ├── security.py
│   ├── ingestors/
│   ├── processors/
│   ├── analyzers/
│   ├── output/
│   └── ui/
├── tests/                  # 215 tests
│   ├── conftest.py         # Shared fixtures, mock LLM
│   ├── test_analyzers.py   # Pipeline, prompts, batching, cache
│   ├── test_security.py    # SSRF, rate limiting, injection detection
│   ├── test_ingestors.py   # All ingestor logic
│   ├── test_output.py      # Markdown + PDF rendering
│   └── ...
├── requirements.txt
├── packages.txt            # System deps for Streamlit Cloud (ffmpeg)
└── .streamlit/config.toml  # Theme, upload limits, security flags
```

### Code conventions

- **No comments unless asked.** Code should be self-documenting.
- **Type hints on all public functions.**
- **Tests for every feature.** Run `pytest` before pushing.
- **`str.replace()` over `str.format()`** for prompt templating — content with `{` or `}` would crash `.format()`.
- **One LLMClient instance per session** — avoids re-initializing the HTTP client.

### Key invariants

| Invariant | Where enforced |
|---|---|
| Content truncated at 50K chars | `pipeline.py:_truncate_if_needed()` |
| Max 30 LLM calls/min per session | `security.py:RateLimiter` |
| Files validated by magic bytes, not extension | `security.py:validate_file_magic()` |
| SSRF blocks private/loopback/cloud-metadata IPs | `security.py:validate_url_safe()` |
| Prompt injection detected and warned (not blocked) | `security.py:detect_prompt_injection()` |
| Error messages sanitized (no paths, no keys) | `security.py:sanitize_error_message()` |
| Response cache: LRU, 50 entries, 1h TTL | `llm_client.py:ResponseCache` |

---

## Testing

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Run specific module
pytest tests/test_analyzers.py -v

# Run with coverage
pytest --cov=app
```

### Test structure

| File | Tests | Covers |
|---|---|---|
| `test_analyzers.py` | 30 | LLM client, prompts, pipeline, batching, cache |
| `test_security.py` | 40 | SSRF, rate limiting, injection, file magic, error sanitization |
| `test_ingestors.py` | 31 | YouTube, PDF, article, audio, base ingestor |
| `test_output.py` | 38 | Markdown rendering, PDF generation, Unicode, tables |
| `test_cleaner.py` | 20 | Filler removal, dedup, timestamps, Unicode |
| `test_chunker.py` | 10 | Semantic chunking, boundaries, token limits |
| `test_config.py` | 14 | safe_filename, API key loading, source types |
| `test_parser.py` | 9 | Batched response parsing |
| `test_integration.py` | 16 | End-to-end pipeline, resilience, boundaries |
| **Total** | **215** | |

### What the mocks do

`conftest.py` patches `LLMClient._client` with a MagicMock that returns predefined section-delimited responses. The pipeline tests verify that batches route correctly based on instruction text unique to each batch.

---

## Deployment

### Streamlit Community Cloud (recommended)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select repo, branch `main`, entry point `app/main.py`
4. Add secrets in the dashboard:
   ```
   OPENCODE_ZEN_KEY = "your-key-here"
   ```

**Constraints**: 1GB RAM, no background workers, limited system deps. Audio transcription (`faster-whisper`, `yt-dlp`) is disabled on cloud — the app shows a fallback message.

### packages.txt

Streamlit Cloud reads `packages.txt` for system-level dependencies. Currently contains only `ffmpeg` for audio support.

### .streamlit/config.toml

```toml
[theme]
base = "dark"
primaryColor = "#4da6ff"

[server]
maxUploadSize = 50        # MB
enableXsrfProtection = true
headless = true

[browser]
gatherUsageStats = false

[runner]
magicEnabled = false      # Security: disable Streamlit magic
```

### Docker (for local/containerized deployment)

Not yet provided. Contributions welcome.

---

## Troubleshooting

### "Authentication error" or `[Analysis failed]`

Your API key is being sent to the wrong endpoint. Open the sidebar → LLM Settings → select the correct preset for your provider. If using a custom key, fill in Base URL, Model, and API Key fields.

### PDF analysis returns garbled text

Streamlit Cloud uses PyMuPDF4LLM which handles most PDFs well. Scanned PDFs (images) need OCR — not supported on cloud. Use locally with `opendataloader-pdf` for better accuracy.

### Audio tab says "Audio transcription is only available locally"

`faster-whisper` requires `ffmpeg` and is not available on Streamlit Cloud. Run locally to use audio analysis.

### Rate limit errors (429)

The app enforces 30 LLM calls/min per session. If your provider has lower limits (e.g., Gemini free: 10 RPM), wait before retrying. The response cache avoids duplicate calls for the same content.

### Slow first request

Font download for PDF generation happens lazily on first PDF render. Subsequent requests use the cached font. LLM response cache warms up after the first analysis.

### SSRF blocks my URL

The app blocks private IPs (10.x, 192.168.x, 127.0.0.1), link-local addresses, and cloud metadata endpoints (169.254.169.254). This is intentional — it prevents server-side request forgery. Use only public URLs.

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-change`
3. Make changes, add tests
4. Run `pytest` — all 215 tests must pass
5. Open a PR with a clear description of what changed and why

### Adding a new ingestor

1. Create `app/ingestors/my_source.py` inheriting from `BaseIngestor`
2. Implement `validate()` and `ingest()`
3. Add `SourceType.MY_SOURCE` to `config.py`
4. Add a tab in `main.py`
5. Write tests in `tests/test_ingestors.py`

### Adding a new analysis step

1. Add prompt template to `app/analyzers/prompts.py`
2. Register in `ALL_PROMPTS` dict
3. The pipeline auto-picks it up. If it's independent, add it to a batch. If it depends on prior results, add to `_DEPENDENT_SECTIONS`.
4. Update the output template in `app/output/templates/`

### Adding a new LLM preset

Edit the `presets` dict in `app/ui/sidebar.py`. Each entry is `("base_url", "model")`.

---

## License

Not yet specified. Add a `LICENSE` file before publishing.

---

## Acknowledgments

Built on top of: Streamlit, OpenAI SDK, youtube-transcript-api, trafilatura, PyMuPDF4LLM, pdfplumber, semchunk, fpdf2, mistletoe, tenacity.
