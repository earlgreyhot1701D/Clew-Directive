"""
Orchestrator — Coordinates the full Clew Directive flow.

Flow:
    1. Receive Vibe Check responses from frontend
    2. Navigator synthesizes profile summary
    3. Return profile for feedback loop ("Does this sound like you?")
    4. On confirmation: Scout gathers + verifies resources
    5. Navigator generates personalized learning path
    6. PDF generator creates Command Briefing
    7. Return PDF download URL
    8. Session memory cleared (stateless)

This file orchestrates but does not implement. Each step delegates
to the appropriate agent, tool, or interface.
"""

import logging
from typing import Any

from agents.scout import ScoutAgent
from agents.navigator import NavigatorAgent
from interfaces.memory_interface import MemoryInterface, create_memory
from interfaces.knowledge_interface import KnowledgeInterface
from tools.pdf_generator import generate_command_briefing
from exceptions import (
    ClewException,
    BedrockTimeoutError,
    BedrockThrottleError,
    InvalidLLMResponseError,
    ResourceLoadError,
    NoResourcesFoundError,
    PDFGenerationError,
)

logger = logging.getLogger("clew.orchestrator")


class Orchestrator:
    """
    Coordinates the Vibe Check → Profile → Path → PDF flow.

    Stateless: all session data lives in memory_interface and is
    cleared after PDF delivery.
    """

    def __init__(
        self,
        scout: ScoutAgent,
        navigator: NavigatorAgent,
        memory: MemoryInterface | None = None,
    ) -> None:
        self.scout = scout
        self.navigator = navigator
        self.memory = memory or create_memory()

    def process_vibe_check(self, vibe_check_responses: dict) -> str:
        """
        Process Vibe Check responses and generate profile summary.

        Args:
            vibe_check_responses: Dict mapping question IDs to selected options.
                Example: {"skepticism": "Curious but haven't started", ...}

        Returns:
            Profile summary string (3-4 sentences).
            
        Raises:
            ClewException: For user-facing errors (timeout, throttle, etc.)
        """
        logger.info("[orchestrator] Processing Vibe Check")
        
        try:
            profile = self.navigator.synthesize_profile(vibe_check_responses)
            logger.info("[orchestrator] Profile synthesized: %d chars", len(profile))
            return profile
            
        except (BedrockTimeoutError, BedrockThrottleError, InvalidLLMResponseError):
            # Re-raise custom exceptions (they have user-friendly messages)
            raise
            
        except Exception as e:
            logger.error("[orchestrator] Vibe Check processing failed: %s", e, exc_info=True)
            # Generic fallback - Navigator should have handled this, but just in case
            raise ClewException(
                user_message=(
                    "We encountered an error generating your profile. "
                    "Please try again or refresh the page."
                ),
                technical_message=f"Orchestrator: Vibe Check processing failed: {str(e)}",
                retry_allowed=True,
                http_status=500,
            )

    def process_refinement(self, original_profile: str, user_correction: str) -> str:
        """
        Refine profile based on user feedback.

        Args:
            original_profile: The first profile summary that was rejected.
            user_correction: Free text from user explaining what was wrong.

        Returns:
            Revised profile summary string.
            
        Raises:
            ClewException: For user-facing errors (timeout, throttle, etc.)
        """
        logger.info("[orchestrator] Processing profile refinement")
        
        try:
            refined_profile = self.navigator.refine_profile(original_profile, user_correction)
            logger.info("[orchestrator] Profile refined: %d chars", len(refined_profile))
            return refined_profile
            
        except (BedrockTimeoutError, BedrockThrottleError):
            # Re-raise custom exceptions
            raise
            
        except Exception as e:
            logger.error("[orchestrator] Profile refinement failed: %s", e, exc_info=True)
            # Fallback: return original with note
            logger.warning("[orchestrator] Returning original profile with user note")
            return f"{original_profile}\n\n(Note: {user_correction})"

    def generate_briefing(self, approved_profile: str) -> dict:
        """
        Generate complete learning path briefing.

        Args:
            approved_profile: The confirmed profile summary.

        Returns:
            Dict with complete learning path structure:
            {
                "profile_summary": str,
                "recommended_resources": list[dict],
                "approach_guidance": str,
                "total_estimated_hours": int,
            }
            
        Raises:
            ClewException: For user-facing errors
        """
        logger.info("[orchestrator] Generating briefing")
        
        try:
            # Scout gathers and verifies resources
            resources = self.scout.gather_resources(domain="ai-foundations")
            logger.info("[orchestrator] Scout gathered %d resources", len(resources))
            
        except NoResourcesFoundError:
            # Re-raise - has user-friendly message
            raise
            
        except ResourceLoadError:
            # Re-raise - has user-friendly message
            raise
            
        except Exception as e:
            logger.error("[orchestrator] Scout failed: %s", e, exc_info=True)
            raise ClewException(
                user_message=(
                    "We're having trouble loading our resource directory. "
                    "Please try again in a few minutes."
                ),
                technical_message=f"Orchestrator: Scout failed: {str(e)}",
                retry_allowed=True,
                http_status=503,
            )
        
        try:
            # Navigator generates personalized path
            learning_path = self.navigator.generate_learning_path(approved_profile, resources)
            logger.info(
                "[orchestrator] Navigator generated path with %d resources",
                len(learning_path.get("recommended_resources", [])),
            )
            
            return learning_path
            
        except (BedrockTimeoutError, BedrockThrottleError, InvalidLLMResponseError):
            # Re-raise custom exceptions
            raise
            
        except Exception as e:
            logger.error("[orchestrator] Navigator failed: %s", e, exc_info=True)
            raise ClewException(
                user_message=(
                    "We encountered an error generating your learning path. "
                    "Please try again."
                ),
                technical_message=f"Orchestrator: Navigator failed: {str(e)}",
                retry_allowed=True,
                http_status=500,
            )

    def start_session(self, vibe_check_responses: dict) -> dict:
        """
        .. deprecated::
            **NOT CALLED IN PRODUCTION.** This method was written for the
            original single-process architecture where a long-lived
            Orchestrator managed in-memory session state across the full
            Vibe Check → Feedback → Briefing flow.

            In the Lambda deployment, each HTTP request is handled by a
            separate Lambda function that calls process_vibe_check(),
            process_refinement(), or generate_briefing() directly —
            bypassing start_session() entirely.

            Scheduled for removal in a future cleanup pass.

        Phase 1: Process Vibe Check and return profile for feedback.

        Args:
            vibe_check_responses: Dict mapping question IDs to selected options.

        Returns:
            {
                "profile_summary": str,
                "session_id": str,  # Ephemeral, for this request only
            }
        """
        logger.info("[orchestrator] Starting session with Vibe Check")

        # Store responses in session memory
        self.memory.store("vibe_check", vibe_check_responses)

        # Navigator synthesizes profile
        profile = self.navigator.synthesize_profile(vibe_check_responses)
        self.memory.store("profile_summary", profile)
        self.memory.store("refinement_count", 0)

        return {
            "profile_summary": profile,
            "phase": "feedback",
        }

    def handle_feedback(self, confirmed: bool, correction: str = "") -> dict:
        """
        .. deprecated::
            **NOT CALLED IN PRODUCTION.** This method was written for the
            original single-process architecture where a long-lived
            Orchestrator managed in-memory session state (profile, refinement
            count) across multiple user interactions.

            In the Lambda deployment, the frontend manages flow state and
            calls process_refinement() or generate_briefing() directly via
            separate Lambda invocations — bypassing handle_feedback() entirely.

            Scheduled for removal in a future cleanup pass.

        Phase 2: Handle "That's me" or "Not quite" feedback.

        Args:
            confirmed: True if user confirmed profile, False if rejected.
            correction: Free text correction (only if confirmed=False).

        Returns:
            If confirmed: proceeds to path generation, returns learning path + PDF URL.
            If not confirmed (first time): returns refined profile for second feedback.
            If not confirmed (second time): returns reset signal.
        """
        refinement_count = self.memory.retrieve("refinement_count") or 0

        if confirmed:
            logger.info("[orchestrator] Profile confirmed, generating path")
            return self._generate_path_and_briefing()

        if refinement_count >= 1:
            logger.info("[orchestrator] Second rejection — reset")
            self.memory.clear()
            return {"phase": "reset", "message": "Let's start fresh."}

        # First rejection — refine
        logger.info("[orchestrator] Refining profile with correction")
        original = self.memory.retrieve("profile_summary") or ""
        refined = self.navigator.refine_profile(original, correction)
        self.memory.store("profile_summary", refined)
        self.memory.store("refinement_count", refinement_count + 1)

        return {
            "profile_summary": refined,
            "phase": "feedback",
        }

    def _generate_path_and_briefing(self) -> dict:
        """
        Internal: Scout verifies resources, Navigator generates path,
        PDF generator creates briefing.
        """
        # Scout gathers and verifies resources
        verified = self.scout.gather_resources(domain="ai-foundations")

        # Navigator generates personalized path
        profile = self.memory.retrieve("profile_summary") or ""
        learning_path = self.navigator.generate_learning_path(profile, verified)

        # Generate PDF
        pdf_url = generate_command_briefing(learning_path)

        # Clear session — stateless
        self.memory.clear()
        logger.info("[orchestrator] Session complete, memory cleared")

        return {
            "phase": "complete",
            "learning_path": learning_path,
            "pdf_url": pdf_url,
        }
