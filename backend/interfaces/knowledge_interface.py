"""
Knowledge interface for Clew Directive resource directory.

MVP: Direct S3 JSON read via directory_loader tool.
Future: Bedrock Knowledge Base or embedding-based semantic search.

Contract:
    load_resources(domain) → list[dict]
    get_resource(resource_id) → dict or None
"""

from abc import ABC, abstractmethod


class KnowledgeInterface(ABC):
    """Abstract knowledge base contract."""

    @abstractmethod
    def load_resources(self, domain: str = "ai-foundations") -> list[dict]:
        """
        Load all active resources for a given domain.

        Args:
            domain: Knowledge domain to filter by. MVP uses "ai-foundations" only.

        Returns:
            List of resource dicts with status == "active".
        """
        ...

    @abstractmethod
    def get_resource(self, resource_id: str) -> dict | None:
        """Retrieve a single resource by ID."""
        ...


class S3DirectoryKnowledge(KnowledgeInterface):
    """
    MVP implementation: reads directory.json from S3 directly.

    The full JSON is small enough (~35-40 resources) to load entirely
    into memory. Navigator reasons over the complete dataset in-context.
    No vector search needed at this scale.
    """

    def __init__(self, directory_data: dict | None = None) -> None:
        self._data = directory_data or {"resources": []}

    def load_resources(self, domain: str = "ai-foundations") -> list[dict]:
        # Check if domain matches the directory-level domain
        directory_domain = self._data.get("domain", "ai-foundations")
        
        # If requesting a different domain than what's in the directory, return empty
        if domain != directory_domain:
            return []
        
        # Return all active resources (domain is implicit from directory)
        return [
            r for r in self._data.get("resources", [])
            if r.get("status") == "active"
        ]

    def get_resource(self, resource_id: str) -> dict | None:
        for r in self._data.get("resources", []):
            if r.get("id") == resource_id:
                return r
        return None


# TODO: Future implementation
# class BedrockKBKnowledge(KnowledgeInterface):
#     """Future: Bedrock Knowledge Base with OpenSearch vector store."""
#     pass
#
# class EmbeddingKnowledge(KnowledgeInterface):
#     """Future: Titan Text Embeddings + cosine similarity in Lambda."""
#     pass


def create_knowledge(directory_data: dict | None = None) -> KnowledgeInterface:
    """Factory: returns the active knowledge implementation."""
    return S3DirectoryKnowledge(directory_data)
