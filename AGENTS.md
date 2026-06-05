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
| **PDF parsing** | `OpenDataLoader` (primary) + `pypdf` (fallback) | #1 benchmark accuracy 0.907, Apache-2.0, no GPU required |
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
    │   ├─ youtube-transcript-api.fetch()
    │   └─ if no transcript: yt-dlp (audio) → faster-whisper (local only)
    │
    ├─ PDF File
    │   └─ OpenDataLoader.convert() → structured JSON/Markdown
    │
    ├─ Article URL
    │   └─ trafilatura.extract() → clean text + metadata
    │
    ├─ Audio File
    │   └─ faster-whisper.transcribe()
    │
    └─ Raw Text
        └─ Used directly
    │
    ▼
Clean Text → semchunk.chunk() → semantic chunks
    │
    ▼
LLM Pipeline (sequential analysis via openai SDK + DeepSeek V4 Flash Free)
    ├─ Executive Summary
    ├─ Key Takeaways
    ├─ Detailed Analysis
    ├─ Frameworks & Models
    ├─ Action Items
    ├─ Risks & Limitations
    ├─ Notable Quotes
    └─ Final Synthesis
    │
    ▼
Guardrails AI → validate output quality
    │
    ▼
Jinja2 Template → Markdown report (.md)
    │
    ▼
mistletoe (MD→HTML) → fpdf2 → PDF report (.pdf)
    │
    ▼
Streamlit UI → Display + Download buttons
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

## Processing Philosophy

- Signal over noise
- Importance over chronology
- Information density over verbosity
- Clarity over complexity
- Evidence over assertion
- Analysis over simple summarization

---

## Git Remote

```
git remote add origin https://github.com/AshayK003/PACE.git
git branch -M main
git push -u origin main
```
