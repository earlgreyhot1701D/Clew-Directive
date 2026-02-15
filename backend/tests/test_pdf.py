"""
Tests for PDF generator.

Covers:
    - Template file exists
    - Template renders without errors
    - Generated HTML contains required sections
    - HTML rendering with various data
    - No PII in output

Note: PDF generation tests require WeasyPrint with GTK libraries.
On Windows, these tests focus on HTML rendering which is the core logic.
"""

import pytest
from pathlib import Path
from backend.tools.pdf_generator import render_html, WEASYPRINT_AVAILABLE
from backend.tests.mocks.bedrock_mocks import MOCK_LEARNING_PATH


class TestPDFTemplate:
    """Test suite for PDF template."""

    def test_template_exists(self):
        """Command Briefing HTML template must exist."""
        template_path = (
            Path(__file__).parent.parent / "templates" / "command_briefing.html"
        )
        assert template_path.exists(), f"Template not found: {template_path}"

    def test_template_has_required_sections(self):
        """Template must contain all required section markers."""
        template_path = (
            Path(__file__).parent.parent / "templates" / "command_briefing.html"
        )
        content = template_path.read_text()
        assert "COMMAND BRIEFING" in content.upper()
        assert "Your Profile" in content or "profile_summary" in content
        assert "Your Learning Path" in content or "recommended_resources" in content
        assert "What to Expect" in content or "approach_guidance" in content
        assert "About This Briefing" in content
        assert "No data from this session was stored" in content

    def test_template_has_wcag_colors(self):
        """Template should use WCAG-compliant color values."""
        template_path = (
            Path(__file__).parent.parent / "templates" / "command_briefing.html"
        )
        content = template_path.read_text()
        # Primary colors from design system
        assert "#0A233F" in content  # Osprey Navy
        assert "#FDC500" in content or "#fdfdfd" in content  # Gold or paper white

    def test_template_has_clickable_links(self):
        """Template should have clickable resource links."""
        template_path = (
            Path(__file__).parent.parent / "templates" / "command_briefing.html"
        )
        content = template_path.read_text()
        # Check for anchor tags with resource URLs
        assert '<a href="{{ resource.resource_url }}">' in content
        assert '<a href="{{ resource.provider_url }}">' in content


class TestHTMLRendering:
    """Test suite for HTML rendering (works without WeasyPrint)."""

    def test_render_html_with_mock_data(self):
        """Test HTML rendering with mock learning path."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # Verify HTML was generated
        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html

    def test_render_html_includes_profile(self):
        """Test that rendered HTML includes profile summary."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # Profile summary should be in the HTML
        profile = MOCK_LEARNING_PATH["profile_summary"]
        assert profile in html

    def test_render_html_includes_all_resources(self):
        """Test that rendered HTML includes all resources."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # All resource names should be in the HTML
        for resource in MOCK_LEARNING_PATH["recommended_resources"]:
            assert resource["resource_name"] in html
            assert resource["resource_url"] in html
            assert resource["provider"] in html

    def test_render_html_includes_approach_guidance(self):
        """Test that rendered HTML includes approach guidance."""
        html = render_html(MOCK_LEARNING_PATH)
        
        guidance = MOCK_LEARNING_PATH["approach_guidance"]
        assert guidance in html

    def test_render_html_includes_total_hours(self):
        """Test that rendered HTML includes total estimated hours."""
        html = render_html(MOCK_LEARNING_PATH)
        
        total_hours = str(MOCK_LEARNING_PATH["total_estimated_hours"])
        assert total_hours in html

    def test_render_html_with_minimal_data(self):
        """Test HTML rendering with minimal learning path data."""
        minimal_path = {
            "profile_summary": "Test profile",
            "recommended_resources": [
                {
                    "resource_id": "test-1",
                    "resource_name": "Test Resource",
                    "resource_url": "https://example.com",
                    "provider": "Test Provider",
                    "provider_url": "https://provider.com",
                    "why_for_you": "This is a test resource.",
                    "difficulty": "beginner",
                    "estimated_hours": 10,
                    "format": "course",
                    "free_model": "Fully free",
                    "sequence_note": "Start here",
                    "sequence_order": 1,
                }
            ],
            "approach_guidance": "Test guidance",
            "total_estimated_hours": 10,
        }
        
        html = render_html(minimal_path)
        assert len(html) > 0
        assert "Test profile" in html
        assert "Test Resource" in html

    def test_render_html_with_empty_resources(self):
        """Test HTML rendering with empty resources list."""
        empty_path = {
            "profile_summary": "Test profile",
            "recommended_resources": [],
            "approach_guidance": "No resources available",
            "total_estimated_hours": 0,
        }
        
        html = render_html(empty_path)
        assert len(html) > 0
        assert "Test profile" in html
        assert "No resources available" in html

    def test_render_html_handles_special_characters(self):
        """Test HTML rendering with special characters in content."""
        special_chars_path = {
            "profile_summary": "Test with special chars: <>&\"'",
            "recommended_resources": [
                {
                    "resource_id": "test-1",
                    "resource_name": "Resource with <special> & \"chars\"",
                    "resource_url": "https://example.com?param=value&other=test",
                    "provider": "Provider & Co.",
                    "provider_url": "https://provider.com",
                    "why_for_you": "This has 'quotes' and \"double quotes\".",
                    "difficulty": "beginner",
                    "estimated_hours": 10,
                    "format": "course",
                    "free_model": "Fully free",
                    "sequence_note": "Start here",
                    "sequence_order": 1,
                }
            ],
            "approach_guidance": "Guidance with <tags> & symbols",
            "total_estimated_hours": 10,
        }
        
        # Should not raise exception
        html = render_html(special_chars_path)
        assert len(html) > 0
        # Content should be present (Jinja2 doesn't auto-escape by default)
        assert "special" in html

    def test_render_html_no_pii(self):
        """Test that rendered HTML contains no PII."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # Should not contain email patterns (except in URLs which is OK)
        # Check that there's no standalone email address
        import re
        # Look for email patterns not in href attributes
        email_pattern = r'(?<!href=")[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, html)
        assert len(matches) == 0, f"Found email addresses: {matches}"

    def test_render_html_has_dates(self):
        """Test that rendered HTML includes generation and verification dates."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # Should contain date information
        assert "Generated:" in html or "generated" in html.lower()
        assert "verified" in html.lower()

    def test_render_html_has_privacy_statement(self):
        """Test that rendered HTML includes privacy statement."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # Should contain privacy statement
        assert "No data from this session was stored" in html

    def test_render_html_has_clickable_links(self):
        """Test that rendered HTML has clickable links."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # Should have anchor tags with hrefs
        assert '<a href="' in html
        
        # Check that resource URLs are in anchor tags
        for resource in MOCK_LEARNING_PATH["recommended_resources"]:
            url = resource["resource_url"]
            assert f'href="{url}"' in html

    def test_render_html_includes_sequence_notes(self):
        """Test that rendered HTML includes sequence notes."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # Should include sequence notes like "Start here"
        for resource in MOCK_LEARNING_PATH["recommended_resources"]:
            sequence_note = resource["sequence_note"]
            assert sequence_note in html

    def test_render_html_includes_resource_metadata(self):
        """Test that rendered HTML includes resource metadata (difficulty, hours, format)."""
        html = render_html(MOCK_LEARNING_PATH)
        
        # Should include metadata for each resource
        for resource in MOCK_LEARNING_PATH["recommended_resources"]:
            assert resource["difficulty"] in html
            assert str(resource["estimated_hours"]) in html
            assert resource["format"] in html
            assert resource["free_model"] in html


@pytest.mark.skipif(not WEASYPRINT_AVAILABLE, reason="WeasyPrint not available (requires GTK libraries)")
class TestPDFGeneration:
    """Test suite for actual PDF generation (requires WeasyPrint)."""

    def test_generate_pdf_returns_bytes(self):
        """Test that generate_pdf returns valid PDF bytes."""
        from backend.tools.pdf_generator import generate_pdf
        
        pdf_bytes = generate_pdf(MOCK_LEARNING_PATH)
        
        # Verify we got bytes
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Verify PDF magic number (starts with %PDF)
        assert pdf_bytes[:4] == b'%PDF'

    def test_generate_command_briefing_saves_file(self):
        """Test that generate_command_briefing saves file in dev mode."""
        from backend.tools.pdf_generator import generate_command_briefing
        import os
        
        os.environ["ENVIRONMENT"] = "dev"
        
        pdf_path = generate_command_briefing(MOCK_LEARNING_PATH)
        
        # Should return a file path
        assert isinstance(pdf_path, str)
        assert pdf_path.endswith(".pdf")
        
        # File should exist
        assert Path(pdf_path).exists()
        
        # Clean up
        Path(pdf_path).unlink()


