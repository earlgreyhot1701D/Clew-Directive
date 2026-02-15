"""
Tests for Curator freshness check.

Covers:
    - Status progression (active → degraded → stale → dead)
    - last_verified timestamp updates
    - Graceful handling of verification errors
    - Lambda handler S3 integration (mocked)
    - CloudWatch metrics publishing
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from backend.curator.freshness_check import (
    check_all_resources,
    lambda_handler,
    STATUS_ACTIVE,
    STATUS_DEGRADED,
    STATUS_STALE,
    STATUS_DEAD,
)


class TestCuratorFreshness:
    """Test suite for Curator freshness checks."""

    def _make_directory(self, statuses=None):
        """Create a minimal directory for testing."""
        statuses = statuses or ["active", "active"]
        return {
            "version": "test",
            "resources": [
                {
                    "id": f"test-{i}",
                    "resource_url": f"https://example.com/resource-{i}",
                    "status": s,
                    "last_verified": "2026-01-01T00:00:00Z",
                }
                for i, s in enumerate(statuses)
            ],
        }

    @patch("backend.curator.freshness_check.verify_url", return_value=True)
    def test_all_active_stays_active(self, mock_verify):
        """If all URLs are live, all statuses should remain active."""
        directory = self._make_directory(["active", "active"])
        updated = check_all_resources(directory)
        for r in updated["resources"]:
            assert r["status"] == STATUS_ACTIVE

    @patch("backend.curator.freshness_check.verify_url", return_value=False)
    def test_active_degrades_on_failure(self, mock_verify):
        """Active resource should degrade to degraded on first failure."""
        directory = self._make_directory(["active"])
        updated = check_all_resources(directory)
        assert updated["resources"][0]["status"] == STATUS_DEGRADED

    @patch("backend.curator.freshness_check.verify_url", return_value=False)
    def test_degraded_becomes_stale(self, mock_verify):
        """Degraded resource should become stale on second failure."""
        directory = self._make_directory(["degraded"])
        updated = check_all_resources(directory)
        assert updated["resources"][0]["status"] == STATUS_STALE

    @patch("backend.curator.freshness_check.verify_url", return_value=False)
    def test_stale_becomes_dead(self, mock_verify):
        """Stale resource should become dead on third failure."""
        directory = self._make_directory(["stale"])
        updated = check_all_resources(directory)
        assert updated["resources"][0]["status"] == STATUS_DEAD

    @patch("backend.curator.freshness_check.verify_url", return_value=False)
    def test_dead_stays_dead(self, mock_verify):
        """Dead resource should remain dead on subsequent failures."""
        directory = self._make_directory(["dead"])
        updated = check_all_resources(directory)
        assert updated["resources"][0]["status"] == STATUS_DEAD

    @patch("backend.curator.freshness_check.verify_url", return_value=True)
    def test_last_verified_updates(self, mock_verify):
        """last_verified should be updated for every resource."""
        directory = self._make_directory(["active"])
        old_verified = directory["resources"][0]["last_verified"]
        updated = check_all_resources(directory)
        assert updated["resources"][0]["last_verified"] != old_verified

    @patch("backend.curator.freshness_check.verify_url", return_value=True)
    def test_last_curated_updates(self, mock_verify):
        """Directory-level last_curated should be updated."""
        directory = self._make_directory()
        updated = check_all_resources(directory)
        assert "last_curated" in updated

    @patch("backend.curator.freshness_check.verify_url", side_effect=Exception("Network error"))
    def test_verification_error_handling(self, mock_verify):
        """Verification errors should be logged but not crash."""
        directory = self._make_directory(["active"])
        updated = check_all_resources(directory)
        # Should still update last_verified even on error
        assert updated["resources"][0]["last_verified"] != "2026-01-01T00:00:00Z"

    @patch("backend.curator.freshness_check.verify_url")
    def test_mixed_results(self, mock_verify):
        """Test with mix of live and dead URLs."""
        # First URL live, second dead
        mock_verify.side_effect = [True, False]
        directory = self._make_directory(["active", "active"])
        updated = check_all_resources(directory)
        assert updated["resources"][0]["status"] == STATUS_ACTIVE
        assert updated["resources"][1]["status"] == STATUS_DEGRADED


class TestCuratorLambda:
    """Test suite for Curator Lambda handler."""

    @patch.dict("os.environ", {"CD_S3_BUCKET": "test-bucket", "CD_DIRECTORY_KEY": "test.json"})
    @patch("backend.curator.freshness_check.verify_url", return_value=True)
    @patch("boto3.client")
    def test_lambda_handler_success(self, mock_boto3_client, mock_verify):
        """Lambda handler should read from S3, check resources, write back."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_boto3_client.side_effect = lambda service: (
            mock_s3 if service == "s3" else mock_cloudwatch
        )

        # Mock S3 get_object response
        directory_data = {
            "version": "1.0",
            "resources": [
                {
                    "id": "test-1",
                    "resource_url": "https://example.com/1",
                    "status": "active",
                    "last_verified": "2026-01-01T00:00:00Z",
                }
            ],
        }
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(directory_data).encode())
        }

        # Call lambda handler
        result = lambda_handler({}, None)

        # Verify S3 operations
        assert mock_s3.get_object.called
        assert mock_s3.put_object.called

        # Verify CloudWatch metrics published
        assert mock_cloudwatch.put_metric_data.called

        # Verify response
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["total_resources"] == 1
        assert body["failed_resources"] == 0

    @patch.dict("os.environ", {"CD_S3_BUCKET": "test-bucket", "CD_DIRECTORY_KEY": "test.json"})
    @patch("backend.curator.freshness_check.verify_url", return_value=False)
    @patch("boto3.client")
    def test_lambda_handler_high_failure_rate(self, mock_boto3_client, mock_verify):
        """Lambda handler should detect high failure rate."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_boto3_client.side_effect = lambda service: (
            mock_s3 if service == "s3" else mock_cloudwatch
        )

        # Mock directory with 5 resources (all will fail)
        directory_data = {
            "version": "1.0",
            "resources": [
                {
                    "id": f"test-{i}",
                    "resource_url": f"https://example.com/{i}",
                    "status": "active",
                    "last_verified": "2026-01-01T00:00:00Z",
                }
                for i in range(5)
            ],
        }
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(directory_data).encode())
        }

        # Call lambda handler
        result = lambda_handler({}, None)

        # Verify response shows high failure rate
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["failed_resources"] == 5  # All failed
        assert body["failure_rate"] == 100.0  # All failed

    @patch.dict("os.environ", {"CD_S3_BUCKET": "test-bucket", "CD_DIRECTORY_KEY": "test.json"})
    @patch("boto3.client")
    def test_lambda_handler_s3_error(self, mock_boto3_client):
        """Lambda handler should handle S3 errors gracefully."""
        # Mock S3 client that raises error
        mock_s3 = MagicMock()
        mock_s3.get_object.side_effect = Exception("S3 error")
        mock_boto3_client.return_value = mock_s3

        # Call lambda handler
        result = lambda_handler({}, None)

        # Verify error response
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "error" in body

    @patch.dict("os.environ", {"CD_S3_BUCKET": "test-bucket", "CD_DIRECTORY_KEY": "test.json"})
    @patch("backend.curator.freshness_check.verify_url")
    @patch("boto3.client")
    def test_lambda_handler_cloudwatch_metrics(self, mock_boto3_client, mock_verify):
        """Lambda handler should publish CloudWatch metrics."""
        # Mock S3 and CloudWatch clients
        mock_s3 = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_boto3_client.side_effect = lambda service: (
            mock_s3 if service == "s3" else mock_cloudwatch
        )

        # Mock directory with mixed results (2 active, 1 degraded)
        mock_verify.side_effect = [True, True, False]
        directory_data = {
            "version": "1.0",
            "resources": [
                {
                    "id": f"test-{i}",
                    "resource_url": f"https://example.com/{i}",
                    "status": "active",
                    "last_verified": "2026-01-01T00:00:00Z",
                }
                for i in range(3)
            ],
        }
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(directory_data).encode())
        }

        # Call lambda handler
        result = lambda_handler({}, None)

        # Verify CloudWatch metrics were published
        assert mock_cloudwatch.put_metric_data.called
        call_args = mock_cloudwatch.put_metric_data.call_args
        assert call_args[1]["Namespace"] == "ClewDirective/Curator"
        
        # Verify metric data contains expected metrics
        metric_data = call_args[1]["MetricData"]
        metric_names = [m["MetricName"] for m in metric_data]
        assert "ResourceFailureRate" in metric_names
        assert "FailedResources" in metric_names
        assert "TotalResources" in metric_names

    @patch.dict("os.environ", {"CD_S3_BUCKET": "test-bucket", "CD_DIRECTORY_KEY": "test.json"})
    @patch("backend.curator.freshness_check.verify_url", return_value=False)
    @patch("boto3.client")
    def test_lambda_handler_alert_threshold(self, mock_boto3_client, mock_verify):
        """Lambda handler should log error when failure rate exceeds 10%."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_boto3_client.side_effect = lambda service: (
            mock_s3 if service == "s3" else mock_cloudwatch
        )

        # Mock directory with 20 resources (all will fail = 100% failure rate)
        directory_data = {
            "version": "1.0",
            "resources": [
                {
                    "id": f"test-{i}",
                    "resource_url": f"https://example.com/{i}",
                    "status": "active",
                    "last_verified": "2026-01-01T00:00:00Z",
                }
                for i in range(20)
            ],
        }
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(directory_data).encode())
        }

        # Call lambda handler
        with patch("backend.curator.freshness_check.logger") as mock_logger:
            result = lambda_handler({}, None)
            
            # Verify error was logged for high failure rate
            assert any(
                "ALERT" in str(call) and "10%" in str(call)
                for call in mock_logger.error.call_args_list
            )

        # Verify response still succeeds
        assert result["statusCode"] == 200

    @patch.dict("os.environ", {"CD_S3_BUCKET": "test-bucket", "CD_DIRECTORY_KEY": "test.json"})
    @patch("backend.curator.freshness_check.verify_url", return_value=True)
    @patch("boto3.client")
    def test_lambda_handler_s3_write_format(self, mock_boto3_client, mock_verify):
        """Lambda handler should write properly formatted JSON to S3."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_boto3_client.side_effect = lambda service: (
            mock_s3 if service == "s3" else mock_cloudwatch
        )

        # Mock directory
        directory_data = {
            "version": "1.0",
            "resources": [
                {
                    "id": "test-1",
                    "resource_url": "https://example.com/1",
                    "status": "active",
                    "last_verified": "2026-01-01T00:00:00Z",
                }
            ],
        }
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(directory_data).encode())
        }

        # Call lambda handler
        result = lambda_handler({}, None)

        # Verify S3 put_object was called with correct parameters
        assert mock_s3.put_object.called
        call_args = mock_s3.put_object.call_args
        assert call_args[1]["Bucket"] == "test-bucket"
        assert call_args[1]["Key"] == "test.json"
        assert call_args[1]["ContentType"] == "application/json"
        
        # Verify JSON is properly formatted (indented)
        written_json = call_args[1]["Body"]
        assert "  " in written_json  # Should have indentation

    @patch.dict("os.environ", {})  # No environment variables set
    @patch("backend.curator.freshness_check.verify_url", return_value=True)
    @patch("boto3.client")
    def test_lambda_handler_default_env_vars(self, mock_boto3_client, mock_verify):
        """Lambda handler should use default values when env vars not set."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_boto3_client.side_effect = lambda service: (
            mock_s3 if service == "s3" else mock_cloudwatch
        )

        # Mock directory
        directory_data = {
            "version": "1.0",
            "resources": [
                {
                    "id": "test-1",
                    "resource_url": "https://example.com/1",
                    "status": "active",
                    "last_verified": "2026-01-01T00:00:00Z",
                }
            ],
        }
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(directory_data).encode())
        }

        # Call lambda handler
        result = lambda_handler({}, None)

        # Verify default bucket and key were used
        get_call_args = mock_s3.get_object.call_args
        assert get_call_args[1]["Bucket"] == "clew-directive-data"
        assert get_call_args[1]["Key"] == "directory.json"

    def test_check_all_resources_no_pii(self):
        """Verify no PII appears in any output."""
        directory = {
            "version": "1.0",
            "resources": [
                {
                    "id": "test-1",
                    "resource_url": "https://example.com/1",
                    "status": "active",
                    "last_verified": "2026-01-01T00:00:00Z",
                }
            ],
        }
        
        with patch("backend.curator.freshness_check.verify_url", return_value=True):
            updated = check_all_resources(directory)
        
        # Convert to JSON string to check for PII patterns
        output_str = json.dumps(updated)
        
        # Check for common PII patterns (email, phone, SSN, etc.)
        import re
        assert not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', output_str), "Email found in output"
        assert not re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', output_str), "Phone number found in output"
        assert not re.search(r'\b\d{3}-\d{2}-\d{4}\b', output_str), "SSN found in output"

