"""
Lambda Handler: Profile Refinement

Endpoint: POST /refine-profile
Purpose: Refine profile based on user correction

Input:
    {
        "original_profile": "You're approaching AI...",
        "user_correction": "Actually I'm more hands-on...",
        "refinement_count": 0  # Optional, defaults to 0 for backward compatibility
    }

Output:
    {
        "profile": "You're approaching AI with hands-on curiosity..."
    }
"""

import json
import logging

from agents.orchestrator import Orchestrator
from exceptions import ClewException, ValidationError

logger = logging.getLogger("clew.lambda.refine_profile")

# Allowed CORS origins — must match API Gateway allowedOrigins
ALLOWED_ORIGINS = {
    "https://clewdirective.com",
    "https://www.clewdirective.com",
    "http://localhost:3000"
}


def _cors_headers(event: dict) -> dict:
    """Return CORS headers with origin validated against allowlist."""
    origin = (event.get("headers") or {}).get("origin", "")
    if not origin:
        origin = (event.get("headers") or {}).get("Origin", "")
    allowed = origin if origin in ALLOWED_ORIGINS or origin.endswith(".amplifyapp.com") else ""
    return {
        "Access-Control-Allow-Origin": allowed,
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
    }


def lambda_handler(event, context):
    """
    AWS Lambda entry point for profile refinement.

    Args:
        event: API Gateway event with body containing original_profile and user_correction
        context: Lambda context object

    Returns:
        API Gateway response with revised profile or error
    """
    logger.info("[lambda:refine_profile] Request received")

    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        original_profile = body.get("original_profile", "")
        user_correction = body.get("user_correction", "")

        # Validate original_profile present and non-empty
        if not original_profile or not original_profile.strip():
            raise ValidationError("original_profile", "Cannot be empty")

        # Validate user_correction present and non-empty
        if not user_correction or not user_correction.strip():
            raise ValidationError("user_correction", "Cannot be empty")

        # Extract refinement count (defaults to 0 for backward compatibility)
        refinement_count = body.get("refinement_count", 0)

        # Enforce one-refinement limit
        if refinement_count >= 1:
            raise ValidationError(
                "refinement_count",
                "Profile has already been refined. Please proceed to generate your learning plan."
            )

        # Process refinement
        logger.info("[lambda:refine_profile] Processing profile refinement")
        
        # Initialize knowledge interface and agents
        from interfaces.knowledge_interface import create_knowledge
        from tools.directory_loader import load_directory
        from agents.scout import ScoutAgent
        from agents.navigator import NavigatorAgent
        
        # Load directory data
        directory_data = load_directory()
        knowledge = create_knowledge(directory_data)
        
        scout = ScoutAgent(knowledge=knowledge)
        navigator = NavigatorAgent()
        orchestrator = Orchestrator(scout=scout, navigator=navigator)
        revised_profile = orchestrator.process_refinement(original_profile, user_correction)

        logger.info("[lambda:refine_profile] Profile refined successfully")
        return {
            "statusCode": 200,
            "headers": _cors_headers(event),
            "body": json.dumps({"profile": revised_profile}),
        }

    except json.JSONDecodeError as e:
        logger.warning("[lambda:refine_profile] Invalid JSON: %s", e)
        return {
            "statusCode": 400,
            "headers": _cors_headers(event),
            "body": json.dumps({
                "error": "Invalid JSON in request body",
                "retry_allowed": False,
            }),
        }

    except ClewException as e:
        logger.warning("[lambda:refine_profile] ClewException: %s", e.technical_message)
        return {
            "statusCode": e.http_status,
            "headers": _cors_headers(event),
            "body": json.dumps({
                "error": e.user_message,
                "retry_allowed": e.retry_allowed,
            }),
        }

    except Exception as e:
        logger.error("[lambda:refine_profile] Unexpected error: %s", e, exc_info=True)
        return {
            "statusCode": 500,
            "headers": _cors_headers(event),
            "body": json.dumps({
                "error": (
                    "We encountered an unexpected error. "
                    "Please try again or contact support if the problem persists."
                ),
                "retry_allowed": True,
            }),
        }
