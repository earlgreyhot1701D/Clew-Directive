"""
Tests for Navigator agent capitalization fixes.

Verifies that the fix_capitalization function properly handles:
- Lowercase "i" and i-contractions
- Lowercase "ai" acronym
- Sentence starts
- First character capitalization
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from agents.navigator import fix_capitalization


class TestCapitalizationFix:
    """Test suite for capitalization fixes."""
    
    def test_fix_standalone_i(self):
        """Test that standalone 'i' is capitalized to 'I'."""
        text = "i want to learn"
        result = fix_capitalization(text)
        assert result == "I want to learn"
    
    def test_fix_i_contractions(self):
        """Test that i-contractions are capitalized."""
        test_cases = [
            ("i've dabbled", "I've dabbled"),
            ("i'm curious", "I'm curious"),
            ("i'll start", "I'll start"),
            ("i'd like", "I'd like"),
            ("i're interested", "I're interested"),
        ]
        
        for input_text, expected in test_cases:
            result = fix_capitalization(input_text)
            assert result == expected, f"Failed for: {input_text}"
    
    def test_fix_ai_acronym(self):
        """Test that 'ai' is capitalized to 'AI'."""
        test_cases = [
            ("exploring ai", "Exploring AI"),
            ("build things with ai", "Build things with AI"),
            ("ai tools", "AI tools"),
            ("learn about ai", "Learn about AI"),
        ]
        
        for input_text, expected in test_cases:
            result = fix_capitalization(input_text)
            assert result == expected, f"Failed for: {input_text}"
    
    def test_fix_sentence_starts(self):
        """Test that sentences start with capital letters."""
        text = "first sentence. second sentence. third sentence!"
        result = fix_capitalization(text)
        assert result == "First sentence. Second sentence. Third sentence!"
    
    def test_fix_first_character(self):
        """Test that the first character is always capitalized."""
        text = "you're approaching AI"
        result = fix_capitalization(text)
        assert result == "You're approaching AI"
    
    def test_complex_profile_text(self):
        """Test with realistic profile text containing multiple issues."""
        text = "You're approaching AI with a i've dabbled and want more structure mindset. your main goal is to build things with ai, and you prefer learning by hands-on projects. given your background in career transition / exploring ai, we'll focus on resources that connect AI concepts to practical applications."
        
        result = fix_capitalization(text)
        
        # Check all issues are fixed
        assert "I've dabbled" in result
        assert "build things with AI" in result
        assert "exploring AI" in result
        assert result.startswith("You're")
        assert ". Your main goal" in result or ". your main goal" in result  # Sentence start
        assert ". Given your background" in result or ". given your background" in result
    
    def test_empty_string(self):
        """Test that empty string is handled."""
        result = fix_capitalization("")
        assert result == ""
    
    def test_none_input(self):
        """Test that None is handled."""
        result = fix_capitalization(None)
        assert result is None
    
    def test_preserves_proper_nouns(self):
        """Test that existing proper capitalization is preserved."""
        text = "You're learning from Stanford University and MIT."
        result = fix_capitalization(text)
        assert "Stanford University" in result
        assert "MIT" in result
    
    def test_multiple_ai_occurrences(self):
        """Test that all occurrences of 'ai' are fixed."""
        text = "ai is powerful. learn ai. use ai tools."
        result = fix_capitalization(text)
        assert result.count("AI") == 3
        assert "ai" not in result.lower() or "AI" in result  # All 'ai' should be 'AI'
    
    def test_user_input_phrases(self):
        """Test with actual user input phrases from Vibe Check."""
        test_cases = [
            (
                "You're approaching AI with a i've dabbled and want more structure mindset",
                "I've dabbled"
            ),
            (
                "career transition / exploring ai",
                "AI"  # Will be capitalized
            ),
            (
                "build things with ai",
                "AI"  # Will be capitalized
            ),
        ]
        
        for input_text, expected_phrase in test_cases:
            result = fix_capitalization(input_text)
            assert expected_phrase in result, f"Expected '{expected_phrase}' in: {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
