# AGENTS.md — PACE Development Guide

## Project Overview
**PACE** (Precise Analysis and Compilation of Extracts) is a Streamlit app that ingests content (YouTube, PDF, article, audio, text) and produces structured AI-powered analysis reports with export to Markdown, PDF, EPUB, and Obsidian formats.

## Architecture

```
app/
├── main.py                    # Streamlit app entry, wires everything together
├── config.py                  # SourceType, MODEL_NAME, BASE_URL, safe_filename, build_export_path
├── security.py                # SSRF protection, rate limiting, input sanitization
├── analyzers/
│   ├── llm_client.py          # OpenAI-compatible client with BYOK, response cache, retries
│   ├── pipeline.py            # Sequential batch execution (A→B→C with delays)
│   ├── prompts.py             # System prompt + all analysis prompts
│   ├── parser.py              # Parses ===SECTION=== delimited LLM responses
│   └── categorizer.py         # LLM-based content categorization for export paths
├── ingestors/
│   ├── base.py                # BaseIngestor interface
│   ├── youtube.py             # YouTube transcript + oEmbed title fetch
│   ├── pdf.py                 # PDF text extraction
│   ├── article.py             # Web article extraction
│   └── audio.py               # Audio transcription (ffmpeg required)
├── processors/
│   ├── cleaner.py             # Text cleaning pipeline
│   └── chunker.py             # Text chunking for LLM context
├── output/
│   ├── markdown.py            # Jinja2-based markdown rendering
│   ├── pdf.py                 # PDF generation (lazy font loading)
│   ├── epub.py                # EPUB generation (ebooklib + mistletoe)
│   ├── obsidian.py            # Obsidian frontmatter + YAML metadata
│   └── templates/             # Jinja2 templates (report.md.j2, executive.md.j2)
└── ui/
    ├── sidebar.py             # Settings, LLM config, Export Path section
    └── components.py          # Report display, download buttons
```

## Key Conventions

### Testing
- **Run all tests:** `python -m pytest --tb=short`
- **Run specific test file:** `python -m pytest tests/test_analyzers.py -v`
- Tests use `pytest` with `unittest.mock`. No external test frameworks.
- Mock the LLM client for unit tests (never hit real API in tests).
- All tests must pass before committing.

### Code Style
- Python 3.12+ with type hints (`str | None`, `dict[str, str]`)
- No comments unless explicitly requested
- Prefer `st.session_state` for persisting state across Streamlit reruns
- Use `@retry` from tenacity for API calls with exponential backoff
- SSRF protection: always validate URLs with `is_safe_url()` before fetching

### LLM Integration
- Default provider: OpenCode Zen (`deepseek-v4-flash-free` via `https://opencode.ai/zen/v1`)
- BYOK: User can select OpenCode Zen models or use other OpenAI-compatible providers
- Response caching: LRU cache (50 entries, 1h TTL) in `ResponseCache`
- Rate limiting: 30 LLM calls/minute per session via `RateLimiter`
- Retries: 2 attempts with exponential backoff (3s-15s) on rate limit errors

### Pipeline Execution
- **Sequential batches** (not concurrent) to avoid rate limiting on free tiers
- Batch A (executive_summary, key_takeaways) → 2s delay → Batch B (detailed_analysis, supporting_evidence) → 2s delay → Batch C (frameworks, action_items, risks, notable_quotes)
- Dependent sections (missing_important, final_synthesis) run after batches with 1s delay between

### Export Formats
- **Markdown:** Jinja2 templates cached at module level
- **PDF:** Lazy font loading, `fpdf2` library
- **EPUB:** `ebooklib` + `mistletoe` for HTML rendering
- **Obsidian:** YAML frontmatter with title, date, source_type, source_url, category, tags, aliases, vault_path

### Intelligent Export Naming
- `categorize_content()` calls LLM to classify content into Domain/Sub_topic
- Fixed domains: Tech, Business, Science, Health, Education, Culture, Finance, Politics, Sports, Other
- Filename format: `{slug}.md` (no date prefix)
- Sidebar shows editable Export Path section after analysis completes

### Security
- SSRF protection blocks private/loopback/link-local/cloud-metadata IPs
- File upload validation via magic bytes (PDF, audio formats)
- Input sanitization: 50K char truncation, prompt injection detection
- Error sanitization: strips file paths, API keys, truncates to 200 chars
- Rate limiting: `RateLimiter` class tracks per-session LLM calls

### Streamlit Cloud
- Entry point: `streamlit_app.py` (root level, imports `app.main`)
- `.streamlit/config.toml` disables XSRF, enables headless mode
- Secrets via `st.secrets` or environment variables

## Running the App
```bash
streamlit run streamlit_app.py
```

## Commit Convention
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- All 252+ tests must pass before committing
- Never commit secrets, API keys, or `.env` files
