"""
Tests for Directory Loader Tool.

Tests both filesystem and S3 loading paths with mocked AWS services.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from backend.tools.directory_loader import (
    load_directory_from_file,
    load_directory_from_s3,
    load_directory,
)


# Golden test data
GOLDEN_DIRECTORY = {
    "version": "1.0.0",
    "resources": [
        {
            "id": "test-resource-1",
            "name": "Test Course",
            "domain": "ai-foundations",
            "status": "active",
            "resource_url": "https://example.com/course",
        },
        {
            "id": "test-resource-2",
            "name": "Another Course",
            "domain": "ai-foundations",
            "status": "active",
            "resource_url": "https://example.com/course2",
        },
    ],
}


class TestLoadDirectoryFromFile:
    """Tests for filesystem-based directory loading."""

    def test_load_from_default_path(self):
        """Test loading from default data/directory.json path."""
        data = load_directory_from_file()
        
        # Should return valid directory structure
        assert "resources" in data, "Should have resources key"
        assert isinstance(data["resources"], list), "Resources should be a list"
        
        # Should have version
        assert "version" in data, "Should have version key"

    def test_load_from_custom_path(self, tmp_path):
        """Test loading from custom filepath."""
        # Create temporary directory.json
        test_file = tmp_path / "test_directory.json"
        test_file.write_text(json.dumps(GOLDEN_DIRECTORY))
        
        data = load_directory_from_file(test_file)
        
        assert data["version"] == "1.0.0"
        assert len(data["resources"]) == 2
        assert data["resources"][0]["id"] == "test-resource-1"

    def test_load_nonexistent_file(self, tmp_path):
        """Test graceful handling of missing file."""
        nonexistent = tmp_path / "does_not_exist.json"
        
        data = load_directory_from_file(nonexistent)
        
        # Should return empty directory structure
        assert data == {"resources": []}

    def test_load_invalid_json(self, tmp_path):
        """Test handling of malformed JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            load_directory_from_file(bad_file)

    def test_no_pii_in_output(self):
        """Verify no PII appears in loaded directory data."""
        data = load_directory_from_file()
        
        # Convert to string for searching
        data_str = json.dumps(data).lower()
        
        # Check for common PII patterns (should not exist)
        pii_patterns = [
            "@",  # Email addresses
            "phone",
            "ssn",
            "credit",
            "password",
        ]
        
        for pattern in pii_patterns:
            assert pattern not in data_str or pattern in ["phone", "credit"], \
                f"Potential PII pattern '{pattern}' found in directory data"


class TestLoadDirectoryFromS3:
    """Tests for S3-based directory loading with mocked boto3."""

    @patch("boto3.client")
    def test_load_from_s3_success(self, mock_boto3_client):
        """Test successful S3 load."""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3
        
        # Mock S3 response
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(GOLDEN_DIRECTORY).encode("utf-8")
        mock_s3.get_object.return_value = {"Body": mock_body}
        
        # Load from S3
        data = load_directory_from_s3("test-bucket", "directory.json")
        
        # Verify boto3 called correctly
        mock_boto3_client.assert_called_once()
        mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="directory.json"
        )
        
        # Verify data
        assert data["version"] == "1.0.0"
        assert len(data["resources"]) == 2

    @patch("boto3.client")
    def test_load_from_s3_with_endpoint_url(self, mock_boto3_client):
        """Test S3 load respects AWS_ENDPOINT_URL for LocalStack."""
        with patch.dict("os.environ", {"AWS_ENDPOINT_URL": "http://localhost:4566"}):
            mock_s3 = Mock()
            mock_boto3_client.return_value = mock_s3
            
            mock_body = Mock()
            mock_body.read.return_value = json.dumps(GOLDEN_DIRECTORY).encode("utf-8")
            mock_s3.get_object.return_value = {"Body": mock_body}
            
            load_directory_from_s3("test-bucket", "directory.json")
            
            # Verify endpoint_url passed to boto3
            mock_boto3_client.assert_called_once_with(
                "s3",
                endpoint_url="http://localhost:4566"
            )

    @patch("boto3.client")
    def test_load_from_s3_client_error(self, mock_boto3_client):
        """Test handling of S3 ClientError (e.g., NoSuchKey)."""
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3
        
        # Simulate S3 error
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            "GetObject"
        )
        
        data = load_directory_from_s3("test-bucket", "missing.json")
        
        # Should return empty directory
        assert data == {"resources": []}

    @patch("boto3.client")
    def test_load_from_s3_network_error(self, mock_boto3_client):
        """Test handling of network/connection errors."""
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3
        
        # Simulate network error
        mock_s3.get_object.side_effect = Exception("Connection timeout")
        
        data = load_directory_from_s3("test-bucket", "directory.json")
        
        # Should return empty directory
        assert data == {"resources": []}

    @patch("boto3.client")
    def test_load_from_s3_invalid_json(self, mock_boto3_client):
        """Test handling of invalid JSON from S3."""
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3
        
        # Mock S3 response with invalid JSON
        mock_body = Mock()
        mock_body.read.return_value = b"{ invalid json }"
        mock_s3.get_object.return_value = {"Body": mock_body}
        
        data = load_directory_from_s3("test-bucket", "directory.json")
        
        # Should return empty directory
        assert data == {"resources": []}

    def test_load_from_s3_invalid_bucket(self):
        """Test input validation for bucket parameter."""
        # Empty bucket
        data = load_directory_from_s3("", "directory.json")
        assert data == {"resources": []}
        
        # None bucket
        data = load_directory_from_s3(None, "directory.json")
        assert data == {"resources": []}
        
        # Non-string bucket
        data = load_directory_from_s3(123, "directory.json")
        assert data == {"resources": []}

    def test_load_from_s3_invalid_key(self):
        """Test input validation for key parameter."""
        # Empty key
        data = load_directory_from_s3("test-bucket", "")
        assert data == {"resources": []}
        
        # None key
        data = load_directory_from_s3("test-bucket", None)
        assert data == {"resources": []}
        
        # Non-string key
        data = load_directory_from_s3("test-bucket", 123)
        assert data == {"resources": []}

    @patch("boto3.client")
    def test_no_pii_in_s3_output(self, mock_boto3_client):
        """Verify no PII appears in S3-loaded data."""
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3
        
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(GOLDEN_DIRECTORY).encode("utf-8")
        mock_s3.get_object.return_value = {"Body": mock_body}
        
        data = load_directory_from_s3("test-bucket", "directory.json")
        
        # Convert to string for searching
        data_str = json.dumps(data).lower()
        
        # Check for common PII patterns
        assert "@" not in data_str, "Email addresses should not appear in directory"
        assert "password" not in data_str, "Passwords should not appear in directory"


class TestLoadDirectoryFactory:
    """Tests for the factory function that chooses loader based on environment."""

    @patch("backend.config.settings.load_settings")
    @patch("backend.tools.directory_loader.load_directory_from_file")
    def test_factory_uses_file_in_dev(self, mock_file_loader, mock_settings):
        """Test factory uses filesystem loader in dev environment."""
        # Mock dev environment
        mock_env = Mock()
        mock_env.value = "dev"
        mock_settings.return_value = Mock(env=mock_env)
        
        mock_file_loader.return_value = GOLDEN_DIRECTORY
        
        data = load_directory()
        
        # Should call file loader
        mock_file_loader.assert_called_once()
        assert data == GOLDEN_DIRECTORY

    @patch("backend.tools.directory_loader.load_directory_from_s3")
    @patch("config.settings.load_settings")
    def test_factory_uses_s3_in_staging(self, mock_settings, mock_s3_loader):
        """Test factory uses S3 loader in staging environment."""
        # Mock staging environment
        mock_env = Mock()
        mock_env.value = "staging"
        mock_s3 = Mock(bucket_name="staging-bucket", directory_key="directory.json")
        mock_settings.return_value = Mock(env=mock_env, s3=mock_s3)
        
        mock_s3_loader.return_value = GOLDEN_DIRECTORY
        
        data = load_directory()
        
        # Should call S3 loader with correct params
        mock_s3_loader.assert_called_once_with("staging-bucket", "directory.json")
        assert data == GOLDEN_DIRECTORY

    @patch("backend.tools.directory_loader.load_directory_from_s3")
    @patch("config.settings.load_settings")
    def test_factory_uses_s3_in_production(self, mock_settings, mock_s3_loader):
        """Test factory uses S3 loader in production environment."""
        # Mock production environment
        mock_env = Mock()
        mock_env.value = "production"
        mock_s3 = Mock(bucket_name="prod-bucket", directory_key="directory.json")
        mock_settings.return_value = Mock(env=mock_env, s3=mock_s3)
        
        mock_s3_loader.return_value = GOLDEN_DIRECTORY
        
        data = load_directory()
        
        # Should call S3 loader with correct params
        mock_s3_loader.assert_called_once_with("prod-bucket", "directory.json")
        assert data == GOLDEN_DIRECTORY


class TestGoldenInputOutput:
    """Golden tests: known input → expected output."""

    @patch("boto3.client")
    def test_golden_directory_structure(self, mock_boto3_client):
        """Test that loaded directory has expected structure."""
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3
        
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(GOLDEN_DIRECTORY).encode("utf-8")
        mock_s3.get_object.return_value = {"Body": mock_body}
        
        data = load_directory_from_s3("test-bucket", "directory.json")
        
        # Verify structure
        assert "version" in data
        assert "resources" in data
        assert isinstance(data["resources"], list)
        
        # Verify first resource structure
        resource = data["resources"][0]
        assert "id" in resource
        assert "name" in resource
        assert "domain" in resource
        assert "status" in resource
        assert "resource_url" in resource
        
        # Verify values
        assert resource["id"] == "test-resource-1"
        assert resource["domain"] == "ai-foundations"
        assert resource["status"] == "active"
