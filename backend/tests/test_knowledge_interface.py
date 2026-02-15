"""
Tests for Knowledge Interface.
"""

import pytest
from backend.interfaces.knowledge_interface import (
    S3DirectoryKnowledge,
    create_knowledge,
)
from backend.tools.directory_loader import load_directory_from_file


def test_s3_directory_knowledge_load_resources():
    """Test loading active resources from directory."""
    # Load real directory.json
    directory_data = load_directory_from_file()
    
    knowledge = S3DirectoryKnowledge(directory_data)
    resources = knowledge.load_resources("ai-foundations")
    
    # Should have resources
    assert len(resources) > 0, "Should load resources from directory.json"
    
    # All should be active
    for resource in resources:
        assert resource.get("status") == "active", f"Resource {resource.get('id')} should be active"


def test_s3_directory_knowledge_get_resource():
    """Test retrieving a single resource by ID."""
    directory_data = load_directory_from_file()
    knowledge = S3DirectoryKnowledge(directory_data)
    
    # Get first resource ID from directory
    resources = knowledge.load_resources("ai-foundations")
    if resources:
        first_id = resources[0]["id"]
        
        # Retrieve by ID
        resource = knowledge.get_resource(first_id)
        assert resource is not None, f"Should find resource {first_id}"
        assert resource["id"] == first_id
    
    # Test non-existent ID
    resource = knowledge.get_resource("non-existent-id-12345")
    assert resource is None, "Should return None for non-existent ID"


def test_s3_directory_knowledge_empty_data():
    """Test handling of empty directory data."""
    knowledge = S3DirectoryKnowledge({"resources": []})
    resources = knowledge.load_resources("ai-foundations")
    assert resources == [], "Should return empty list for empty directory"


def test_create_knowledge_factory():
    """Test factory function creates correct implementation."""
    directory_data = load_directory_from_file()
    knowledge = create_knowledge(directory_data)
    
    assert isinstance(knowledge, S3DirectoryKnowledge)
    resources = knowledge.load_resources("ai-foundations")
    assert len(resources) > 0


def test_load_resources_filters_by_status():
    """Test that only active resources are returned."""
    test_data = {
        "domain": "ai-foundations",
        "resources": [
            {"id": "active-1", "status": "active"},
            {"id": "degraded-1", "status": "degraded"},
            {"id": "stale-1", "status": "stale"},
            {"id": "active-2", "status": "active"},
        ]
    }
    
    knowledge = S3DirectoryKnowledge(test_data)
    resources = knowledge.load_resources("ai-foundations")
    
    assert len(resources) == 2, "Should only return active resources"
    assert all(r["status"] == "active" for r in resources)


def test_load_resources_filters_by_domain():
    """Test that only matching domain resources are returned."""
    test_data = {
        "domain": "ai-foundations",
        "resources": [
            {"id": "ai-1", "status": "active"},
            {"id": "ai-2", "status": "active"},
        ]
    }
    
    knowledge = S3DirectoryKnowledge(test_data)
    
    # Should return resources for matching domain
    resources = knowledge.load_resources("ai-foundations")
    assert len(resources) == 2, "Should return resources for matching domain"
    
    # Should return empty for non-matching domain
    resources = knowledge.load_resources("web-development")
    assert len(resources) == 0, "Should return empty for non-matching domain"
