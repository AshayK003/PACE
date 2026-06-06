import streamlit as st


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
            st.text_input(
                "API Key",
                type="password",
                key="api_key",
                placeholder="Optional — leave empty for default key",
                help="Enter a custom API key to override the default. Your key is never stored.",
            )

            presets = {
                "Default (OpenCode Zen)": ("", ""),
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
            }

            def _apply_preset():
                sel = st.session_state.get("_llm_preset", "Default (OpenCode Zen)")
                url, model = presets.get(sel, ("", ""))
                if url:
                    st.session_state["base_url"] = url
                    st.session_state["model_name"] = model

            st.selectbox(
                "Preset",
                options=list(presets.keys()),
                key="_llm_preset",
                on_change=_apply_preset,
                help="Auto-fills Base URL and Model. Top picks: Gemini 2.5 Flash (250/day), Groq Llama 3.3 70B (1K/day, fastest), Cerebras (14K/day).",
            )

            st.text_input(
                "Base URL",
                key="base_url",
                placeholder="https://generativelanguage.googleapis.com/v1beta/openai/",
                help="OpenAI-compatible API endpoint. Leave empty for the default.",
            )
            st.text_input(
                "Model",
                key="model_name",
                placeholder="gemini-2.5-flash",
                help="Model name to use. Leave empty for the default.",
            )

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
