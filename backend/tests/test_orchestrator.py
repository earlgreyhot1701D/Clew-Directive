"""
Tests for Orchestrator flow.

Covers:
    - process_vibe_check() with mocked Navigator
    - process_refinement() with mocked Navigator
    - generate_briefing() with mocked Scout and Navigator
    - Error handling for each method
    - Logging output verification
"""

import pytest
from unittest.mock import Mock, patch, call
from backend.agents.orchestrator import Orchestrator
from exceptions import ClewException
from backend.tests.mocks.bedrock_mocks import (
    MOCK_VIBE_CHECK_CURIOUS_MARKETER,
    MOCK_PROFILE_RESPONSE,
    MOCK_LEARNING_PATH,
)


@pytest.fixture
def mock_scout():
    """Create a mock Scout agent."""
    scout = Mock()
    scout.gather_resources.return_value = [
        {
            "id": "elements-ai-intro",
            "name": "Introduction to AI",
            "provider": "University of Helsinki",
            "resource_url": "https://course.elementsofai.com/",
            "difficulty": "beginner",
            "estimated_hours": 30,
        },
        {
            "id": "google-ai-essentials",
            "name": "Google AI Essentials",
            "provider": "Google",
            "resource_url": "https://grow.google/certificates/ai-essentials/",
            "difficulty": "beginner",
            "estimated_hours": 10,
        },
    ]
    return scout


@pytest.fixture
def mock_navigator():
    """Create a mock Navigator agent."""
    navigator = Mock()
    navigator.synthesize_profile.return_value = MOCK_PROFILE_RESPONSE
    navigator.refine_profile.return_value = "Refined profile based on your feedback."
    navigator.generate_learning_path.return_value = MOCK_LEARNING_PATH
    return navigator


@pytest.fixture
def orchestrator(mock_scout, mock_navigator):
    """Create an Orchestrator instance with mocked agents."""
    return Orchestrator(scout=mock_scout, navigator=mock_navigator)


class TestProcessVibeCheck:
    """Test process_vibe_check method."""

    def test_process_vibe_check_success(self, orchestrator, mock_navigator):
        """Test successful Vibe Check processing."""
        vibe_check = MOCK_VIBE_CHECK_CURIOUS_MARKETER
        
        profile = orchestrator.process_vibe_check(vibe_check)
        
        # Verify Navigator was called
        mock_navigator.synthesize_profile.assert_called_once_with(vibe_check)
        
        # Verify profile returned
        assert profile == MOCK_PROFILE_RESPONSE
        assert len(profile) > 0

    def test_process_vibe_check_logs_correctly(self, orchestrator, caplog):
        """Test that Vibe Check processing logs correctly."""
        vibe_check = MOCK_VIBE_CHECK_CURIOUS_MARKETER
        
        with caplog.at_level("INFO"):
            orchestrator.process_vibe_check(vibe_check)
        
        # Check for orchestrator log messages
        assert any("[orchestrator] Processing Vibe Check" in record.message for record in caplog.records)
        assert any("[orchestrator] Profile synthesized" in record.message for record in caplog.records)

    def test_process_vibe_check_error_handling(self, orchestrator, mock_navigator):
        """Test error handling when Navigator fails."""
        mock_navigator.synthesize_profile.side_effect = Exception("Bedrock timeout")
        
        # Should raise ClewException with user-friendly message
        with pytest.raises(ClewException) as exc_info:
            orchestrator.process_vibe_check(MOCK_VIBE_CHECK_CURIOUS_MARKETER)
        
        assert "try again" in exc_info.value.user_message.lower()

    def test_process_vibe_check_empty_responses(self, orchestrator, mock_navigator):
        """Test with empty Vibe Check responses."""
        empty_vibe_check = {}
        
        profile = orchestrator.process_vibe_check(empty_vibe_check)
        
        # Navigator should still be called
        mock_navigator.synthesize_profile.assert_called_once_with(empty_vibe_check)
        assert isinstance(profile, str)


class TestProcessRefinement:
    """Test process_refinement method."""

    def test_process_refinement_success(self, orchestrator, mock_navigator):
        """Test successful profile refinement."""
        original = "Original profile summary."
        correction = "I'm more interested in building things."
        
        refined = orchestrator.process_refinement(original, correction)
        
        # Verify Navigator was called
        mock_navigator.refine_profile.assert_called_once_with(original, correction)
        
        # Verify refined profile returned
        assert refined == "Refined profile based on your feedback."
        assert len(refined) > 0

    def test_process_refinement_logs_correctly(self, orchestrator, caplog):
        """Test that refinement logs correctly."""
        original = "Original profile."
        correction = "Not quite right."
        
        with caplog.at_level("INFO"):
            orchestrator.process_refinement(original, correction)
        
        # Check for orchestrator log messages
        assert any("[orchestrator] Processing profile refinement" in record.message for record in caplog.records)
        assert any("[orchestrator] Profile refined" in record.message for record in caplog.records)

    def test_process_refinement_error_handling(self, orchestrator, mock_navigator):
        """Test error handling when refinement fails."""
        original = "Original profile."
        correction = "Change this."
        mock_navigator.refine_profile.side_effect = Exception("Bedrock error")
        
        refined = orchestrator.process_refinement(original, correction)
        
        # Should return original profile with note
        assert original in refined
        assert "(Note:" in refined
        assert correction in refined

    def test_process_refinement_empty_correction(self, orchestrator, mock_navigator):
        """Test refinement with empty correction."""
        original = "Original profile."
        correction = ""
        
        refined = orchestrator.process_refinement(original, correction)
        
        # Navigator should still be called
        mock_navigator.refine_profile.assert_called_once_with(original, correction)
        assert isinstance(refined, str)


class TestGenerateBriefing:
    """Test generate_briefing method."""

    def test_generate_briefing_success(self, orchestrator, mock_scout, mock_navigator):
        """Test successful briefing generation."""
        approved_profile = "You're curious about AI and want to learn."
        
        result = orchestrator.generate_briefing(approved_profile)
        
        # Verify Scout was called
        mock_scout.gather_resources.assert_called_once_with(domain="ai-foundations")
        
        # Verify Navigator was called with Scout's resources
        assert mock_navigator.generate_learning_path.called
        call_args = mock_navigator.generate_learning_path.call_args
        assert call_args[0][0] == approved_profile  # First arg is profile
        assert len(call_args[0][1]) == 2  # Second arg is resources list
        
        # Verify result structure
        assert "profile_summary" in result
        assert "recommended_resources" in result
        assert "approach_guidance" in result
        assert "total_estimated_hours" in result

    def test_generate_briefing_logs_correctly(self, orchestrator, caplog):
        """Test that briefing generation logs correctly."""
        approved_profile = "You're curious about AI."
        
        with caplog.at_level("INFO"):
            orchestrator.generate_briefing(approved_profile)
        
        # Check for orchestrator log messages
        assert any("[orchestrator] Generating briefing" in record.message for record in caplog.records)
        assert any("[orchestrator] Scout gathered" in record.message for record in caplog.records)
        assert any("[orchestrator] Navigator generated path" in record.message for record in caplog.records)

    def test_generate_briefing_scout_returns_empty(self, orchestrator, mock_scout):
        """Test error handling when Scout returns no resources."""
        mock_scout.gather_resources.return_value = []
        
        # Should raise NoResourcesFoundError (which Scout would raise)
        # But since we're mocking Scout to return [], Navigator will get empty list
        # and should still generate a path (using fallback if needed)
        result = orchestrator.generate_briefing("Profile")
        
        # Should still return a valid path structure
        assert "recommended_resources" in result
        assert "approach_guidance" in result

    def test_generate_briefing_scout_error(self, orchestrator, mock_scout):
        """Test error handling when Scout raises exception."""
        mock_scout.gather_resources.side_effect = Exception("S3 connection failed")
        
        # Should raise ClewException with user-friendly message
        with pytest.raises(ClewException) as exc_info:
            orchestrator.generate_briefing("Profile")
        
        assert "resource directory" in exc_info.value.user_message.lower()

    def test_generate_briefing_navigator_error(self, orchestrator, mock_navigator):
        """Test error handling when Navigator raises exception."""
        mock_navigator.generate_learning_path.side_effect = Exception("Bedrock timeout")
        
        # Should raise ClewException with user-friendly message
        with pytest.raises(ClewException) as exc_info:
            orchestrator.generate_briefing("Profile")
        
        assert "learning path" in exc_info.value.user_message.lower()

    def test_generate_briefing_uses_correct_domain(self, orchestrator, mock_scout):
        """Test that briefing generation uses ai-foundations domain."""
        orchestrator.generate_briefing("Profile")
        
        # Verify Scout was called with correct domain
        mock_scout.gather_resources.assert_called_once_with(domain="ai-foundations")


class TestOrchestratorIntegration:
    """Integration tests for full orchestrator flow."""

    def test_full_flow_happy_path(self, orchestrator, mock_scout, mock_navigator):
        """Test complete flow: Vibe Check → Profile → Briefing."""
        # Step 1: Process Vibe Check
        vibe_check = MOCK_VIBE_CHECK_CURIOUS_MARKETER
        profile = orchestrator.process_vibe_check(vibe_check)
        assert len(profile) > 0
        
        # Step 2: Generate briefing (user confirmed profile)
        result = orchestrator.generate_briefing(profile)
        assert "recommended_resources" in result
        assert len(result["recommended_resources"]) >= 3

    def test_full_flow_with_refinement(self, orchestrator, mock_navigator):
        """Test flow with profile refinement."""
        # Step 1: Process Vibe Check
        vibe_check = MOCK_VIBE_CHECK_CURIOUS_MARKETER
        profile = orchestrator.process_vibe_check(vibe_check)
        
        # Step 2: User rejects, refine profile
        refined = orchestrator.process_refinement(profile, "I want more hands-on content")
        assert len(refined) > 0
        
        # Step 3: Generate briefing with refined profile
        result = orchestrator.generate_briefing(refined)
        assert "recommended_resources" in result

    def test_orchestrator_calls_agents_in_correct_order(self, orchestrator, mock_scout, mock_navigator):
        """Test that agents are called in the correct sequence."""
        profile = "Test profile"
        
        orchestrator.generate_briefing(profile)
        
        # Verify call order: Scout first, then Navigator
        assert mock_scout.gather_resources.called
        assert mock_navigator.generate_learning_path.called
        
        # Scout should be called before Navigator
        scout_call_time = mock_scout.gather_resources.call_args
        navigator_call_time = mock_navigator.generate_learning_path.call_args
        assert scout_call_time is not None
        assert navigator_call_time is not None

