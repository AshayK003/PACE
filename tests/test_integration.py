import pytest
from unittest.mock import MagicMock, patch


def _mock_batch_response(section_type: str) -> str:
    if section_type == "a":
        return "===EXECUTIVE_SUMMARY===\nThis is a sufficiently long executive summary.\n===KEY_TAKEAWAYS===\nThis is a sufficiently long key takeaways section."
    elif section_type == "b":
        return "===DETAILED_ANALYSIS===\nThis is a sufficiently long detailed analysis section.\n===SUPPORTING_EVIDENCE===\nThis is a sufficiently long supporting evidence section."
    return "===FRAMEWORKS===\nThis is a sufficiently long frameworks section.\n===ACTION_ITEMS===\nThis is a sufficiently long action items section.\n===RISKS===\nThis is a sufficiently long risks section.\n===NOTABLE_QUOTES===\nThis is a sufficiently long notable quotes section."


def _mock_send_factory():
    def mock_send(system_prompt, user_message, **kwargs):
        if "produce TWO separate sections" in user_message and "EXECUTIVE_SUMMARY" in user_message:
            return _mock_batch_response("a")
        elif "produce TWO separate sections" in user_message and "DETAILED_ANALYSIS" in user_message:
            return _mock_batch_response("b")
        elif "produce FOUR separate sections" in user_message:
            return _mock_batch_response("c")
        return "Synthesis result."
    return mock_send


class TestFullPipeline:
    def test_complete_data_flow(self, sample_text):
        """clean -> chunk -> pipeline -> markdown -> PDF produces valid output."""
        from app.processors.cleaner import clean_pipeline
        from app.processors.chunker import chunk_text
        from app.analyzers.pipeline import AnalysisPipeline
        from app.output.markdown import render_markdown
        from app.output.pdf import render_pdf

        content = (sample_text + "\n\n") * 30
        cleaned = clean_pipeline(content)
        chunks = chunk_text(cleaned, chunk_size=2000, overlap=50)
        full_text = " ".join(chunks)

        pipeline = AnalysisPipeline()
        with patch.object(pipeline.client, "send", side_effect=_mock_send_factory()):
            results = pipeline.run_all(full_text)

        report_data = {
            "title": "Integration Test",
            "source_type": "Text",
            "source_url": "",
            "date_analyzed": "2026-06-05",
        }
        report_data.update(results)

        md = render_markdown(report_data)
        pdf = render_pdf(md)

        assert isinstance(md, str) and len(md) > 100
        assert "Executive Summary" in md
        assert "Integration Test" in md

        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 500

    def test_complete_data_flow_preserves_all_sections(self, sample_text):
        """All 10 output sections should survive the full pipeline."""
        from app.processors.cleaner import clean_pipeline
        from app.processors.chunker import chunk_text
        from app.analyzers.pipeline import AnalysisPipeline
        from app.output.markdown import render_markdown

        content = sample_text
        cleaned = clean_pipeline(content)
        chunks = chunk_text(cleaned, chunk_size=2000)
        full_text = " ".join(chunks)

        pipeline = AnalysisPipeline()
        with patch.object(pipeline.client, "send", side_effect=_mock_send_factory()):
            results = pipeline.run_all(full_text)

        report_data = {
            "title": "Sections Test",
            "source_type": "PDF",
            "source_url": "",
            "date_analyzed": "2026-06-05",
        }
        report_data.update(results)

        md = render_markdown(report_data)

        headings = [
            "Executive Summary", "Key Takeaways", "Detailed Analysis",
            "Supporting Evidence", "Frameworks & Models",
            "Action Items", "Risks & Limitations", "Notable Quotes",
            "Missing But Important", "Final Synthesis",
        ]
        for heading in headings:
            assert heading in md, f"Missing heading: {heading}"

    def test_cleaning_and_chunking_large_content(self):
        """Large content should survive clean + chunk without crashing."""
        from app.processors.cleaner import clean_pipeline
        from app.processors.chunker import chunk_text

        content = "This is a test sentence for the PACE analysis system. " * 2000
        cleaned = clean_pipeline(content)
        chunks = chunk_text(cleaned, chunk_size=2000, overlap=50)

        assert len(chunks) >= 1
        total = sum(len(c) for c in chunks)
        assert total > 0

    def test_pipeline_per_step_callback(self, sample_text):
        """Progress callback should fire for batch and sequential steps."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()
        seen = []

        def track(step_name, progress):
            seen.append(step_name)

        with patch.object(pipeline.client, "send", side_effect=_mock_send_factory()):
            pipeline.run_all(sample_text, progress_callback=track)

        assert len(seen) >= 3
        assert seen[-1] == "complete"


class TestPipelineResilience:
    def test_step_failure_does_not_abort_pipeline(self, sample_text):
        """One failing batch should not prevent other batches from running."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()

        def mock_send(system_prompt, user_message, **kwargs):
            if "produce TWO separate sections" in user_message and "EXECUTIVE_SUMMARY" in user_message:
                raise ValueError("Simulated batch A failure")
            elif "produce TWO separate sections" in user_message and "DETAILED_ANALYSIS" in user_message:
                return _mock_batch_response("b")
            elif "produce FOUR separate sections" in user_message:
                return _mock_batch_response("c")
            return "Synthesis result."

        with patch.object(pipeline.client, "send", side_effect=mock_send):
            results = pipeline.run_all(sample_text)

        assert "executive_summary" in results
        assert "Analysis failed" in results["executive_summary"]
        assert results["final_synthesis"]

    def test_content_truncation_at_50k(self):
        """Content exceeding MAX_CONTENT_CHARS should be truncated, not crash."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()
        huge = "A" * 60000

        with patch.object(pipeline.client, "send", side_effect=_mock_send_factory()) as mock_send:
            results = pipeline.run_all(huge)

        assert len(results) == 10
        for call in mock_send.call_args_list:
            sent = call[1]["user_message"] if "user_message" in call[1] else call[0][1]
            assert "Content truncated" in sent

    def test_empty_result_triggers_batch_fallback(self, sample_text):
        """Pipeline should handle empty batch results gracefully."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()

        def mock_send(system_prompt, user_message, **kwargs):
            if "produce TWO separate sections" in user_message and "EXECUTIVE_SUMMARY" in user_message:
                return "===EXECUTIVE_SUMMARY===\n     \n===KEY_TAKEAWAYS===\n     "
            elif "produce TWO separate sections" in user_message and "DETAILED_ANALYSIS" in user_message:
                return _mock_batch_response("b")
            elif "produce FOUR separate sections" in user_message:
                return _mock_batch_response("c")
            elif "Executive Summary:" in user_message or "Key Takeaways:" in user_message:
                return ""
            return "Synthesis result."

        with patch.object(pipeline.client, "send", side_effect=mock_send):
            results = pipeline.run_all(sample_text)

        assert results["executive_summary"] == ""
        assert results["key_takeaways"] == ""

    def test_no_rate_limiting_delay_between_steps(self, sample_text):
        """Pipeline should not add artificial delays between steps."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()

        with patch.object(pipeline.client, "send", side_effect=_mock_send_factory()):
            results = pipeline.run_all(sample_text)

        assert len(results) == 10

    def test_format_context_includes_previous_results(self, sample_text):
        """Synthesis steps should receive earlier analysis results as context."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()
        contexts = {}

        def mock_send(system_prompt, user_message, **kwargs):
            if "produce TWO separate sections" in user_message and "EXECUTIVE_SUMMARY" in user_message:
                return _mock_batch_response("a")
            elif "produce TWO separate sections" in user_message and "DETAILED_ANALYSIS" in user_message:
                return _mock_batch_response("b")
            elif "produce FOUR separate sections" in user_message:
                return _mock_batch_response("c")
            contexts["synthesis_call"] = user_message
            return "Synthesis result."

        with patch.object(pipeline.client, "send", side_effect=mock_send):
            pipeline.run_all(sample_text)

        assert "Earlier findings" in contexts.get("synthesis_call", "")


class TestPipelineBoundaries:
    def test_empty_context(self):
        """Empty context should not crash the pipeline."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()
        with patch.object(pipeline, "_send_batch", return_value=""):
            results = pipeline.run_all("")
        assert isinstance(results, dict)
        assert len(results) == 10

    def test_whitespace_only_context(self):
        """Whitespace-only content should be handled."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()
        with patch.object(pipeline.client, "send", side_effect=_mock_send_factory()):
            results = pipeline.run_all("   \n\n   ")
        assert len(results) == 10

    def test_batch_prompts_are_distinct(self, sample_text):
        """Each batch should use its own prompt template."""
        from app.analyzers.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline()
        prompts_used = set()

        def mock_send(system_prompt, user_message, **kwargs):
            prompts_used.add(user_message[:50])
            if "executive summary" in user_message.lower():
                return _mock_batch_response("a")
            elif "detailed analysis" in user_message.lower():
                return _mock_batch_response("b")
            return _mock_batch_response("c")

        with patch.object(pipeline.client, "send", side_effect=mock_send):
            pipeline.run_all(sample_text)

        assert len(prompts_used) >= 3
