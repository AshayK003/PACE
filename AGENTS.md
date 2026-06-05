# PACE — Agent Context File

## Project Overview

PACE (Precise Analysis and Compilation of Extracts) is an advanced AI analysis and summarization system that transforms raw, unstructured information from long-form content into organized, actionable summaries.

**Live URL:** Streamlit Community Cloud (once deployed)
**GitHub:** https://github.com/AshayK003/PACE

---

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | Streamlit (Python) | Zero deployment cost via Community Cloud, rapid prototyping, multi-user |
| **LLM** | DeepSeek V4 Flash Free (via OpenCode Zen API) | Free, 200K context, OpenAI-compatible |
| **YouTube transcripts** | `youtube-transcript-api` | No API key needed, fast |
| **YouTube audio (local only)** | `yt-dlp` → `faster-whisper` | For videos without transcripts (requires ffmpeg, not available on Community Cloud) |
| **PDF parsing (cloud)** | `PyMuPDF4LLM` + `pdfplumber` (tables) | Fits 1GB RAM, fast 0.09s/page, zero-config OCR. AGPL-3.0. Table supplement fixes weak extraction. |
| **PDF parsing (local)** | `OpenDataLoader` (primary) + `pypdf` (fallback) | #1 benchmark accuracy 0.907, Apache-2.0, no GPU, requires Java 11 |
| **Web articles** | `trafilatura` | Best open-source article extraction, JSON metadata output |
| **Audio transcription** | `faster-whisper` | 4x faster than OpenAI Whisper, CPU-compatible |
| **Semantic chunking** | `semchunk` | 15% better RAG performance, used by Microsoft Intel Toolkit |
| **LLM orchestration** | `openai` SDK (direct calls) | DeepSeek is OpenAI-compatible. Keeping it simple — no LangChain/LlamaIndex overhead |
| **Markdown output** | `jinja2` templates | Clean, extensible report generation |
| **PDF output** | `fpdf2` + `mistletoe` | Pure Python, MD→HTML→PDF, zero system dependencies |
| **Quality guardrails** | `guardrails-ai` | Hallucination detection, format validation |
| **Storage** | None (ephemeral) | No database — each analysis is a fresh session |
| **Deployment** | Streamlit Community Cloud | Free tier, Debian Linux, 1GB RAM limit |

---

## Project Structure

```
pace/
├── app/
│   ├── main.py                    # Streamlit entry point
│   ├── config.py                  # Settings, API keys, constants
│   ├── pages/                     # Streamlit multipage app
│   │   ├── 1_🔗_youtube.py
│   │   ├── 2_📄_pdf.py
│   │   ├── 3_🌐_article.py
│   │   ├── 4_🎙️_audio.py
│   │   └── 5_📝_text.py
│   ├── ingestors/                 # Content extraction layer
│   │   ├── base.py                # Abstract base class
│   │   ├── youtube.py
│   │   ├── pdf.py
│   │   ├── article.py
│   │   └── audio.py
│   ├── processors/                # Text processing
│   │   ├── chunker.py             # semchunk wrapper
│   │   └── cleaner.py             # Dedup, filler removal
│   ├── analyzers/                 # LLM analysis pipeline
│   │   ├── pipeline.py            # Orchestrator
│   │   ├── prompts.py             # All prompt templates
│   │   └── llm_client.py          # DeepSeek V4 Flash Free client
│   ├── output/                    # Report generation
│   │   ├── markdown.py            # Jinja2 → MD
│   │   ├── pdf.py                 # fpdf2 → PDF
│   │   └── templates/
│   │       ├── report.md.j2       # Full report
│   │       └── executive.md.j2    # Summary only
│   └── ui/                        # Streamlit UI components
│       ├── components.py
│       ├── progress.py            # Pipeline progress tracker
│       └── sidebar.py
├── tests/
│   ├── test_ingestors.py
│   ├── test_chunker.py
│   ├── test_analyzers.py
│   └── test_output.py
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── packages.txt
├── AGENTS.md
├── README.md
└── .gitignore
```

---

## Architecture & Data Flow

```
User Input (URL / File / Text)
    │
    ├─ YouTube URL
    │   ├─ youtube-transcript-api.list() → find best language
    │   └─ youtube-transcript-api.fetch(video_id, languages=[en, hi, ...])
    │
    ├─ PDF File
    │   └─ PyMuPDF4LLM.to_markdown() + pdfplumber (tables) + pypdf (fallback)
    │
    ├─ Article URL
    │   └─ trafilatura.extract() → clean text + JSON metadata
    │
    ├─ Audio File
    │   └─ faster-whisper.transcribe() (local only; cloud fallback message)
    │
    └─ Raw Text ──→ Used directly
    │
    ▼
[Optional] LLM Translation (if non-English detected via metadata)
    │
    ▼
clean_pipeline() → remove fillers, dedup, timestamps, URLs
    │
    ▼
semchunk.chunk() → semantic chunks (word-count tokenizer, configurable overlap)
    │
    ▼
LLM Pipeline (10 sequential steps, DeepSeek V4 Flash Free via OpenAI SDK)
    ├─ Executive Summary
    ├─ Key Takeaways
    ├─ Detailed Analysis
    ├─ Supporting Evidence
    ├─ Frameworks & Models
    ├─ Action Items
    ├─ Risks & Limitations
    ├─ Notable Quotes
    ├─ Missing But Important
    └─ Final Synthesis (receives previous results as context)
    │
    ▼
Jinja2 Template → Markdown report (.md)
    │
    ▼
mistletoe (MD→HTML) → fpdf2 + DejaVu Sans → PDF report (.pdf)
    │
    ▼
Streamlit UI → Display + Download buttons (MD + PDF)
```

---

## Key Constraints

1. **Streamlit Community Cloud** — 1GB RAM, no background workers, limited system deps. All audio transcoding (yt-dlp, faster-whisper) disabled on cloud. Falls back to: "This video has no transcript. Transcribe audio locally."
2. **Ephemeral** — No database. All state is in-memory per user session.
3. **Zero cost** — LLM is free (DeepSeek V4 Flash Free via OpenCode Zen). Hosting is free (Streamlit Community Cloud). No API keys needed except OpenCode Zen.
4. **Multi-user** — Single container, shared by all users via threads.

---

## LLM Configuration

```python
client = OpenAI(
    api_key=st.secrets["OPENCODE_ZEN_KEY"],
    base_url="https://opencode.ai/zen/v1",
)
model = "deepseek-v4-flash-free"
# 200K context, free, OpenAI-compatible
```

Users can also enter their own API key via the sidebar (LLM Settings → API Key), which overrides the default. The key is stored only in session state and never persisted.

---

## Output Sections (from requirements)

1. **Executive Summary** — Concise overview
2. **Key Takeaways** — Highest-priority insights
3. **Detailed Analysis** — Structured breakdown by topic
4. **Supporting Evidence** — Examples, stats, reasoning
5. **Frameworks & Models** — Methodologies, mental models
6. **Action Items** — Practical recommendations
7. **Risks & Limitations** — Caveats, trade-offs
8. **Notable Quotes** — High-impact quotations
9. **Missing But Important** — What the source didn't address
10. **Final Synthesis** — Ultimate message + implications

---

## Pipeline Robustness

| Layer | Safeguard |
|-------|-----------|
| **Content length** | Auto-truncated at 50K chars with `[Content truncated]` note |
| **Empty LLM result** | Retried once automatically per step |
| **Rate limiting** | 0.3s delay between sequential LLM calls |
| **Step failure** | Per-step try/except with `[Analysis failed for {step}: {error}]` message — rest continues |
| **PDF Unicode** | DejaVu Sans font (regular, bold, italic, bold-italic) covers all Unicode BMP — auto-downloaded from GitHub release, cached locally |
| **Translation** | Non-English YouTube transcripts → chunked LLM translation to English with per-chunk fallback |
| **API Key** | Sidebar input overrides default key; stored only in session state |
| **Theme** | Dark mode via `.streamlit/config.toml` `[theme] base = "dark"` |

---

## Research-Backed Decisions

| Decision | Evidence | Source |
|----------|----------|--------|
| Direct SDK over LangChain/LlamaIndex | 20% lower latency, 50% less memory, no abstraction tax for linear pipelines | Toolhalla RAG Framework Comparison 2026 |
| fpdf2 for PDF output | Only pure-Python option without system deps; confirmed working on Streamlit Cloud | fpdf2 official docs, Streamlit community |
| PyMuPDF4LLM for cloud PDF | Only high-accuracy parser fitting 1GB RAM; 0.09s/page, AGPL-3.0 | OpenDataLoader Benchmark |
| faster-whisper over alternatives | 4-6x faster than Whisper, identical WER, CPU-compatible, pip-installable | HF Open ASR Leaderboard |
| semchunk for chunking | No embedding model needed, production-proven in Microsoft Intel Toolkit | semchunk GitHub |
| trafilatura for articles | #1 F1 score (0.958) across all open-source extractors | ScrapingHub Article Extraction Benchmark |
| youtube-transcript-api | Only option with no API key, no headless browser, actively maintained | jdepoix/youtube-transcript-api |

---

## Processing Philosophy

- Signal over noise
- Importance over chronology
- Information density over verbosity
- Clarity over complexity
- Evidence over assertion
- Analysis over simple summarization

---

## Key Dependencies

```txt
# Core
streamlit>=1.40.0
openai>=2.0.0

# Content Ingestion
youtube-transcript-api>=1.0.0
trafilatura>=2.0.0
pymupdf4llm>=0.2.0         # Cloud PDF parsing (AGPL-3.0)
pdfplumber>=0.11.0          # Table supplement
pypdf>=5.0.0                # Fallback PDF parser

# Local only (not on Streamlit Cloud)
opendataloader-pdf>=0.1.0   # Local PDF parsing, requires Java 11
yt-dlp>=2026.1.0            # YouTube audio download
faster-whisper>=1.0.0       # Audio transcription

# Text Processing
semchunk>=4.0.0

# Output
jinja2>=3.1.0
fpdf2>=2.8.0
mistletoe>=1.0.0

# Quality
guardrails-ai>=0.6.0

# Utilities
tenacity>=9.0.0             # Retry logic
tiktoken>=0.8.0             # Token counting
```

---

## Git Remote

```
git remote add origin https://github.com/AshayK003/PACE.git
git branch -M main
git push -u origin main
```
