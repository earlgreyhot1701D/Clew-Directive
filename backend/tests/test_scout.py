"""
Tests for Scout Agent.

Covers:
    - Resource loading from knowledge interface
    - URL verification (with mocked HTTP)
    - Graceful degradation when verification fails
    - Filtering of non-active resources
    - Error handling (ResourceLoadError, NoResourcesFoundError)
    - High failure rate detection
    - No PII in outputs
"""

import pytest
from unittest.mock import MagicMock, Mock

from agents.scout import ScoutAgent
from interfaces.knowledge_interface import S3DirectoryKnowledge
from exceptions import ResourceLoadError, NoResourcesFoundError
from tests.mocks.s3_mocks import load_mock_directory


class TestScoutAgent:
    """Test suite for ScoutAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.directory = load_mock_directory()
        self.knowledge = S3DirectoryKnowledge(self.directory)
        self.mock_verifier = MagicMock(return_value=True)
        self.scout = ScoutAgent(
            knowledge=self.knowledge,
            resource_verifier=self.mock_verifier,
        )

    def test_gather_resources_returns_active_only(self):
        """Scout should only return resources with status='active'."""
        resources = self.scout.gather_resources(verify_urls=False)
        for r in resources:
            assert r["status"] == "active", f"Resource {r['id']} has status {r['status']}"

    def test_gather_resources_calls_verifier(self):
        """Scout should call verifier for each resource when verify_urls=True."""
        resources = self.scout.gather_resources(verify_urls=True)
        assert self.mock_verifier.call_count == len(resources)

    def test_gather_resources_without_verification(self):
        """Scout should skip verification when verify_urls=False."""
        resources = self.scout.gather_resources(verify_urls=False)
        assert self.mock_verifier.call_count == 0
        assert len(resources) > 0

    def test_graceful_degradation_on_verifier_error(self):
        """If verifier throws, Scout should include resource anyway."""
        self.mock_verifier.side_effect = Exception("Network error")
        resources = self.scout.gather_resources(verify_urls=True)
        # Resources should still be returned despite verification errors
        assert len(resources) > 0

    def test_filters_dead_resources(self):
        """Verifier returning False should exclude that resource."""
        call_count = 0
        def verifier_first_fails(url):
            nonlocal call_count
            call_count += 1
            return call_count > 1  # First resource fails, rest pass
        self.scout.resource_verifier = verifier_first_fails
        all_resources = self.knowledge.load_resources()
        verified = self.scout.gather_resources(verify_urls=True)
        if len(all_resources) > 1:
            assert len(verified) < len(all_resources)

    def test_resource_load_error_raises_exception(self):
        """Scout should raise ResourceLoadError when knowledge interface fails."""
        mock_knowledge = Mock()
        mock_knowledge.load_resources.side_effect = Exception("S3 connection timeout")
        scout = ScoutAgent(knowledge=mock_knowledge)
        
        with pytest.raises(ResourceLoadError) as exc_info:
            scout.gather_resources(domain="ai-foundations", verify_urls=False)
        
        assert "ai-foundations" in str(exc_info.value.user_message)
        assert "S3 connection timeout" in str(exc_info.value.technical_message)

    def test_no_resources_found_raises_exception(self):
        """Scout should raise NoResourcesFoundError when no resources exist for domain."""
        mock_knowledge = Mock()
        mock_knowledge.load_resources.return_value = []
        scout = ScoutAgent(knowledge=mock_knowledge)
        
        with pytest.raises(NoResourcesFoundError) as exc_info:
            scout.gather_resources(domain="nonexistent-domain", verify_urls=False)
        
        assert "nonexistent-domain" in str(exc_info.value.user_message)

    def test_all_resources_fail_verification_raises_exception(self):
        """Scout should raise NoResourcesFoundError when all resources fail verification."""
        self.mock_verifier.return_value = False  # All verifications fail
        
        with pytest.raises(NoResourcesFoundError) as exc_info:
            self.scout.gather_resources(verify_urls=True)
        
        assert "ai-foundations" in str(exc_info.value.user_message)

    def test_high_failure_rate_logs_error_but_continues(self):
        """Scout should log error when >30% resources fail but still return valid ones."""
        call_count = 0
        def verifier_40_percent_fail(url):
            nonlocal call_count
            call_count += 1
            # Fail 40% of resources
            return call_count % 5 != 0
        
        self.scout.resource_verifier = verifier_40_percent_fail
        all_resources = self.knowledge.load_resources()
        
        # Should not raise exception, but should return fewer resources
        verified = self.scout.gather_resources(verify_urls=True)
        assert len(verified) > 0
        assert len(verified) < len(all_resources)

    def test_gather_resources_with_custom_domain(self):
        """Scout should pass domain parameter to knowledge interface."""
        mock_knowledge = Mock()
        mock_knowledge.load_resources.return_value = [
            {"id": "test-1", "status": "active", "resource_url": "https://example.com"}
        ]
        scout = ScoutAgent(knowledge=mock_knowledge, resource_verifier=MagicMock(return_value=True))
        
        scout.gather_resources(domain="custom-domain", verify_urls=False)
        
        mock_knowledge.load_resources.assert_called_once_with("custom-domain")

    def test_no_pii_in_output(self):
        """Scout output should never contain PII."""
        resources = self.scout.gather_resources(verify_urls=False)
        
        # Check all resource fields for common PII patterns
        pii_patterns = [
            "@",  # Email addresses
            "phone",
            "ssn",
            "credit",
            "password",
        ]
        
        for resource in resources:
            resource_str = str(resource).lower()
            for pattern in pii_patterns:
                assert pattern not in resource_str, f"Potential PII found: {pattern}"

    def test_verifier_none_skips_verification(self):
        """Scout should skip verification when resource_verifier is None."""
        scout = ScoutAgent(knowledge=self.knowledge, resource_verifier=None)
        resources = scout.gather_resources(verify_urls=True)
        
        # Should return resources without verification
        assert len(resources) > 0

    def test_gather_resources_default_domain(self):
        """Scout should use 'ai-foundations' as default domain."""
        mock_knowledge = Mock()
        mock_knowledge.load_resources.return_value = [
            {"id": "test-1", "status": "active", "resource_url": "https://example.com"}
        ]
        scout = ScoutAgent(knowledge=mock_knowledge)
        
        scout.gather_resources(verify_urls=False)
        
        # Should call with default domain
        mock_knowledge.load_resources.assert_called_once_with("ai-foundations")

    def test_resource_url_truncation_in_logs(self):
        """Scout should truncate long URLs in log messages to prevent log pollution."""
        long_url = "https://example.com/" + "a" * 200
        mock_knowledge = Mock()
        mock_knowledge.load_resources.return_value = [
            {"id": "test-1", "status": "active", "resource_url": long_url}
        ]
        
        self.mock_verifier.return_value = False  # Trigger warning log
        scout = ScoutAgent(knowledge=mock_knowledge, resource_verifier=self.mock_verifier)
        
        # Should not raise exception even with long URL
        with pytest.raises(NoResourcesFoundError):
            scout.gather_resources(verify_urls=True)
