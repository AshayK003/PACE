from app.analyzers.parser import parse_batched_response, batch_a_response, batch_b_response, batch_c_response


class TestBatchedResponseParser:
    def test_parse_batch_a(self):
        response = "===EXECUTIVE_SUMMARY===\nSummary here.\n===KEY_TAKEAWAYS===\nTakeaway here."
        result = batch_a_response(response)
        assert result["executive_summary"] == "Summary here."
        assert result["key_takeaways"] == "Takeaway here."

    def test_parse_batch_b(self):
        response = "===DETAILED_ANALYSIS===\nAnalysis here.\n===SUPPORTING_EVIDENCE===\nEvidence here."
        result = batch_b_response(response)
        assert result["detailed_analysis"] == "Analysis here."
        assert result["supporting_evidence"] == "Evidence here."

    def test_parse_batch_c(self):
        response = (
            "===FRAMEWORKS===\nFrameworks here.\n"
            "===ACTION_ITEMS===\nActions here.\n"
            "===RISKS===\nRisks here.\n"
            "===NOTABLE_QUOTES===\nQuotes here."
        )
        result = batch_c_response(response)
        assert result["frameworks"] == "Frameworks here."
        assert result["action_items"] == "Actions here."
        assert result["risks"] == "Risks here."
        assert result["notable_quotes"] == "Quotes here."

    def test_missing_sections_get_empty_string(self):
        response = "===EXECUTIVE_SUMMARY===\nSummary."
        result = batch_a_response(response)
        assert result["executive_summary"] == "Summary."
        assert result["key_takeaways"] == ""

    def test_extra_whitespace_handled(self):
        response = "===EXECUTIVE_SUMMARY===\n  Summary  \n===KEY_TAKEAWAYS===\n  Takeaway  "
        result = batch_a_response(response)
        assert result["executive_summary"] == "Summary"
        assert result["key_takeaways"] == "Takeaway"

    def test_empty_response(self):
        result = batch_a_response("")
        assert result["executive_summary"] == ""
        assert result["key_takeaways"] == ""

    def test_multiline_content(self):
        response = "===EXECUTIVE_SUMMARY===\nLine 1\nLine 2\nLine 3\n===KEY_TAKEAWAYS===\n- Item 1\n- Item 2"
        result = batch_a_response(response)
        assert "Line 1\nLine 2\nLine 3" in result["executive_summary"]
        assert "- Item 1\n- Item 2" in result["key_takeaways"]

    def test_custom_parse(self):
        response = "===FOO===\nFoo content.\n===BAR===\nBar content."
        result = parse_batched_response(response, ["foo", "bar"])
        assert result["foo"] == "Foo content."
        assert result["bar"] == "Bar content."

    def test_unknown_sections_ignored(self):
        response = "===EXECUTIVE_SUMMARY===\nSummary.\n===UNKNOWN===\nUnknown."
        result = batch_a_response(response)
        assert result["executive_summary"] == "Summary."
        assert "unknown" not in result
