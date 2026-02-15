"""
Tests for Navigator Agent - Profile Synthesis.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.agents.navigator import NavigatorAgent


@pytest.fixture
def navigator():
    """Create a Navigator agent instance."""
    return NavigatorAgent()


@pytest.fixture
def sample_vibe_check():
    """Sample Vibe Check responses."""
    return {
        "skepticism": "Curious but haven't started learning",
        "goal": "Understand what AI actually is and isn't",
        "learning_style": "Reading and thinking at my own pace",
        "context": "Business / Marketing / Operations"
    }


def test_synthesize_profile_basic(navigator, sample_vibe_check):
    """Test basic profile synthesis with mocked Strands response."""
    mock_response = Mock()
    mock_response.output = """You're approaching AI with curiosity but haven't started learning yet, 
    which is a great place to begin. Your main goal is to understand what AI actually is and isn't, 
    and you prefer learning by reading at your own pace. Given your background in business and marketing, 
    we'll focus on resources that connect AI concepts to practical applications in your field."""
    
    with patch.object(navigator.agent, 'invoke_async', new_callable=AsyncMock, return_value=mock_response):
        profile = navigator.synthesize_profile(sample_vibe_check)
        
        # Should return a string
        assert isinstance(profile, str)
        
        # Should be reasonable length (3-4 sentences)
        assert len(profile) > 100, "Profile should be substantial"
        assert len(profile) < 1000, "Profile should be concise"
        
        # Should use second person
        assert "you" in profile.lower() or "your" in profile.lower(), "Should use second person"


def test_synthesize_profile_fallback_on_error(navigator, sample_vibe_check):
    """Test that fallback is used when Strands call fails."""
    with patch.object(navigator.agent, 'invoke_async', side_effect=Exception("API Error")):
        profile = navigator.synthesize_profile(sample_vibe_check)
        
        # Should still return a profile (fallback)
        assert isinstance(profile, str)
        assert len(profile) > 100


def test_refine_profile(navigator):
    """Test profile refinement with mocked response."""
    original = """You're approaching AI with curiosity but haven't started learning yet. 
    Your main goal is to understand what AI actually is and isn't, and you prefer learning 
    by reading at your own pace. Given your background in business, we'll focus on practical 
    applications."""
    
    correction = "I'm actually more interested in the technical side, not just business applications"
    
    mock_response = Mock()
    mock_response.output = """You're approaching AI with curiosity and want to understand it deeply. 
    Your main goal is to grasp what AI actually is and isn't, with a focus on the technical foundations 
    rather than just business applications. You prefer learning by reading at your own pace, which will 
    serve you well as you explore the technical concepts."""
    
    with patch.object(navigator.agent, 'invoke_async', new_callable=AsyncMock, return_value=mock_response):
        refined = navigator.refine_profile(original, correction)
        
        # Should return a string
        assert isinstance(refined, str)
        
        # Should be different from original
        assert refined != original
        
        # Should be reasonable length
        assert len(refined) > 100


def test_refine_profile_fallback_on_error(navigator):
    """Test that refinement falls back gracefully on error."""
    original = "You're a complete beginner to AI."
    correction = "I actually have some experience with machine learning"
    
    with patch.object(navigator.agent, 'invoke_async', side_effect=Exception("API Error")):
        refined = navigator.refine_profile(original, correction)
        
        # Should produce a refined profile (fallback)
        assert len(refined) > 0
        assert correction in refined  # Fallback includes the correction


def test_fallback_profile(navigator, sample_vibe_check):
    """Test fallback profile generation."""
    fallback = navigator._fallback_profile(sample_vibe_check)
    
    # Should return a string
    assert isinstance(fallback, str)
    
    # Should be reasonable length
    assert len(fallback) > 100
    
    # Should use second person
    assert "you" in fallback.lower() or "your" in fallback.lower()
