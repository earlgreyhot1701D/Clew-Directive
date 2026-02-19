"""
Scout Agent — Resource verification using Amazon Nova Micro.

Responsibilities:
    - Load curated resources from directory.json (via knowledge interface)
    - Verify resource URLs are live (HTTP HEAD checks)
    - Return validated, active resources to the Navigator

Uses Nova Micro for cost efficiency ($0.000035/1K input tokens).
Does NOT perform reasoning — that's the Navigator's job.
"""

import logging
from typing import Any

from config.models import SCOUT_MODEL
from interfaces.knowledge_interface import KnowledgeInterface
from exceptions import ResourceLoadError, NoResourcesFoundError

logger = logging.getLogger("clew.agent.scout")


class ScoutAgent:
    """
    Scout agent: loads and verifies curated learning resources.

    The Scout reads directory.json, filters for active resources in
    the requested domain, and optionally performs runtime URL spot-checks
    to catch resources that went dead since the last Curator run.
    """

    def __init__(
        self,
        knowledge: KnowledgeInterface,
        resource_verifier: Any = None,  # tools.resource_verifier.verify_url
    ) -> None:
        self.knowledge = knowledge
        self.resource_verifier = resource_verifier
        self.model = SCOUT_MODEL

    def gather_resources(
        self,
        domain: str = "ai-foundations",
        verify_urls: bool = False,
    ) -> list[dict]:
        """
        Load and verify resources for the given domain.

        Args:
            domain: Knowledge domain to load resources for.
            verify_urls: If True AND resource_verifier is provided, perform runtime HTTP HEAD checks.
                         WARNING: With 23 resources and 5s timeout + 2 retries, worst-case is 345s.
                         Only enable for Curator runs with generous Lambda timeout (300s+).
                         User-facing requests should use verify_urls=False (default).
                         Production: Scout trusts Curator's weekly verification.

        Returns:
            List of verified, active resource dicts.
            
        Raises:
            ResourceLoadError: If resource loading fails
            NoResourcesFoundError: If no resources found for domain
        """
        logger.info(
            "[agent:scout] Loading resources for domain=%s, verify=%s",
            domain,
            verify_urls,
        )

        # Load all active resources from knowledge interface
        try:
            resources = self.knowledge.load_resources(domain)
        except Exception as e:
            logger.error("[agent:scout] Failed to load resources: %s", e, exc_info=True)
            raise ResourceLoadError(domain, str(e))
        
        if not resources:
            logger.warning("[agent:scout] No resources found for domain=%s", domain)
            raise NoResourcesFoundError(domain)
        
        logger.info("[agent:scout] Loaded %d active resources", len(resources))

        if not verify_urls or self.resource_verifier is None:
            return resources

        # Runtime URL verification (spot-check)
        verified = []
        failed_count = 0
        
        for resource in resources:
            url = resource.get("resource_url", "")
            resource_id = resource.get("id", "unknown")
            
            try:
                is_live = self.resource_verifier(url)
                if is_live:
                    verified.append(resource)
                else:
                    failed_count += 1
                    logger.warning(
                        "[agent:scout] Resource failed verification: id=%s url=%s",
                        resource_id,
                        url[:100],
                    )
            except Exception as verify_error:
                # Graceful degradation: if verification fails, include the
                # resource anyway (Curator verified it within the last week)
                logger.warning(
                    "[agent:scout] Verification error for id=%s, including anyway: %s",
                    resource_id,
                    str(verify_error)[:100],
                )
                verified.append(resource)

        # Check if too many resources failed
        failure_rate = failed_count / len(resources) if resources else 0
        if failure_rate > 0.3:  # More than 30% failed
            logger.error(
                "[agent:scout] High failure rate: %d/%d resources failed verification",
                failed_count,
                len(resources),
            )
            # Still return what we have, but log the issue
        
        if not verified:
            logger.error("[agent:scout] All resources failed verification")
            raise NoResourcesFoundError(domain)

        logger.info(
            "[agent:scout] Verification complete: %d/%d resources passed",
            len(verified),
            len(resources),
        )
        return verified
