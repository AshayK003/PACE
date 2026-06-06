import streamlit as st

from app.config import build_export_path

_DOMAINS = [
    "Tech", "Business", "Science", "Health", "Education",
    "Culture", "Finance", "Politics", "Sports", "Other",
]


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
            provider = st.radio(
                "Provider",
                ["OpenCode Zen", "Other"],
                key="llm_provider",
                horizontal=True,
            )

            if provider == "OpenCode Zen":
                st.text_input(
                    "API Key",
                    type="password",
                    key="api_key",
                    placeholder="Optional — leave empty for env key",
                    help="Your OpenCode Zen API key. Leave empty to use the environment variable OPENCODE_ZEN_KEY.",
                )
                zen_models = [
                    "deepseek-v4-flash-free",
                    "gemini-2.5-flash",
                    "gemini-2.5-flash-lite",
                    "gpt-4o-mini",
                    "gpt-4o",
                    "claude-3.5-sonnet",
                    "claude-3-haiku",
                ]
                st.selectbox(
                    "Model",
                    options=zen_models,
                    key="model_name",
                    help="Select a model from OpenCode Zen.",
                )
                st.session_state["base_url"] = ""
            else:
                other_presets = {
                    "Gemini 2.5 Flash": (
                        "https://generativelanguage.googleapis.com/v1beta/openai/",
                        "gemini-2.5-flash",
                    ),
                    "Gemini 2.5 Flash-Lite": (
                        "https://generativelanguage.googleapis.com/v1beta/openai/",
                        "gemini-2.5-flash-lite",
                    ),
                    "Groq Llama 3.3 70B": (
                        "https://api.groq.com/openai/v1",
                        "llama-3.3-70b-versatile",
                    ),
                    "Cerebras Llama 3.3 70B": (
                        "https://api.cerebras.ai/v1",
                        "llama-3.3-70b-versatile",
                    ),
                    "OpenRouter DeepSeek V3 (free)": (
                        "https://openrouter.ai/api/v1",
                        "deepseek/deepseek-chat-v3.1:free",
                    ),
                    "OpenRouter Qwen3 235B (free)": (
                        "https://openrouter.ai/api/v1",
                        "qwen/qwen3-235b-a22b:free",
                    ),
                    "Mistral Small": (
                        "https://api.mistral.ai/v1",
                        "mistral-small-latest",
                    ),
                    "DeepSeek V4 Flash": (
                        "https://api.deepseek.com",
                        "deepseek-v4-flash",
                    ),
                    "Custom (OpenAI-compatible)": ("", ""),
                }

                def _apply_other_preset():
                    sel = st.session_state.get("_other_preset", "Gemini 2.5 Flash")
                    url, model = other_presets.get(sel, ("", ""))
                    st.session_state["base_url"] = url
                    st.session_state["model_name"] = model

                st.selectbox(
                    "Preset",
                    options=list(other_presets.keys()),
                    key="_other_preset",
                    on_change=_apply_other_preset,
                    help="Auto-fills Base URL and Model. Top picks: Gemini 2.5 Flash (250/day), Groq Llama 3.3 70B (1K/day, fastest).",
                )
                st.text_input(
                    "API Key",
                    type="password",
                    key="api_key",
                    placeholder="Enter your API key",
                    help="API key for the selected provider.",
                )
                st.text_input(
                    "Base URL",
                    key="base_url",
                    placeholder="https://api.example.com/v1",
                    help="OpenAI-compatible API endpoint.",
                )
                st.text_input(
                    "Model",
                    key="model_name",
                    placeholder="model-name",
                    help="Model name to use.",
                )

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
