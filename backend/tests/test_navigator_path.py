"""
Tests for Navigator Agent learning path generation.

Covers:
    - Path generation with mocked Strands responses
    - JSON parsing and validation
    - Fallback behavior on errors
    - Resource selection and sequencing
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.agents.navigator import NavigatorAgent
from backend.tests.mocks.bedrock_mocks import (
    MOCK_VIBE_CHECK_CURIOUS_MARKETER,
    MOCK_LEARNING_PATH,
)


# Mock verified resources from Scout
MOCK_VERIFIED_RESOURCES = [
    {
        "id": "elements-ai-intro",
        "name": "Introduction to AI",
        "provider": "University of Helsinki / MinnaLearn",
        "provider_url": "https://www.elementsofai.com/",
        "resource_url": "https://course.elementsofai.com/",
        "authority_tier": 1,
        "free_model": "Fully free",
        "category": "foundations",
        "difficulty": "beginner",
        "estimated_hours": 30,
        "format": "course",
        "prerequisites": [],
        "tags": ["non-technical", "conceptual", "self-paced"],
        "description": "Foundational AI concepts for everyone",
        "best_for": "Complete beginners, skeptics",
        "last_verified": "2026-02-15T00:00:00Z",
        "status": "active",
    },
    {
        "id": "google-ai-essentials",
        "name": "Google AI Essentials",
        "provider": "Google / Grow with Google",
        "provider_url": "https://grow.google/",
        "resource_url": "https://grow.google/certificates/ai-essentials/",
        "authority_tier": 2,
        "free_model": "Fully free",
        "category": "foundations",
        "difficulty": "beginner",
        "estimated_hours": 10,
        "format": "course",
        "prerequisites": [],
        "tags": ["practical", "hands-on", "google"],
        "description": "Practical AI skills for everyday work",
        "best_for": "Business professionals wanting practical skills",
        "last_verified": "2026-02-15T00:00:00Z",
        "status": "active",
    },
    {
        "id": "google-prompting-essentials",
        "name": "Google Prompting Essentials",
        "provider": "Google / Grow with Google",
        "provider_url": "https://grow.google/",
        "resource_url": "https://grow.google/certificates/prompting-essentials/",
        "authority_tier": 2,
        "free_model": "Fully free",
        "category": "prompting",
        "difficulty": "beginner",
        "estimated_hours": 5,
        "format": "course",
        "prerequisites": [],
        "tags": ["prompting", "practical", "google"],
        "description": "Master prompt engineering fundamentals",
        "best_for": "Anyone using AI tools regularly",
        "last_verified": "2026-02-15T00:00:00Z",
        "status": "active",
    },
    {
        "id": "fast-ai-course",
        "name": "Practical Deep Learning for Coders",
        "provider": "fast.ai",
        "provider_url": "https://www.fast.ai/",
        "resource_url": "https://course.fast.ai/",
        "authority_tier": 2,
        "free_model": "Fully free",
        "category": "deep-learning",
        "difficulty": "intermediate",
        "estimated_hours": 40,
        "format": "course",
        "prerequisites": ["basic-python"],
        "tags": ["deep-learning", "hands-on", "coding"],
        "description": "Top-down approach to deep learning",
        "best_for": "Developers wanting to build AI models",
        "last_verified": "2026-02-15T00:00:00Z",
        "status": "active",
    },
]


@pytest.fixture
def navigator():
    """Create a Navigator agent instance."""
    return NavigatorAgent()


@pytest.fixture
def mock_strands_response():
    """Mock Strands agent response for path generation."""
    # Create a mock response that looks like what Strands returns
    mock_response = Mock()
    
    # Build the JSON response (without profile_summary, Navigator adds that)
    path_json = {
        "recommended_resources": MOCK_LEARNING_PATH["recommended_resources"],
        "approach_guidance": MOCK_LEARNING_PATH["approach_guidance"],
        "total_estimated_hours": MOCK_LEARNING_PATH["total_estimated_hours"],
    }
    
    mock_response.output = json.dumps(path_json)
    return mock_response


def test_generate_learning_path_basic(navigator, mock_strands_response):
    """Test basic path generation with mocked Strands response."""
    profile = "You're curious about AI and want to learn."
    
    # Mock the agent's invoke_async method
    with patch.object(navigator.agent, 'invoke_async', new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_strands_response
        
        path = navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)
        
        # Verify structure
        assert "profile_summary" in path
        assert path["profile_summary"] == profile
        assert "recommended_resources" in path
        assert "approach_guidance" in path
        assert "total_estimated_hours" in path
        
        # Verify resources
        assert len(path["recommended_resources"]) >= 3
        assert all("why_for_you" in r for r in path["recommended_resources"])


def test_generate_learning_path_with_markdown_json(navigator):
    """Test parsing JSON wrapped in markdown code blocks."""
    profile = "You're curious about AI."
    
    # Mock response with markdown code blocks
    mock_response = Mock()
    path_json = {
        "recommended_resources": MOCK_LEARNING_PATH["recommended_resources"][:3],
        "approach_guidance": "Start with the basics.",
        "total_estimated_hours": 45,
    }
    mock_response.output = f"```json\n{json.dumps(path_json)}\n```"
    
    with patch.object(navigator.agent, 'invoke_async', new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_response
        
        path = navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)
        
        assert "recommended_resources" in path
        assert len(path["recommended_resources"]) == 3


def test_generate_learning_path_invalid_json_fallback(navigator):
    """Test fallback when Strands returns invalid JSON."""
    profile = "You're curious about AI."
    
    # Mock response with invalid JSON
    mock_response = Mock()
    mock_response.output = "This is not valid JSON at all!"
    
    # Mock the agent __call__ method (used by ThreadPoolExecutor)
    with patch.object(navigator.agent, '__call__', return_value=mock_response):
        path = navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)
        
        # Should use fallback
        assert "recommended_resources" in path
        assert len(path["recommended_resources"]) == 4  # Fallback picks 4
        assert path["profile_summary"] == profile


def test_generate_learning_path_exception_fallback(navigator):
    """Test fallback when Strands call raises exception."""
    profile = "You're curious about AI."
    
    # Mock the agent __call__ method to raise exception
    with patch.object(navigator.agent, '__call__', side_effect=Exception("Bedrock timeout")):
        path = navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)
        
        # Should use fallback
        assert "recommended_resources" in path
        assert len(path["recommended_resources"]) == 4
        assert "approach_guidance" in path


def test_fallback_learning_path_structure(navigator):
    """Test that fallback path has correct structure."""
    profile = "You're curious about AI."
    
    path = navigator._fallback_learning_path(profile, MOCK_VERIFIED_RESOURCES)
    
    # Verify all required fields
    assert path["profile_summary"] == profile
    assert len(path["recommended_resources"]) == 4
    assert path["total_estimated_hours"] > 0
    assert path["approach_guidance"]
    
    # Verify resource fields
    for r in path["recommended_resources"]:
        assert "resource_id" in r
        assert "resource_name" in r
        assert "resource_url" in r
        assert "provider" in r
        assert "provider_url" in r
        assert "why_for_you" in r
        assert "sequence_order" in r


def test_fallback_selects_high_authority_resources(navigator):
    """Test that fallback prioritizes high authority tier resources."""
    profile = "You're curious about AI."
    
    path = navigator._fallback_learning_path(profile, MOCK_VERIFIED_RESOURCES)
    
    # First resource should be authority tier 1 (elements-ai-intro)
    first_resource = path["recommended_resources"][0]
    assert first_resource["resource_id"] == "elements-ai-intro"


def test_format_resource_catalog(navigator):
    """Test resource catalog formatting for prompt."""
    catalog = navigator._format_resource_catalog(MOCK_VERIFIED_RESOURCES[:2])
    
    # Should contain key information
    assert "elements-ai-intro" in catalog
    assert "University of Helsinki" in catalog
    assert "Authority Tier: 1" in catalog
    assert "Difficulty: beginner" in catalog


def test_validate_learning_path_valid(navigator):
    """Test validation of a valid learning path."""
    valid_path = {
        "recommended_resources": MOCK_LEARNING_PATH["recommended_resources"],
        "approach_guidance": "Start here.",
        "total_estimated_hours": 45,
    }
    
    assert navigator._validate_learning_path(valid_path) is True


def test_validate_learning_path_missing_fields(navigator):
    """Test validation fails with missing fields."""
    invalid_path = {
        "recommended_resources": [],
        # Missing approach_guidance and total_estimated_hours
    }
    
    assert navigator._validate_learning_path(invalid_path) is False


def test_validate_learning_path_incomplete_resource(navigator):
    """Test validation fails with incomplete resource."""
    invalid_path = {
        "recommended_resources": [
            {
                "resource_id": "test",
                # Missing many required fields
            }
        ],
        "approach_guidance": "Start here.",
        "total_estimated_hours": 10,
    }
    
    assert navigator._validate_learning_path(invalid_path) is False


def test_path_includes_profile_summary(navigator, mock_strands_response):
    """Test that generated path includes the profile summary."""
    profile = "You're a curious learner."
    
    with patch.object(navigator.agent, 'invoke_async', new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_strands_response
        
        path = navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)
        
        assert path["profile_summary"] == profile
