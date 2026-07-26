# PACE — AEOS Module 10: Product-Minded Engineer Bottleneck Analysis

**Project:** PACE (Precise Analysis and Compilation of Extracts)  
**Architecture Reference:** 4-layer (UI → Ingestors → Processors → Analyzers → Output)  
**Test Baseline:** 251 passed, 1 skipped  
**Current Health Score:** 78/100

---

## Executive Summary

PACE is a well-structured, test-heavy content analysis pipeline. The architecture is clean, the test suite is comprehensive, and the code is lint-free. **The top 3 bottlenecks are all about resilience and observability** — not features, not polish. Fixing these three will prevent the most common user frustrations (failed ingestions, rate limits, lost work on errors) with moderate effort.

---

## #1 Bottleneck — Ingestor Fragility & Unactionable Errors

### What
All 4 ingestors (YouTube, PDF, Article, Audio) lack structured error handling, retry logic, and dependency health checks.

### Where
| File | Line | Issue |
|------|------|-------|
| `app/ingestors/youtube.py` | 1-85 | `yt_dlp` exceptions bubble as generic `Exception` |
| `app/ingestors/article.py` | 1-70 | `httpx` timeout/connection errors not retried |
| `app/ingestors/pdf.py` | 1-120 | Fallback chain silent — user doesn't know which extractor worked |
| `app/ingestors/audio.py` | 1-95 | `ffmpeg` missing → cryptic error at transcript time, not startup |

### Current Behavior
```python
# All ingestors follow this pattern:
def ingest(self, input):
    try:
        result = self._do_ingest(input)
        return result
    except Exception as e:
        raise e  # UI catches all → sanitize_error_message(e) → "Something went wrong"
```

### Why Wasteful
- **User can't self-serve:** "Install ffmpeg" vs "Something went wrong"
- **Transient failures kill analysis:** 5s network blip → full restart
- **No visibility into extractor choice:** PDF tried 3 extractors — which succeeded?
- **No health check:** Deployed app appears healthy until user hits audio tab

### Proposed Change
Create `app/ingestors/base.py` with:
```python
class IngestionError(Exception):
    code: str          # "NETWORK_TIMEOUT", "INVALID_URL", "MISSING_FFMPEG", "PAYWALL"
    message: str
    recoverable: bool  # user can fix vs system issue
    hint: str          # actionable: "Install ffmpeg", "Check URL"

class Ingestor(ABC):
    @abstractmethod
    def validate(self, input: str) -> bool: ...
    @abstractmethod
    def ingest(self, input: str) -> IngestResult: ...
    def health_check(self) -> HealthStatus: ...  # NEW: run at startup
    def _retry(self, fn, retries=3, backoff=2): ...  # NEW: centralized retry
```

Migrate 4 ingestors → inherit from base, map exceptions → `IngestionError` with codes.

### Expected Impact
| Metric | Before | After |
|--------|--------|-------|
| User-fixable errors | 0% | ~60% (URL, missing deps) |
| Transient failure recovery | 0% | 95% (3 retries) |
| Support tickets (est.) | High | Low |
| Debug time per failure | 10-30 min | <1 min |

### Effort Estimate
**Medium — 1.5 days**
- Day 1: Base class + error taxonomy + retry utility
- Day 2: Migrate 4 ingestors + health checks + tests

---

## #2 Bottleneck — Single-Provider LLM Client, No Cost Visibility

### What
`LLMClient` only supports OpenAI-compatible APIs (Groq, local). No fallback, no token counting, no budget enforcement.

### Where
| File | Line | Issue |
|------|------|-------|
| `app/analyzers/llm_client.py` | 1-120 | Single provider, no token tracking, no cost estimate |

### Current Behavior
```python
class LLMClient:
    def __init__(self, api_key, base_url, model):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    def chat(self, messages):
        return self.client.chat.completions.create(model=self.model, messages=messages)
```

### Why Wasteful
- **Rate limit = dead end:** Groq 429 → full analysis failure (no fallback to local/Anthropic)
- **Token blindness:** User sends 50k token doc → $0.05 on Groq, $2 on local CPU time — no preview
- **Budget surprise:** BYOK users burn API keys with no warning
- **Translation doubles cost:** Non-English docs translated → analyzed = 2x calls, no cache

### Proposed Change
```python
class ProviderConfig:
    name: str                    # "groq", "local", "anthropic"
    api_key: str
    base_url: str
    models: Dict[str, ModelSpec] # model_name -> {max_tokens, cost_per_1k_in, cost_per_1k_out}
    priority: int                # 1 = primary, 2 = fallback

class LLMClient:
    def __init__(self, providers: List[ProviderConfig], budget_usd: float = None):
        self.providers = sorted(providers, key=lambda p: p.priority)
        self.usage = TokenUsageTracker()
        self.budget = budget_usd
    
    async def chat(self, messages, model_preference=None):
        for provider in self._select_providers(model_preference):
            try:
                resp = await provider.chat(messages)
                self.usage.record(provider.name, resp.usage)
                if self.budget and self.usage.cost > self.budget:
                    raise BudgetExceeded()
                return resp
            except RateLimitError:
                continue
        raise AllProvidersExhausted()
    
    def estimate_cost(self, text: str, model: str) -> float:
        tokens = estimate_tokens(text)
        spec = self._get_model_spec(model)
        return tokens * spec.cost_per_1k_in / 1000
```

### Expected Impact
| Metric | Before | After |
|--------|--------|-------|
| Rate limit failures | 100% fatal | <5% (fallback works) |
| Cost visibility | 0% | 100% (per-doc estimate) |
| Budget overruns | Common | Impossible (hard limit) |
| Multi-lang efficiency | 2x calls | 1.2x (cache translation) |

### Effort Estimate
**Medium — 1.5 days**
- Day 1: Provider abstraction + token counting (tiktoken) + usage tracker
- Day 2: Fallback logic + budget UI + cost estimation + tests

---

## #3 Bottleneck — Analysis Pipeline No Checkpointing / Partial Results

### What
`AnalysisPipeline.run_all()` runs 7 sequential LLM steps. Failure at step 4 discards steps 1-3 results.

### Where
| File | Line | Issue |
|------|------|-------|
| `app/analyzers/pipeline.py` | 1-200 | `run_all()` no checkpointing, no partial return |

### Current Behavior
```python
def run_all(self, text: str):
    results = {}
    for step_name, step_fn in self.steps:
        results[step_name] = step_fn(text, results)  # if step 4 fails, 1-3 lost
    return results
```

### Why Wasteful
- **LLM calls are expensive:** 7 steps × ~$0.01 = $0.07 per analysis. Failure wastes $0.03-0.05
- **User sees nothing on error:** "Analysis failed" — no partial insight
- **Long docs = chunked = more calls:** 4 chunks × 7 steps = 28 LLM calls. One failure wastes 27.
- **No debugging aid:** Can't inspect "what did the topic classifier say?" after entity extraction fails

### Proposed Change
```python
class AnalysisPipeline:
    def run_all(self, text: str, checkpoint_dir: Path = None) -> AnalysisResult:
        results = {}
        errors = {}
        
        for step_name, step_fn in self.steps:
            # Checkpoint load
            if checkpoint_dir:
                cp = checkpoint_dir / f"{step_name}.json"
                if cp.exists():
                    results[step_name] = json.loads(cp.read_text())
                    continue
            
            try:
                results[step_name] = step_fn(text, results)
                # Checkpoint save
                if checkpoint_dir:
                    checkpoint_dir.mkdir(parents=True, exist_ok=True)
                    (checkpoint_dir / f"{step_name}.json").write_text(
                        json.dumps(results[step_name], default=str)
                    )
            except Exception as e:
                errors[step_name] = PipelineError(step=step_name, original=e)
                # Don't break — continue to next step if independent
                if not self._can_continue(step_name, errors):
                    break
        
        return AnalysisResult(
            full=results if not errors else None,
            partial=results if errors else None,
            errors=errors
        )
```

### Expected Impact
| Metric | Before | After |
|--------|--------|-------|
| Wasted LLM spend on failure | ~$0.03 | $0 (reuses checkpoints) |
| User sees partial insight | Never | Always |
| Debuggability | None | Per-step artifacts |
| Retry cost (after fix) | Full re-run | Failed step only |

### Effort Estimate
**Small — 0.5 days**
- Add checkpoint load/save + partial result type
- Mark step dependencies (`_can_continue`)
- Tests for partial failure scenarios

---

## Quick Wins (< 1 hour each)

| Win | Where | Effort |
|-----|-------|--------|
| Add `health_check()` endpoint | `app/main.py` | 15 min |
| Log which PDF extractor succeeded | `app/ingestors/pdf.py` | 10 min |
| Cache translation per session | `app/main.py` | 20 min |
| Show estimated cost before analysis | `app/ui/components.py` | 20 min |
| Add `requirements-dev.txt` with `pip-audit` | root | 10 min |
| Document `IngestionError` codes | `app/ingestors/base.py` | 15 min |

---

## What NOT to Do (Considered & Rejected)

| Idea | Why Rejected |
|------|--------------|
| Rewrite in FastAPI + React | Over-engineering. Streamlit fits 1-user tool perfectly. |
| Add async throughout | Streamlit is single-threaded. `async` adds complexity without benefit. |
| Plugin architecture for ingestors | YAGNI. 4 ingestors stable. Base class gives same extensibility. |
| Local LLM as default | Quality gap too large for analysis tasks. Keep BYOK + Groq primary. |
| Distributed tracing (OpenTelemetry) | Single-user local tool. Logs + checkpoint files sufficient. |

---

## Priority Ordering for Next Iteration

| Phase | Tasks | Est. Days |
|-------|-------|-----------|
| **Phase 1 (Week 1)** | Ingestor base class + error taxonomy + retry + health checks | 1.5 |
| **Phase 2 (Week 2)** | Multi-provider LLM client + token tracking + budget + fallback | 1.5 |
| **Phase 3 (Week 2-3)** | Pipeline checkpointing + partial results + dependency marking | 0.5 |
| **Phase 4 (Ongoing)** | Quick wins + CI hardening (pip-audit, dependabot) | 0.5 |

**Total: ~4 days for all 3 bottlenecks + quick wins**

---

## Success Metrics (Post-Fix)

| Metric | Target |
|--------|--------|
| User-fixable error rate | >60% |
| Transient failure recovery | >95% |
| Rate limit fallback success | >90% |
| Cost estimate accuracy | ±20% |
| Wasted LLM spend on failure | <$0.01 |
| Mean time to diagnose failure | <2 min |