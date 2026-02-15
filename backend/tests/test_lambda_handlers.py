"""
Tests for Lambda handlers.

Covers:
    - lambda_vibe_check.py (Vibe Check processing)
    - lambda_refine_profile.py (Profile refinement)
    - lambda_generate_briefing.py (Briefing generation)
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from backend.lambda_vibe_check import lambda_handler as vibe_check_handler
from backend.lambda_refine_profile import lambda_handler as refine_profile_handler
from backend.lambda_generate_briefing import lambda_handler as generate_briefing_handler


class TestVibeCheckHandler:
    """Test suite for lambda_vibe_check.py"""

    def _make_event(self, body):
        """Create a mock API Gateway event."""
        return {"body": json.dumps(body)}

    @patch("backend.lambda_vibe_check.Orchestrator")
    def test_vibe_check_success(self, mock_orchestrator_class):
        """Valid input should return profile."""
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_vibe_check.return_value = "You're approaching AI with curiosity..."
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create event
        event = self._make_event({
            "vibe_check_responses": {
                "skepticism": "Curious but haven't started",
                "goal": "Understand what AI is",
                "learning_style": "Reading at own pace",
                "context": "Business",
            }
        })

        # Call handler
        response = vibe_check_handler(event, None)

        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "profile" in body
        assert body["profile"] == "You're approaching AI with curiosity..."

    def test_vibe_check_missing_field(self):
        """Missing required field should return 400."""
        event = self._make_event({
            "vibe_check_responses": {
                "skepticism": "Curious",
                "goal": "Learn AI",
                # Missing learning_style and context
            }
        })

        response = vibe_check_handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "Missing required fields" in body["error"]

    def test_vibe_check_empty_field(self):
        """Empty field should return 400."""
        event = self._make_event({
            "vibe_check_responses": {
                "skepticism": "Curious",
                "goal": "",  # Empty
                "learning_style": "Reading",
                "context": "Business",
            }
        })

        response = vibe_check_handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "Empty fields not allowed" in body["error"]

    @patch("backend.lambda_vibe_check.Orchestrator")
    def test_vibe_check_orchestrator_error(self, mock_orchestrator_class):
        """Orchestrator error should return 500."""
        # Mock orchestrator to raise error
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_vibe_check.side_effect = Exception("Bedrock timeout")
        mock_orchestrator_class.return_value = mock_orchestrator

        event = self._make_event({
            "vibe_check_responses": {
                "skepticism": "Curious",
                "goal": "Learn AI",
                "learning_style": "Reading",
                "context": "Business",
            }
        })

        response = vibe_check_handler(event, None)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body

    @patch("backend.lambda_vibe_check.Orchestrator")
    def test_vibe_check_cors_headers(self, mock_orchestrator_class):
        """Response should include CORS headers."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_vibe_check.return_value = "Profile"
        mock_orchestrator_class.return_value = mock_orchestrator

        event = self._make_event({
            "vibe_check_responses": {
                "skepticism": "Curious",
                "goal": "Learn AI",
                "learning_style": "Reading",
                "context": "Business",
            }
        })

        response = vibe_check_handler(event, None)

        assert "headers" in response
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_vibe_check_invalid_json(self):
        """Invalid JSON should return 400."""
        event = {"body": "not valid json{"}

        response = vibe_check_handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body


class TestRefineProfileHandler:
    """Test suite for lambda_refine_profile.py"""

    def _make_event(self, body):
        """Create a mock API Gateway event."""
        return {"body": json.dumps(body)}

    @patch("backend.lambda_refine_profile.Orchestrator")
    def test_refine_success(self, mock_orchestrator_class):
        """Valid input should return revised profile."""
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_refinement.return_value = "You're approaching AI with hands-on curiosity..."
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create event
        event = self._make_event({
            "original_profile": "You're approaching AI with curiosity...",
            "user_correction": "Actually I'm more hands-on",
        })

        # Call handler
        response = refine_profile_handler(event, None)

        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "profile" in body
        assert "hands-on" in body["profile"]

    def test_refine_missing_original(self):
        """Missing original_profile should return 400."""
        event = self._make_event({
            "user_correction": "I'm more hands-on",
        })

        response = refine_profile_handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "original_profile" in body["error"]

    def test_refine_empty_correction(self):
        """Empty user_correction should return 400."""
        event = self._make_event({
            "original_profile": "You're approaching AI...",
            "user_correction": "",
        })

        response = refine_profile_handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "user_correction" in body["error"]

    @patch("backend.lambda_refine_profile.Orchestrator")
    def test_refine_orchestrator_error(self, mock_orchestrator_class):
        """Orchestrator error should return 500."""
        # Mock orchestrator to raise error
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_refinement.side_effect = Exception("Navigator error")
        mock_orchestrator_class.return_value = mock_orchestrator

        event = self._make_event({
            "original_profile": "You're approaching AI...",
            "user_correction": "I'm more hands-on",
        })

        response = refine_profile_handler(event, None)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body

    @patch("backend.lambda_refine_profile.Orchestrator")
    def test_refine_cors_headers(self, mock_orchestrator_class):
        """Response should include CORS headers."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_refinement.return_value = "Revised profile"
        mock_orchestrator_class.return_value = mock_orchestrator

        event = self._make_event({
            "original_profile": "Original",
            "user_correction": "Correction",
        })

        response = refine_profile_handler(event, None)

        assert "headers" in response
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"


class TestGenerateBriefingHandler:
    """Test suite for lambda_generate_briefing.py"""

    def _make_event(self, body):
        """Create a mock API Gateway event."""
        return {"body": json.dumps(body)}

    @patch("backend.lambda_generate_briefing.generate_command_briefing")
    @patch("backend.lambda_generate_briefing.Orchestrator")
    def test_generate_briefing_success(self, mock_orchestrator_class, mock_pdf_gen):
        """Valid input should return learning path and PDF URL."""
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.generate_briefing.return_value = {
            "learning_path": [
                {
                    "resource_id": "elements-ai-intro",
                    "resource_name": "Introduction to AI",
                    "provider": "University of Helsinki",
                    "sequence": 1,
                    "reasoning": "Perfect starting point",
                    "estimated_hours": 30,
                    "resource_url": "https://course.elementsofai.com/",
                }
            ],
            "total_hours": 30,
            "next_steps": "After completing...",
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Mock PDF generator
        mock_pdf_gen.return_value = "https://s3.amazonaws.com/bucket/briefing-abc123.pdf"

        # Create event
        event = self._make_event({
            "approved_profile": "You're approaching AI with curiosity...",
        })

        # Call handler
        response = generate_briefing_handler(event, None)

        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "learning_path" in body
        assert "pdf_url" in body
        assert body["pdf_url"] == "https://s3.amazonaws.com/bucket/briefing-abc123.pdf"

    def test_generate_briefing_missing_profile(self):
        """Missing approved_profile should return 400."""
        event = self._make_event({})

        response = generate_briefing_handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "approved_profile" in body["error"]

    def test_generate_briefing_empty_profile(self):
        """Empty approved_profile should return 400."""
        event = self._make_event({
            "approved_profile": "",
        })

        response = generate_briefing_handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body

    @patch("backend.lambda_generate_briefing.Orchestrator")
    def test_generate_briefing_scout_error(self, mock_orchestrator_class):
        """Scout error should return 500."""
        # Mock orchestrator to return error
        mock_orchestrator = MagicMock()
        mock_orchestrator.generate_briefing.return_value = {
            "error": "scout_failed",
            "message": "Failed to load resources",
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        event = self._make_event({
            "approved_profile": "You're approaching AI...",
        })

        response = generate_briefing_handler(event, None)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body

    @patch("backend.lambda_generate_briefing.generate_command_briefing")
    @patch("backend.lambda_generate_briefing.Orchestrator")
    def test_generate_briefing_pdf_error(self, mock_orchestrator_class, mock_pdf_gen):
        """PDF generation error should still return path (graceful degradation)."""
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.generate_briefing.return_value = {
            "learning_path": [{"resource_id": "test"}],
            "total_hours": 30,
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Mock PDF generator to raise error
        mock_pdf_gen.side_effect = Exception("WeasyPrint error")

        event = self._make_event({
            "approved_profile": "You're approaching AI...",
        })

        response = generate_briefing_handler(event, None)

        # Should still return 200 with path, but no PDF URL
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "learning_path" in body
        assert body["pdf_url"] is None
        assert "pdf_error" in body

    @patch("backend.lambda_generate_briefing.generate_command_briefing")
    @patch("backend.lambda_generate_briefing.Orchestrator")
    def test_generate_briefing_cors_headers(self, mock_orchestrator_class, mock_pdf_gen):
        """Response should include CORS headers."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.generate_briefing.return_value = {
            "learning_path": [],
            "total_hours": 0,
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_pdf_gen.return_value = "https://s3.amazonaws.com/test.pdf"

        event = self._make_event({
            "approved_profile": "Profile",
        })

        response = generate_briefing_handler(event, None)

        assert "headers" in response
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
