# Intelligent Export Naming & Categorization for Obsidian Vaults

**Date:** 2026-06-06
**Status:** Approved
**Approach:** LLM as Categorizer (1 extra API call)

## Problem

Currently all exports download with a flat sanitized filename (`analysis_of_...`). No folder structure, no categorization. For users with Obsidian vaults, this means manual reorganization after every analysis.

## Goal

Automatically categorize and name exported files using LLM-derived topic analysis, producing a `Domain/Sub_topic/YYYY-MM-DD_slug.md` structure that drops directly into an Obsidian vault.

## Design Decisions

| Decision | Choice | Reasoning |
|---|---|---|
| Categorization method | LLM call | Zero rules to maintain, handles any topic |
| Filename format | `Date_Prefix + Topic` | Sortable by date, clear topic |
| Folder depth | 2-level: `Domain/Sub_topic` | Balanced — not too shallow, not too deep |
| UI visibility | Editable in sidebar | User can override auto-suggestion |

## Components

### 1. Categorization Module (`app/analyzers/categorizer.py`)

New standalone function called after the main analysis pipeline.

```python
def categorize_content(
    client: LLMClient,
    title: str,
    key_takeaways: list[str],
    topic: str,
) -> dict:
    """Return {domain, sub_topic, slug} for a piece of content."""
```

**Prompt constraints:**
- `domain` must be one of: `Tech, Business, Science, Health, Education, Culture, Finance, Politics, Sports, Other`
- `sub_topic` — freeform, max 2 words
- `slug` — snake_case, max 5 words, no special characters

**Fallback:** On any error (API failure, malformed response), returns:
```python
{"domain": "Other", "sub_topic": "Unsorted", "slug": "report"}
```

**Token cost:** ~150 tokens input, ~30 tokens output. Negligible.

### 2. Path Builder (`app/config.py`)

New utility function alongside existing `safe_filename`.

```python
def build_export_path(
    domain: str,
    sub_topic: str,
    slug: str,
    date_str: str,
) -> dict:
    """Return {folder, filename, full_path} for export."""
```

Returns:
- `folder`: `"Tech/AI"`
- `filename`: `"2026-06-06_transformer_architecture_explained"`
- `full_path`: `"Tech/AI/2026-06-06_transformer_architecture_explained"`

Extensions (`.md`, `.pdf`, `.epub`) are added by each renderer at download time, not by this function.

### 3. Obsidian Frontmatter Update (`app/output/obsidian.py`)

Enhanced `render_obsidian` adds two new frontmatter fields:

```yaml
---
title: "Transformer Architecture Explained"
date: 2026-06-06
source_type: YouTube
source_url: https://youtube.com/watch?v=...
category: Tech/AI
tags: [pace, analysis, youtube, transformer, deep-learning, tech, ai]
aliases: ["Transformer Architecture Explained"]
vault_path: "Tech/AI/2026-06-06_transformer_architecture_explained.md"
---
```

Changes:
- `category` field — the `Domain/Sub_topic` path
- `vault_path` field — full relative path for easy import
- `tags` enriched — adds domain + sub_topic as lowercase tags alongside existing tags

### 4. Sidebar UI (`app/ui/sidebar.py`)

New "Export Path" section that appears only when `has_report == True`.

Three editable fields:
1. **Domain** — `st.selectbox` with fixed list (Tech, Business, Science, Health, Education, Culture, Finance, Politics, Sports, Other)
2. **Sub-topic** — `st.text_input`, pre-filled from LLM
3. **Filename** — `st.text_input`, pre-filled from `{date}_{slug}`

Below the fields: read-only preview of the full path.

All fields write to `st.session_state.export_path` which is read by `render_download_buttons`.

### 5. Main Integration (`app/main.py`)

Updated `_run_analysis` flow:

1. Main analysis executes (existing)
2. After results are collected, call `categorize_content(client, display_title, key_takeaways, topic)`
3. Store result in `st.session_state.export_path`
4. Sidebar renders editable fields from `export_path`
5. `render_download_buttons` uses current field values to build filenames

**Key session state fields:**
- `st.session_state.export_path` — dict with `domain`, `sub_topic`, `slug`, `date`
- All download functions read from this dict

### 6. Download Button Updates (`app/ui/components.py`)

`render_download_buttons` now builds filenames from the export path:

```python
date_str = export_path["date"]
slug = export_path["slug"]
folder = export_path["folder"]
base = f"{date_str}_{slug}"
# Downloads: {base}.md, {base}.pdf, {base}.epub
# Obsidian: {folder}/{base}.md
```

## Error Handling

| Failure | Behavior |
|---|---|
| Categorization API call fails | Fallback to `Other/Unsorted/{date}_report` |
| LLM returns malformed JSON | Parse error → fallback |
| User clears a field | Use remaining fields, default missing to "report" |
| Domain not in fixed list | Ignore LLM value, use "Other" |

## Files Changed

| File | Change |
|---|---|
| `app/analyzers/categorizer.py` | **NEW** — LLM categorization function |
| `app/config.py` | Add `build_export_path` function |
| `app/output/obsidian.py` | Add `category`, `vault_path` to frontmatter, enrich tags |
| `app/ui/sidebar.py` | Add "Export Path" section with editable fields |
| `app/ui/components.py` | Update `render_download_buttons` to use export path |
| `app/main.py` | Call categorizer after analysis, store in session state |
| `tests/test_categorizer.py` | **NEW** — unit tests for categorizer |
| `tests/test_config.py` | Add tests for `build_export_path` |
| `tests/test_output.py` | Update Obsidian tests for new frontmatter fields |

## Testing

- Unit tests for `categorize_content` (mock LLM response, error fallback)
- Unit tests for `build_export_path` (normal cases, edge cases)
- Obsidian frontmatter tests (new fields present, tags enriched)
- Integration: verify full flow from analysis → categorization → download filename
