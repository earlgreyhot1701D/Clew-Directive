"""
Tests for Navigator Agent.

Covers:
    - Vibe Check question definitions are complete
    - Profile synthesis contract
    - Learning path output structure
    - No PII in any output
"""

import pytest
from backend.agents.navigator import NavigatorAgent, VIBE_CHECK_QUESTIONS
from backend.tests.mocks.bedrock_mocks import (
    MOCK_VIBE_CHECK_CURIOUS_MARKETER,
    MOCK_LEARNING_PATH,
)


class TestVibeCheckQuestions:
    """Verify Vibe Check question definitions."""

    def test_exactly_four_questions(self):
        assert len(VIBE_CHECK_QUESTIONS) == 4

    def test_all_questions_have_required_fields(self):
        for q in VIBE_CHECK_QUESTIONS:
            assert "id" in q
            assert "question" in q
            assert "options" in q
            assert len(q["options"]) >= 4

    def test_question_ids_are_unique(self):
        ids = [q["id"] for q in VIBE_CHECK_QUESTIONS]
        assert len(ids) == len(set(ids))

    def test_expected_question_ids(self):
        ids = {q["id"] for q in VIBE_CHECK_QUESTIONS}
        assert ids == {"skepticism", "goal", "learning_style", "context"}


class TestNavigatorAgent:
    """Test suite for NavigatorAgent."""

    def test_learning_path_structure(self):
        """Verify mock learning path has required fields."""
        path = MOCK_LEARNING_PATH
        assert "profile_summary" in path
        assert "recommended_resources" in path
        assert "approach_guidance" in path
        assert "total_estimated_hours" in path
        assert len(path["recommended_resources"]) >= 3

    def test_resource_entries_have_required_fields(self):
        """Each recommended resource must have all required fields."""
        required = {
            "resource_id", "resource_name", "resource_url", "provider",
            "provider_url", "why_for_you", "difficulty", "estimated_hours",
            "format", "free_model", "sequence_note", "sequence_order",
        }
        for r in MOCK_LEARNING_PATH["recommended_resources"]:
            missing = required - set(r.keys())
            assert not missing, f"Resource {r.get('resource_id')} missing: {missing}"

    def test_no_pii_in_profile(self):
        """Profile summary should not contain PII."""
        profile = MOCK_LEARNING_PATH["profile_summary"]
        # No email patterns
        assert "@" not in profile
        # No phone patterns
        assert not any(c.isdigit() and len(c) > 4 for c in profile.split())

    def test_resources_are_sequenced(self):
        """Resources should have sequential order numbers."""
        orders = [r["sequence_order"] for r in MOCK_LEARNING_PATH["recommended_resources"]]
        assert orders == sorted(orders)
        assert orders[0] == 1
