import streamlit as st

from app.config import BASE_URL, build_export_path

try:
    from curl_cffi import requests as _curl_requests
except Exception:
    import httpx as _curl_requests  # type: ignore[no-redef]

_DOMAINS = [
    "Tech", "Business", "Science", "Health", "Education",
    "Culture", "Finance", "Politics", "Sports", "Other",
]

PROVIDERS = {
    "OpenCode Zen (free)": {
        "base_url": "",
        "models": [
            "deepseek-v4-flash-free",
            "deepseek-v4-flash",
            "deepseek-v3.1",
            "gpt-4o-mini",
            "gpt-4o",
            "claude-sonnet-4",
            "gemini-2.5-flash",
            "llama-3.3-70b",
        ],
        "key_prefix": "",
        "help": "Built-in free tier — no API key required.",
    },
    "Google Gemini (free)": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ],
        "key_prefix": "AIza",
        "help": "1,500 req/day free. No credit card.",
    },
    "Groq (free)": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-4-scout-17b-16e-instruct",
            "qwen3-32b",
            "gpt-oss-120b",
        ],
        "key_prefix": "gsk_",
        "help": "30 RPM, 14,400 RPD. Ultra-fast LPU inference.",
    },
    "Cerebras (free)": {
        "base_url": "https://api.cerebras.ai/v1",
        "models": [
            "llama-3.3-70b",
            "gpt-oss-120b",
        ],
        "key_prefix": "csk-",
        "help": "1M tokens/day. No credit card.",
    },
    "OpenRouter (free)": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "deepseek/deepseek-r1-0528:free",
            "deepseek/deepseek-chat-v3.1:free",
            "qwen/qwen3-235b-a22b:free",
            "qwen/qwen3-coder-480b-a35b:free",
            "meta-llama/llama-4-scout:free",
            "meta-llama/llama-4-maverick:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "openai/gpt-oss-120b:free",
            "mistralai/devstral-2512:free",
        ],
        "key_prefix": "sk-or-",
        "help": "20 RPM, 50 RPD on free models. 30+ free models.",
    },
    "Mistral (free)": {
        "base_url": "https://api.mistral.ai/v1",
        "models": [
            "mistral-small-latest",
            "mistral-large-latest",
        ],
        "key_prefix": "",
        "help": "~1B tokens/month on Experiment tier.",
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "models": [
            "deepseek-v4-flash",
            "deepseek-chat",
        ],
        "key_prefix": "sk-",
        "help": "Very cheap (~$0.0001/1K tokens). Long-context reasoning.",
    },
    "Custom (OpenAI-compatible)": {
        "base_url": "",
        "models": [],
        "key_prefix": "",
        "help": "Any OpenAI-compatible endpoint.",
    },
}

_KEY_PREFIX_MAP = {
    "gsk_": "Groq (free)",
    "csk-": "Cerebras (free)",
    "sk-or-": "OpenRouter (free)",
    "AIza": "Google Gemini (free)",
}


def _detect_provider(api_key: str) -> str | None:
    if not api_key:
        return None
    for prefix, provider in _KEY_PREFIX_MAP.items():
        if api_key.startswith(prefix):
            return provider
    if api_key.startswith("sk-"):
        return "DeepSeek"
    return None


def _test_llm_connection(provider: str, model: str, api_key: str, base_url: str) -> tuple[bool, str]:
    url = (base_url or BASE_URL).rstrip("/")
    key = api_key or "no-key"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1, "stream": False}
    try:
        resp = _curl_requests.post(f"{url}/chat/completions", headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            actual = data.get("model", model)
            return True, f"Connected — {actual}"
        body = resp.text[:300]
        return False, f"HTTP {resp.status_code} — {body}"
    except Exception as exc:
        return False, f"Connection failed — {exc}"


def _render_llm_status() -> None:
    st.divider()
    provider = st.session_state.get("_llm_provider", next(iter(PROVIDERS)))
    model = st.session_state.get("model_name", "")
    api_key = st.session_state.get("api_key", "") or ""
    base_url = st.session_state.get("base_url", "") or ""

    resolved_url = (base_url or BASE_URL).rstrip("/") if (base_url or BASE_URL) else ""
    test_config = f"{provider}|{model}|{resolved_url}"

    prev_test_config = st.session_state.get("_prev_test_config", "")
    if prev_test_config and test_config != prev_test_config:
        st.session_state.pop("llm_test_result", None)

    result = st.session_state.get("llm_test_result")
    if result:
        ok, msg = result
        icon = ":material/check_circle:" if ok else ":material/error:"
        st.markdown(f"**LLM Status** {icon}  \n{msg} — `{provider}` · `{model}`")
    else:
        st.markdown(f"**LLM Status**  \n`{provider}` · `{model}`")

    if st.button("Test Connection", key="test_llm_btn", use_container_width=True):
        ok, msg = _test_llm_connection(provider, model, api_key, base_url)
        st.session_state["llm_test_result"] = (ok, msg)
        st.session_state["_prev_test_config"] = test_config
        st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### PACE")
        st.caption("AI-powered content analysis")

        with st.expander("Settings", expanded=False):
            st.slider(
                "Chunk size",
                min_value=500,
                max_value=4000,
                value=2000,
                step=100,
                key="chunk_size",
                help="Larger chunks give more context per analysis step but use more tokens.",
            )

        with st.expander("LLM Settings", expanded=False):
            provider_names = list(PROVIDERS.keys())

            current_provider = st.session_state.get("_llm_provider", provider_names[0])
            if current_provider not in provider_names:
                current_provider = provider_names[0]

            provider = st.selectbox(
                "Provider",
                options=provider_names,
                index=provider_names.index(current_provider),
                key="_llm_provider",
                help="Select a provider. Auto-detects from API key when possible.",
            )

            prov = PROVIDERS[provider]

            api_key = st.text_input(
                "API Key",
                type="password",
                key="api_key",
                placeholder="Paste your API key — provider auto-detected",
                help=prov["help"],
            )

            prev_key = st.session_state.get("_prev_api_key", "")
            if api_key and api_key != prev_key:
                detected = _detect_provider(api_key)
                if detected and detected != provider:
                    st.session_state["_llm_provider"] = detected
                    if PROVIDERS[detected]["models"]:
                        st.session_state["model_name"] = PROVIDERS[detected]["models"][0]
                    st.session_state["_prev_api_key"] = api_key
                    st.rerun()
                else:
                    st.session_state["_prev_api_key"] = api_key
            elif not api_key:
                st.session_state.pop("_prev_api_key", None)

            if prov["models"]:
                current_model = st.session_state.get("model_name", prov["models"][0])
                if current_model not in prov["models"]:
                    current_model = prov["models"][0]
                    st.session_state["model_name"] = current_model
                model = st.selectbox(
                    "Model",
                    options=prov["models"],
                    index=prov["models"].index(current_model),
                    key="model_name",
                    help="Select a model from this provider.",
                )
            else:
                model = st.text_input(
                    "Model",
                    key="model_name",
                    placeholder="model-name",
                    help="Enter the model name for your endpoint.",
                )

            if provider == "Custom (OpenAI-compatible)":
                st.text_input(
                    "Base URL",
                    key="base_url",
                    placeholder="https://api.example.com/v1",
                    help="OpenAI-compatible API endpoint.",
                )
            else:
                st.session_state["base_url"] = prov["base_url"]

        _render_llm_status()

        if st.session_state.get("md_content"):
            _render_export_path_section()

        st.divider()
        st.markdown(
            "Analyze YouTube videos, PDFs, web articles, "
            "audio files, or raw text into structured reports."
        )
        st.markdown(
            '<div style="margin-top:16px;text-align:center;">'
            '<a href="https://chai4.me/darkcharon3301" target="_blank" '
            'title="Support darkcharon3301 on Chai4Me" '
            'style="display:inline-flex;flex-direction:column;align-items:center;'
            'justify-content:center;background:#ffffff;padding:8px 32px;'
            'border-radius:16px;text-decoration:none;border:1px solid #e5e7eb;'
            'box-shadow:0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);'
            'transition:transform 0.2s;">'
            '<img src="https://chai4.me/icons/wordmark.png" alt="Chai4Me" '
            'style="height:32px;object-fit:contain;"/></a></div>',
            unsafe_allow_html=True,
        )


def _render_export_path_section() -> None:
    ep = st.session_state.get("export_path", {})
    with st.expander("Export Path", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            current_domain = ep.get("domain", "Other")
            if current_domain not in _DOMAINS:
                current_domain = "Other"
            domain = st.selectbox(
                "Domain",
                options=_DOMAINS,
                index=_DOMAINS.index(current_domain),
                key="ep_domain",
            )
        with col2:
            sub_topic = st.text_input(
                "Sub-topic",
                value=ep.get("sub_topic", "Unsorted"),
                key="ep_sub_topic",
                placeholder="e.g., Testing, Blockchain",
            )

        slug = st.text_input(
            "Filename",
            value=ep.get("slug", "report"),
            key="ep_slug",
            placeholder="e.g., transformer_architecture_explained",
        )

        from datetime import date as _date
        date_str = ep.get("date", _date.today().isoformat())
        path_info = build_export_path(domain, sub_topic, slug, date_str)
        st.session_state.export_path = {
            "domain": domain,
            "sub_topic": sub_topic,
            "slug": slug,
            "date": date_str,
            "folder": path_info["folder"],
            "full_path": path_info["full_path"],
        }
        st.caption(f"Path: `{path_info['full_path']}.md`")
