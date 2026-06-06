<div align="center">

# PACE

### Precise Analysis and Compilation of Extracts

**Turn any content into structured, actionable intelligence — in seconds.**

---

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-215%20passing-00C853?style=for-the-badge&logo=pytest&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](CONTRIBUTING.md)

</div>

---

<br>

## What it does

PACE ingests content from **5 sources**, runs **10 parallel AI analyses**, and delivers a **structured report** — all in a single click.

<div align="center">

```
 ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 │  YouTube     │    │   PDF       │    │  Article    │    │  Audio      │
 │  Video       │    │  Document   │    │  (URL)      │    │  File       │
 └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
        │                   │                   │                   │
        └─────────┬─────────┴─────────┬─────────┘                   │
                  │                   │                             │
                  ▼                   ▼                             │
         ┌─────────────────────────────────────┐                    │
         │     Ingest → Clean → Chunk          │◄───────────────────┘
         └─────────────────┬───────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │    Parallel LLM Analysis (3×Batch)  │
         │    ┌─────┐ ┌─────┐ ┌─────┐         │
         │    │  A  │ │  B  │ │  C  │         │
         │    └──┬──┘ └──┬──┘ └──┬──┘         │
         │       └───────┼───────┘             │
         │               ▼                     │
         │    ┌─────────────────┐              │
         │    │  Final Synthesis │              │
         │    └────────┬────────┘              │
         └─────────────┼───────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Markdown + PDF │
              │     Report      │
              └─────────────────┘
```

</div>

---

<br>

## Features

<table>
<tr>
<td width="50%">

### 5 Input Sources

- **YouTube** — transcript extraction, no API key needed
- **PDF** — PyMuPDF4LLM + table extraction
- **Article** — trafilatura (highest F1-score extractor)
- **Audio** — faster-whisper speech-to-text (local)
- **Raw Text** — paste and go

</td>
<td width="50%">

### 10 Analysis Sections

1. Executive Summary
2. Key Takeaways
3. Detailed Analysis
4. Supporting Evidence
5. Frameworks & Models
6. Action Items
7. Risks & Limitations
8. Notable Quotes
9. Missing Important Points
10. Final Synthesis

</td>
</tr>
</table>

<table>
<tr>
<td width="33%">

### Parallel Execution

3 concurrent LLM batches cut analysis time by **~60%** vs sequential.

</td>
<td width="33%">

### Response Cache

LRU cache (50 entries, 1h TTL) — re-analyze the same content instantly.

</td>
<td width="33%">

### BYOK Support

Use your own API key from **9 providers** — Gemini, Groq, Cerebras, OpenRouter, Mistral, DeepSeek, and more.

</td>
</tr>
</table>

<table>
<tr>
<td width="33%">

### SSRF Protection

DNS resolution + IP blocking prevents server-side request forgery.

</td>
<td width="33%">

### Rate Limiting

30 LLM calls/min per session. Configurable per provider.

</td>
<td width="33%">

### Input Sanitization

50K char limit, prompt injection detection, error sanitization.

</td>
</tr>
</table>

---

<br>

## Quick Start

### 1. Install

```bash
git clone https://github.com/AshayK003/PACE.git
cd PACE
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 2. Run

```bash
streamlit run app/main.py
```

Opens at **http://localhost:8501**

### 3. Analyze

1. Select a source tab (YouTube, PDF, Article, Audio, or Text)
2. Paste a URL or drop a file
3. Click **Analyze**
4. Download as Markdown or PDF

---

<br>

## Configuration

### API Key

PACE works out of the box with a built-in free tier. To use your own key:

1. Open the **sidebar** → **LLM Settings**
2. Select a **preset** from the dropdown
3. Enter your **API key**

> Your key is stored in session state only — never persisted to disk.

### Supported Providers

| Preset | Endpoint | Model | Free Limits |
|:-------|:---------|:------|:------------|
| **Gemini 2.5 Flash** | `generativelanguage.googleapis.com` | `gemini-2.5-flash` | 250 req/day |
| **Gemini 2.5 Flash-Lite** | `generativelanguage.googleapis.com` | `gemini-2.5-flash-lite` | 1,000 req/day |
| **Groq Llama 3.3 70B** | `api.groq.com` | `llama-3.3-70b-versatile` | 1,000 req/day |
| **Cerebras** | `api.cerebras.ai` | `llama-3.3-70b-versatile` | 14,400 req/day |
| **OpenRouter (free)** | `openrouter.ai` | `deepseek/deepseek-chat-v3.1:free` | 50 req/day |
| **Mistral Small** | `api.mistral.ai` | `mistral-small-latest` | ~1B tokens/month |
| **DeepSeek V4 Flash** | `api.deepseek.com` | `deepseek-v4-flash` | 5M tokens free |

### Environment Variables

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `OPENCODE_ZEN_KEY` | No | Built-in free key | Default LLM API key |

Set via environment, `.env`, or `.streamlit/secrets.toml`.

---

<br>

## Architecture

```
app/
├── main.py                 # Streamlit entry point, tab routing
├── config.py               # API keys, constants, safe_filename()
├── security.py             # SSRF, rate limiting, input sanitization
├── ingestors/              # Content extraction (one per source)
│   ├── base.py             # Abstract base class
│   ├── youtube.py          # youtube-transcript-api
│   ├── pdf.py              # PyMuPDF4LLM + pdfplumber
│   ├── article.py          # trafilatura
│   └── audio.py            # faster-whisper (local only)
├── processors/             # Text processing
│   ├── cleaner.py          # Dedup, filler removal, URL stripping
│   └── chunker.py          # semchunk semantic chunking
├── analyzers/              # LLM pipeline
│   ├── llm_client.py       # OpenAI-compatible client + cache
│   ├── pipeline.py         # Parallel batch execution
│   ├── prompts.py          # All prompt templates
│   └── parser.py           # Batched response parser
├── output/                 # Report generation
│   ├── markdown.py         # Jinja2 → Markdown
│   ├── pdf.py              # fpdf2 → PDF
│   └── templates/          # Jinja2 templates
└── ui/                     # Streamlit components
    ├── sidebar.py          # Settings, LLM presets
    └── components.py       # Display helpers
```

### Why these libraries?

| Library | Why |
|:--------|:----|
| **Streamlit** | Zero-cost deployment via Community Cloud, multi-user built-in |
| **OpenAI SDK** | Any OpenAI-compatible provider works |
| **semchunk** | Semantic chunking without embeddings |
| **fpdf2** | Pure Python PDF, no system deps |
| **PyMuPDF4LLM** | 0.09s/page, 1GB RAM cloud-friendly |
| **trafilatura** | Highest F1-score article extractor in benchmarks |
| **tenacity** | Retry with exponential backoff |

---

<br>

## Testing

```bash
# Run all 215 tests
pytest

# Verbose
pytest -v

# Specific module
pytest tests/test_analyzers.py -v

# Coverage
pytest --cov=app
```

### Test Coverage

| Module | Tests | What's Covered |
|:-------|:------|:---------------|
| `test_analyzers.py` | 30 | Pipeline, prompts, batching, cache |
| `test_security.py` | 40 | SSRF, rate limiting, injection, file magic |
| `test_ingestors.py` | 31 | YouTube, PDF, article, audio |
| `test_output.py` | 38 | Markdown, PDF, Unicode, tables |
| `test_cleaner.py` | 20 | Filler removal, dedup, timestamps |
| `test_chunker.py` | 10 | Semantic chunking, boundaries |
| `test_config.py` | 14 | Filename utils, API key loading |
| `test_parser.py` | 9 | Batched response parsing |
| `test_integration.py` | 16 | End-to-end pipeline resilience |
| **Total** | **215** | |

---

<br>

## Deployment

### Streamlit Community Cloud (Recommended)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select repo → branch `main` → entry point `app/main.py`
4. Add secrets:
   ```
   OPENCODE_ZEN_KEY = "your-key-here"
   ```

### Local / Docker

```bash
# Local
streamlit run app/main.py

# Docker (contributions welcome)
docker build -t pace .
docker run -p 8501:8501 pace
```

---

<br>

## Troubleshooting

| Problem | Solution |
|:--------|:---------|
| **Authentication error** | Open sidebar → LLM Settings → select correct preset → enter your key |
| **PDF garbled text** | Scanned PDFs need OCR. Run locally with `opendataloader-pdf` |
| **Audio tab disabled** | `faster-whisper` requires local run. Not available on Streamlit Cloud |
| **429 Rate limit** | Wait before retrying. Response cache avoids duplicate calls |
| **Slow first request** | PDF font downloads lazily. Cache warms after first analysis |
| **SSRF blocks URL** | Only public URLs allowed. Private IPs blocked for security |

---

<br>

## Contributing

We welcome contributions! Here's how:

1. **Fork** the repo
2. **Create** a feature branch: `git checkout -b feature/my-change`
3. **Make** changes + add tests
4. **Run** `pytest` — all 215 tests must pass
5. **Open** a PR with a clear description

### Quick contributions

- **New ingestor** → Add `app/ingestors/my_source.py`, inherit `BaseIngestor`, implement `validate()` + `ingest()`
- **New analysis step** → Add prompt to `app/analyzers/prompts.py`, register in `ALL_PROMPTS`
- **New LLM preset** → Edit `presets` dict in `app/ui/sidebar.py`

---

<br>

## Security

PACE takes security seriously. See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

| Layer | Protection |
|:------|:-----------|
| **Network** | SSRF blocking (private IPs, cloud metadata, localhost) |
| **File** | Magic byte validation, 50MB size limit |
| **API** | Rate limiting (30 req/min), response caching |
| **Input** | 50K char truncation, prompt injection detection |
| **Output** | Error sanitization (no paths, no keys, no internals) |

---

<br>

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<br>

<div align="center">

**Built with care for the open-source community.**

If you find PACE useful, consider giving it a star.

[![Star](https://img.shields.io/github/stars/AshayK003/PACE?style=social)](https://github.com/AshayK003/PACE)

</div>
