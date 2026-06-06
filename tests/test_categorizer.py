import json
from unittest.mock import MagicMock

import pytest


class TestCategorizeContent:
    def test_valid_llm_response(self):
        from app.analyzers.categorizer import categorize_content
        client = MagicMock()
        client.send.return_value = json.dumps({
            "domain": "Tech",
            "sub_topic": "Machine_Learning",
            "slug": "transformer_architecture_explained",
        })
        result = categorize_content(
            client, "Transformer Architecture", ["Explains attention"], "Deep Learning",
        )
        assert result["domain"] == "Tech"
        assert result["sub_topic"] == "Machine_Learning"
        assert result["slug"] == "transformer_architecture_explained"

    def test_invalid_domain_falls_back_to_other(self):
        from app.analyzers.categorizer import categorize_content
        client = MagicMock()
        client.send.return_value = json.dumps({
            "domain": "QuantumPhysics",
            "sub_topic": "Entanglement",
            "slug": "quantum_entanglement",
        })
        result = categorize_content(client, "Quantum", [], "Physics")
        assert result["domain"] == "Other"

    def test_malformed_json_falls_back(self):
        from app.analyzers.categorizer import categorize_content
        client = MagicMock()
        client.send.return_value = "This is not JSON at all"
        result = categorize_content(client, "Title", ["takeaway"], "topic")
        assert result["domain"] == "Other"
        assert result["sub_topic"] == "Unsorted"
        assert result["slug"] == "report"

    def test_api_exception_falls_back(self):
        from app.analyzers.categorizer import categorize_content
        client = MagicMock()
        client.send.side_effect = Exception("API error")
        result = categorize_content(client, "Title", [], "topic")
        assert result["domain"] == "Other"

    def test_empty_response_falls_back(self):
        from app.analyzers.categorizer import categorize_content
        client = MagicMock()
        client.send.return_value = ""
        result = categorize_content(client, "Title", [], "topic")
        assert result["domain"] == "Other"

    def test_json_with_extra_text(self):
        from app.analyzers.categorizer import categorize_content
        client = MagicMock()
        client.send.return_value = 'Here is the categorization:\n{"domain": "Health", "sub_topic": "Nutrition", "slug": "keto_diet_guide"}\nDone.'
        result = categorize_content(client, "Keto Diet", [], "Health")
        assert result["domain"] == "Health"
        assert result["slug"] == "keto_diet_guide"

    def test_slug_truncation(self):
        from app.analyzers.categorizer import categorize_content
        client = MagicMock()
        client.send.return_value = json.dumps({
            "domain": "Business",
            "sub_topic": "Marketing",
            "slug": "a_very_long_slug_that_exceeds_the_maximum_length_allowed",
        })
        result = categorize_content(client, "Title", [], "topic")
        assert len(result["slug"]) <= 60

    def test_sub_topic_max_length(self):
        from app.analyzers.categorizer import categorize_content
        client = MagicMock()
        client.send.return_value = json.dumps({
            "domain": "Tech",
            "sub_topic": "A" * 50,
            "slug": "short",
        })
        result = categorize_content(client, "Title", [], "topic")
        assert len(result["sub_topic"]) <= 40
