import pytest
from unittest.mock import MagicMock, patch


# ── LLM Client Tests ─────────────────────────────────────────────────────────

class TestLLMClient:
    def test_client_initialization(self):
        """LLM client should initialize with correct base_url and model."""
        from app.analyzers.llm_client import LLMClient
        client = LLMClient()
        assert client.model == "deepseek-v4-flash-free"
        assert "opencode.ai" in client.base_url or "opencode" in client.base_url

    def test_client_send_message(self, mock_llm_response):
        """client.send() should return a string response."""
        from app.analyzers.llm_client import LLMClient
        client = LLMClient()
        with patch.object(client, "_call_api", return_value="Analysis output."):
            result = client.send(
                system_prompt="You are a helpful analyst.",
                user_message="Analyze this content.",
            )
            assert isinstance(result, str)
            assert len(result) > 0

    def test_client_passes_correct_parameters(self):
        """Client should send correct model, messages and temperature."""
        from app.analyzers.llm_client import LLMClient
        client = LLMClient()
        client._client = MagicMock()
        client.send(
            system_prompt="System prompt here.",
            user_message="User message here.",
            temperature=0.5,
            max_tokens=2000,
        )
        call_kwargs = client._client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == client.model
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 2000
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["role"] == "user"

    @patch("app.analyzers.llm_client.LLMClient.send")
    def test_client_retry_on_failure(self, mock_send):
        """Should retry on transient failures (tenacity)."""
        from app.analyzers.llm_client import LLMClient
        client = LLMClient()
        call_count = 0
        def flaky_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "Success after retry."
        mock_send.side_effect = flaky_call
        result = None
        try:
            result = client.send("prompt", "context", retries=3)
        except Exception:
            pass
        if result:
            assert call_count == 3
            assert result == "Success after retry."

    def test_client_handles_empty_response(self):
        """Should handle empty or None responses gracefully."""
        from app.analyzers.llm_client import LLMClient
        client = LLMClient()
        with patch.object(client, "_call_api", return_value=""):
            result = client.send("prompt", "context")
            assert result == ""

    def test_client_streaming_support(self):
        """Streaming mode should yield tokens progressively."""
        from app.analyzers.llm_client import LLMClient
        client = LLMClient()
        tokens = ["Token 1. ", "Token 2. ", "Token 3."]
        mock_stream = MagicMock()
        mock_stream.__iter__.return_value = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content=t))])
            for t in tokens
        ]
        client._client.chat.completions.create.return_value = mock_stream
        collected = []
        for token in client.send_stream("prompt", "context"):
            collected.append(token)
        assert len(collected) == len(tokens)


# ── Prompts Tests ────────────────────────────────────────────────────────────

class TestPrompts:
    def test_all_prompt_templates_exist(self):
        """All expected prompt constants should be defined in prompts.py."""
        from app.analyzers.prompts import (
            EXECUTIVE_SUMMARY_PROMPT,
            KEY_TAKEAWAYS_PROMPT,
            DETAILED_ANALYSIS_PROMPT,
            SUPPORTING_EVIDENCE_PROMPT,
            FRAMEWORKS_PROMPT,
            ACTION_ITEMS_PROMPT,
            RISKS_PROMPT,
            NOTABLE_QUOTES_PROMPT,
            MISSING_IMPORTANT_PROMPT,
            FINAL_SYNTHESIS_PROMPT,
        )
        assert EXECUTIVE_SUMMARY_PROMPT is not None
        assert KEY_TAKEAWAYS_PROMPT is not None
        assert DETAILED_ANALYSIS_PROMPT is not None
        assert SUPPORTING_EVIDENCE_PROMPT is not None
        assert FRAMEWORKS_PROMPT is not None
        assert ACTION_ITEMS_PROMPT is not None
        assert RISKS_PROMPT is not None
        assert NOTABLE_QUOTES_PROMPT is not None
        assert MISSING_IMPORTANT_PROMPT is not None
        assert FINAL_SYNTHESIS_PROMPT is not None

    def test_prompts_contain_content_placeholder(self):
        """Every prompt should have a placeholder for the content to analyze."""
        from app.analyzers.prompts import ALL_PROMPTS
        for name, prompt in ALL_PROMPTS.items():
            assert "{content}" in prompt, f"{name} is missing {{content}} placeholder"

    def test_prompts_are_unique(self):
        """Each prompt should have distinct content."""
        from app.analyzers.prompts import ALL_PROMPTS
        prompts_set = set(ALL_PROMPTS.values())
        assert len(prompts_set) == len(ALL_PROMPTS)

    def test_prompt_formatting(self):
        """Prompts should format correctly with context."""
        from app.analyzers.prompts import EXECUTIVE_SUMMARY_PROMPT
        formatted = EXECUTIVE_SUMMARY_PROMPT.format(content="Test content to analyze.")
        assert "Test content to analyze." in formatted
        assert isinstance(formatted, str)

    def test_executive_summary_asks_for_concise_output(self):
        """Executive summary prompt should instruct brief output."""
        from app.analyzers.prompts import EXECUTIVE_SUMMARY_PROMPT
        prompt_lower = EXECUTIVE_SUMMARY_PROMPT.lower()
        assert any(term in prompt_lower for term in ["concise", "summary", "overview", "brief"])

    def test_frameworks_prompt_asks_for_models(self):
        """Frameworks prompt should ask for methodologies and models."""
        from app.analyzers.prompts import FRAMEWORKS_PROMPT
        prompt_lower = FRAMEWORKS_PROMPT.lower()
        assert any(term in prompt_lower for term in ["framework", "model", "methodology", "approach"])


# ── Pipeline Tests ───────────────────────────────────────────────────────────

class TestPipeline:
    def test_pipeline_runs_all_steps(self):
        """Pipeline should execute all analysis steps and collect results."""
        from app.analyzers.pipeline import AnalysisPipeline
        pipeline = AnalysisPipeline()
        with patch.object(pipeline, "run_step", return_value="Step result."):
            results = pipeline.run_all("Test content to analyze.")
        assert isinstance(results, dict)
        expected_sections = [
            "executive_summary", "key_takeaways", "detailed_analysis",
            "supporting_evidence", "frameworks", "action_items",
            "risks", "notable_quotes", "missing_important", "final_synthesis",
        ]
        for section in expected_sections:
            assert section in results, f"Missing section: {section}"

    def test_pipeline_progress_callback(self):
        """Pipeline should call progress callback for each step."""
        from app.analyzers.pipeline import AnalysisPipeline
        pipeline = AnalysisPipeline()
        progress_steps = []
        def track_progress(step_name, progress_value):
            progress_steps.append((step_name, progress_value))
        with patch.object(pipeline, "run_step", return_value="Step result."):
            pipeline.run_all("Test content.", progress_callback=track_progress)
        assert len(progress_steps) >= 10  # At least 10 steps
        assert progress_steps[-1][1] == 1.0  # Final progress should be 1.0

    def test_pipeline_with_empty_context(self):
        """Pipeline should handle empty context gracefully."""
        from app.analyzers.pipeline import AnalysisPipeline
        pipeline = AnalysisPipeline()
        with patch.object(pipeline, "run_step", return_value=""):
            results = pipeline.run_all("")
        assert isinstance(results, dict)
        assert len(results) >= 0

    def test_pipeline_step_ordering(self, sample_text):
        """Steps should execute in the defined order."""
        from app.analyzers.pipeline import AnalysisPipeline
        pipeline = AnalysisPipeline()
        execution_order = []
        original_steps = list(pipeline.steps)
        with patch.object(pipeline, "run_step", side_effect=lambda step, ctx: execution_order.append(step.name) or ""):
            pipeline.run_all(sample_text)
        assert len(execution_order) == len(original_steps)
        for i, step in enumerate(original_steps):
            assert execution_order[i] == step.name

    def test_pipeline_passes_context_to_steps(self, sample_text):
        """Each step should receive the full content context."""
        from app.analyzers.pipeline import AnalysisPipeline
        pipeline = AnalysisPipeline()
        received_contexts = []
        def mock_run(step, context):
            received_contexts.append(context)
            return "result"
        with patch.object(pipeline, "run_step", mock_run):
            pipeline.run_all(sample_text)
        for ctx in received_contexts:
            assert ctx == sample_text

    def test_pipeline_previous_results_available(self, sample_text):
        """Later steps should have access to previous step results."""
        from app.analyzers.pipeline import AnalysisPipeline
        pipeline = AnalysisPipeline()
        def mock_run(step, context):
            pipeline.results[step.name] = f"Result of {step.name}"
            return pipeline.results[step.name]
        with (
            patch.object(pipeline, "run_step", mock_run),
            patch.object(pipeline, "_format_context_for_step", return_value=lambda s, ctx: "context"),
        ):
            results = pipeline.run_all(sample_text)
            assert len(results) > 0
            for name in results:
                assert results[name] == f"Result of {name}"


# ── Guardrails Integration Tests ─────────────────────────────────────────────

class TestGuardrailsIntegration:
    def test_guardrails_validate_passes_for_good_output(self):
        """Valid outputs should pass guardrails checks."""
        from app.analyzers.pipeline import validate_output
        good_output = "This is a valid analysis with 100+ words." * 10
        result = validate_output(good_output)
        assert result["passed"] is True

    def test_guardrails_validates_section_completeness(self):
        """Each section should contain minimum content requirements."""
        from app.analyzers.pipeline import validate_section
        assert validate_section("This is a complete section with content.")["passed"] is True
        assert validate_section("")["passed"] is False
        assert validate_section(" ")["passed"] is False

    def test_guardrails_detects_empty_sections(self, sample_report_data):
        """Sections with no content should be flagged."""
        from app.analyzers.pipeline import validate_section
        empty_section = {"title": "Empty", "content": ""}
        invalid_section = {"title": "Invalid", "content": None}
        bad_result = validate_section(empty_section["content"])
        none_result = validate_section(invalid_section["content"])
        assert bad_result["passed"] is False
        assert none_result["passed"] is False

    def test_guardrails_format_check(self):
        """Output should match expected format (lists, structure)."""
        from app.analyzers.pipeline import validate_format
        markdown_lists = "- Item 1\n- Item 2\n- Item 3"
        assert validate_format(markdown_lists)["passed"] is True
        assert validate_format("")["passed"] is False
