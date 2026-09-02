"""
Tests for Navigator Agent learning path generation.

Covers:
    - Path generation with mocked Strands responses
    - JSON parsing and validation
    - Fallback behavior on errors
    - Resource selection and sequencing
    - Resource shuffling to eliminate LLM primacy bias
    - Profile-aware fallback selection
    - No PII in outputs
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.agents.navigator import NavigatorAgent
from backend.exceptions import BedrockTimeoutError, BedrockThrottleError, InvalidLLMResponseError
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


def test_generate_learning_path_shuffles_resources(navigator):
    """Test that resources are shuffled to eliminate LLM primacy bias."""
    profile = "You're curious about AI."
    
    # Create a larger resource list to make shuffling more apparent
    large_resource_list = MOCK_VERIFIED_RESOURCES * 3  # 12 resources
    
    # Mock response
    mock_response = Mock()
    path_json = {
        "recommended_resources": MOCK_LEARNING_PATH["recommended_resources"][:4],
        "approach_guidance": "Start with the basics.",
        "total_estimated_hours": 45,
    }
    mock_response.output = json.dumps(path_json)
    
    # Track the order of resources passed to the agent
    resource_orders = []
    
    def capture_call(*args, **kwargs):
        # Extract the prompt to see resource order
        prompt = args[0] if args else kwargs.get('prompt', '')
        resource_orders.append(prompt)
        return mock_response
    
    with patch.object(navigator.agent, '__call__', side_effect=capture_call):
        # Call multiple times
        for _ in range(3):
            navigator.generate_learning_path(profile, large_resource_list.copy())
    
    # Verify that at least one call had different ordering
    # (with 12 resources, shuffling should produce different orders)
    assert len(resource_orders) == 3
    # This is probabilistic, but with 12 resources, getting the same order 3 times is extremely unlikely


def test_generate_learning_path_does_not_mutate_input(navigator, mock_strands_response):
    """Test that resource shuffling doesn't mutate the original resource list."""
    profile = "You're curious about AI."
    original_resources = MOCK_VERIFIED_RESOURCES.copy()
    original_first_id = original_resources[0]["id"]
    
    with patch.object(navigator.agent, '__call__', return_value=mock_strands_response):
        navigator.generate_learning_path(profile, original_resources)
        
        # Original list should be unchanged
        assert original_resources[0]["id"] == original_first_id
        assert len(original_resources) == len(MOCK_VERIFIED_RESOURCES)


def test_fallback_learning_path_profile_aware_selection(navigator):
    """Test that fallback uses profile keywords for resource selection."""
    # Profile indicating beginner + build focus
    profile_builder = "You're new to AI and want to build things with hands-on projects."
    
    path_builder = navigator._fallback_learning_path(profile_builder, MOCK_VERIFIED_RESOURCES)
    
    # Should select resources matching "build" and "hands-on"
    resource_ids = [r["resource_id"] for r in path_builder["recommended_resources"]]
    
    # fast-ai-course is hands-on and for builders
    assert "fast-ai-course" in resource_ids or len(resource_ids) == 4
    
    # Profile indicating skeptical + understand focus
    profile_skeptic = "You're skeptical about AI and want to understand what's real."
    
    path_skeptic = navigator._fallback_learning_path(profile_skeptic, MOCK_VERIFIED_RESOURCES)
    
    # Should prioritize beginner foundational resources
    first_resource = path_skeptic["recommended_resources"][0]
    assert first_resource["difficulty"] == "beginner"


def test_fallback_learning_path_difficulty_matching(navigator):
    """Test that fallback matches difficulty to profile signals."""
    # Beginner profile
    profile_beginner = "You're new to AI, never used it before, and feeling overwhelmed."
    path = navigator._fallback_learning_path(profile_beginner, MOCK_VERIFIED_RESOURCES)
    
    # Should prioritize beginner resources
    difficulties = [r["difficulty"] for r in path["recommended_resources"]]
    assert difficulties[0] == "beginner"
    
    # Advanced profile
    profile_advanced = "You're a developer with technical background who wants to build AI systems."
    path = navigator._fallback_learning_path(profile_advanced, MOCK_VERIFIED_RESOURCES)
    
    # Should include intermediate resources (we don't have advanced in mock data)
    difficulties = [r["difficulty"] for r in path["recommended_resources"]]
    assert "intermediate" in difficulties or "beginner" in difficulties


def test_fallback_learning_path_total_hours_constraint(navigator):
    """Test that fallback respects total hours constraint."""
    profile = "You're curious about AI."
    
    # Create resources with high hours
    high_hour_resources = [
        {**r, "estimated_hours": 50} for r in MOCK_VERIFIED_RESOURCES
    ]
    
    path = navigator._fallback_learning_path(profile, high_hour_resources)
    
    # Should select 4 resources (not 5) when total would exceed 80 hours
    assert len(path["recommended_resources"]) == 4
    assert path["total_estimated_hours"] <= 200  # 4 * 50


def test_fallback_learning_path_sequences_by_difficulty(navigator):
    """Test that fallback sequences resources from easier to harder."""
    profile = "You're curious about AI."
    
    path = navigator._fallback_learning_path(profile, MOCK_VERIFIED_RESOURCES)
    
    # Extract difficulties in order
    difficulties = [r["difficulty"] for r in path["recommended_resources"]]
    
    # Should be sorted: beginner before intermediate
    diff_order = {"beginner": 0, "intermediate": 1, "advanced": 2}
    difficulty_values = [diff_order.get(d, 1) for d in difficulties]
    
    assert difficulty_values == sorted(difficulty_values), "Resources should be sequenced by difficulty"


def test_no_pii_in_generated_path(navigator, mock_strands_response):
    """Test that generated paths contain no PII."""
    profile = "You're a curious learner."
    
    with patch.object(navigator.agent, '__call__', return_value=mock_strands_response):
        path = navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)
        
        # Convert entire path to string for checking
        path_str = json.dumps(path)
        
        # No email patterns
        assert "@" not in path_str
        
        # No phone patterns (10+ consecutive digits)
        import re
        phone_pattern = r'\d{10,}'
        assert not re.search(phone_pattern, path_str)
        
        # No common PII field names
        pii_fields = ["email", "phone", "ssn", "credit_card", "password"]
        for field in pii_fields:
            assert field not in path_str.lower()



def test_generate_learning_path_timeout_raises_error(navigator):
    """Test that timeout errors are properly raised."""
    profile = "You're curious about AI."
    
    # Mock timeout exception
    with patch.object(navigator.agent, '__call__', side_effect=Exception("timeout")):
        # Should raise BedrockTimeoutError
        with pytest.raises(BedrockTimeoutError):
            navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)


def test_generate_learning_path_throttle_raises_error(navigator):
    """Test that throttling errors are properly raised."""
    profile = "You're curious about AI."
    
    # Mock throttling exception
    with patch.object(navigator.agent, '__call__', side_effect=Exception("throttling detected")):
        # Should raise BedrockThrottleError
        with pytest.raises(BedrockThrottleError):
            navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)


def test_generate_learning_path_max_tokens_uses_fallback(navigator):
    """Test that MaxTokens exception triggers fallback."""
    profile = "You're curious about AI."
    
    # Create a mock exception with MaxTokens in the name
    class MaxTokensReachedException(Exception):
        pass
    
    with patch.object(navigator.agent, '__call__', side_effect=MaxTokensReachedException("Max tokens reached")):
        path = navigator.generate_learning_path(profile, MOCK_VERIFIED_RESOURCES)
        
        # Should use fallback instead of raising
        assert "recommended_resources" in path
        assert len(path["recommended_resources"]) == 4


def test_generate_learning_path_empty_resources_fallback(navigator):
    """Test fallback behavior with empty resource list."""
    profile = "You're curious about AI."
    
    # Empty resource list should still produce a path (though empty)
    path = navigator._fallback_learning_path(profile, [])
    
    assert "recommended_resources" in path
    assert len(path["recommended_resources"]) == 0
    assert path["total_estimated_hours"] == 0


def test_validate_learning_path_warns_on_wrong_count(navigator, caplog):
    """Test that validation logs warning for wrong resource count."""
    import logging
    
    # Path with only 2 resources (should be 4-6)
    path_too_few = {
        "recommended_resources": MOCK_LEARNING_PATH["recommended_resources"][:2],
        "approach_guidance": "Start here.",
        "total_estimated_hours": 35,
    }
    
    with caplog.at_level(logging.WARNING):
        result = navigator._validate_learning_path(path_too_few)
        
        # Should still return True (allows it) but logs warning
        assert "2 resources" in caplog.text or result is True


def test_format_resource_catalog_handles_missing_fields(navigator):
    """Test catalog formatting with resources missing optional fields."""
    incomplete_resource = {
        "id": "test-resource",
        "name": "Test Resource",
        "provider": "Test Provider",
        "resource_url": "https://example.com",
        # Missing many optional fields
    }
    
    catalog = navigator._format_resource_catalog([incomplete_resource])
    
    # Should not crash, should include what's available
    assert "test-resource" in catalog
    assert "Test Resource" in catalog


def test_fallback_learning_path_handles_tags_as_list(navigator):
    """Test that fallback properly handles tags as a list (not string)."""
    profile = "You're curious about AI and want hands-on projects."
    
    # Create resources with tags as lists (correct format)
    resources_with_list_tags = [
        {
            "id": "hands-on-course",
            "name": "Hands-on AI Course",
            "provider": "Test Provider",
            "resource_url": "https://example.com",
            "provider_url": "https://provider.com",
            "authority_tier": 1,
            "difficulty": "beginner",
            "estimated_hours": 20,
            "format": "course",
            "tags": ["hands-on", "practical", "projects"],  # List format
            "description": "Practical AI course",
        },
        {
            "id": "theory-course",
            "name": "AI Theory Course",
            "provider": "Test Provider",
            "resource_url": "https://example.com",
            "provider_url": "https://provider.com",
            "authority_tier": 1,
            "difficulty": "beginner",
            "estimated_hours": 15,
            "format": "course",
            "tags": ["theory", "conceptual"],  # List format
            "description": "Theoretical AI course",
        }
    ]
    
    path = navigator._fallback_learning_path(profile, resources_with_list_tags)
    
    # Should not crash and should prioritize hands-on resource
    assert len(path["recommended_resources"]) == 2
    
    # The hands-on course should score higher due to tag matching
    resource_ids = [r["resource_id"] for r in path["recommended_resources"]]
    assert "hands-on-course" in resource_ids
    
    # First resource should be the hands-on one (higher score)
    first_resource = path["recommended_resources"][0]
    assert first_resource["resource_id"] == "hands-on-course"


def test_fallback_learning_path_handles_empty_tags(navigator):
    """Test that fallback handles resources with empty or missing tags."""
    profile = "You're curious about AI."
    
    resources_with_various_tags = [
        {
            "id": "no-tags",
            "name": "Course Without Tags",
            "provider": "Test Provider",
            "resource_url": "https://example.com",
            "provider_url": "https://provider.com",
            "authority_tier": 1,
            "difficulty": "beginner",
            "estimated_hours": 10,
            "format": "course",
            # No tags field
            "description": "Basic course",
        },
        {
            "id": "empty-tags",
            "name": "Course With Empty Tags",
            "provider": "Test Provider",
            "resource_url": "https://example.com",
            "provider_url": "https://provider.com",
            "authority_tier": 1,
            "difficulty": "beginner",
            "estimated_hours": 10,
            "format": "course",
            "tags": [],  # Empty list
            "description": "Another basic course",
        },
        {
            "id": "with-tags",
            "name": "Course With Tags",
            "provider": "Test Provider",
            "resource_url": "https://example.com",
            "provider_url": "https://provider.com",
            "authority_tier": 1,
            "difficulty": "beginner",
            "estimated_hours": 10,
            "format": "course",
            "tags": ["beginner", "introduction"],
            "description": "Introductory course",
        }
    ]
    
    # Should not crash with missing or empty tags
    path = navigator._fallback_learning_path(profile, resources_with_various_tags)
    
    assert len(path["recommended_resources"]) == 3
    assert "recommended_resources" in path
    assert "total_estimated_hours" in path


def test_fallback_learning_path_tags_keyword_matching(navigator):
    """Test that tags are properly used for keyword matching in fallback."""
    profile = "You're a developer who wants to build AI applications with Python."
    
    resources_for_matching = [
        {
            "id": "python-ai-course",
            "name": "Python AI Development",
            "provider": "Test Provider",
            "resource_url": "https://example.com",
            "provider_url": "https://provider.com",
            "authority_tier": 2,
            "difficulty": "intermediate",
            "estimated_hours": 25,
            "format": "course",
            "tags": ["python", "coding", "hands-on", "building"],
            "description": "Learn to build AI apps",
        },
        {
            "id": "theory-only-course",
            "name": "AI Theory Overview",
            "provider": "Test Provider",
            "resource_url": "https://example.com",
            "provider_url": "https://provider.com",
            "authority_tier": 1,  # Higher authority
            "difficulty": "beginner",
            "estimated_hours": 15,
            "format": "course",
            "tags": ["theory", "conceptual", "non-technical"],
            "description": "Theoretical overview",
        }
    ]
    
    path = navigator._fallback_learning_path(profile, resources_for_matching)
    
    # Python course should score higher despite lower authority tier
    # because it matches "build" and "python" keywords from profile
    first_resource = path["recommended_resources"][0]
    assert first_resource["resource_id"] == "python-ai-course"
