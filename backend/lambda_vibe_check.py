"""
Lambda Handler: Vibe Check Processing

Endpoint: POST /vibe-check
Purpose: Process Vibe Check responses and return profile summary

Input:
    {
        "vibe_check_responses": {
            "skepticism": "...",
            "goal": "...",
            "learning_style": "...",
            "context": "..."
        }
    }

Output:
    {
        "profile": "You're approaching AI with curiosity..."
    }
"""

import json
import logging

from agents.orchestrator import Orchestrator
from exceptions import ClewException, ValidationError

logger = logging.getLogger("clew.lambda.vibe_check")

# Allowed CORS origins — must match API Gateway allowedOrigins
ALLOWED_ORIGINS = {
    "https://clewdirective.com",
    "https://www.clewdirective.com",
    "http://localhost:3000"
}


def _cors_headers(event: dict) -> dict:
    """Return CORS headers with origin validated against allowlist."""
    origin = (event.get("headers") or {}).get("origin", "")
    # Also check Origin header with capital O (API Gateway normalizes to lowercase)
    if not origin:
        origin = (event.get("headers") or {}).get("Origin", "")
    allowed = origin if origin in ALLOWED_ORIGINS or origin.endswith(".amplifyapp.com") else ""
    return {
        "Access-Control-Allow-Origin": allowed,
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
    }


# Required Vibe Check fields
REQUIRED_FIELDS = ["skepticism", "goal", "learning_style", "context"]


def lambda_handler(event, context):
    """
    AWS Lambda entry point for Vibe Check processing.

    Args:
        event: API Gateway event with body containing vibe_check_responses
        context: Lambda context object

    Returns:
        API Gateway response with profile summary or error
    """
    logger.info("[lambda:vibe_check] Request received")

    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        vibe_check_responses = body.get("vibe_check_responses", {})

        # Validate all required fields present
        missing_fields = [f for f in REQUIRED_FIELDS if f not in vibe_check_responses]
        if missing_fields:
            raise ValidationError(
                "vibe_check_responses",
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Validate no empty fields
        empty_fields = [
            f for f in REQUIRED_FIELDS
            if not vibe_check_responses.get(f) or not str(vibe_check_responses[f]).strip()
        ]
        if empty_fields:
            raise ValidationError(
                "vibe_check_responses",
                f"Empty fields not allowed: {', '.join(empty_fields)}"
            )

        # Process Vibe Check
        logger.info("[lambda:vibe_check] Processing Vibe Check responses")
        
        # Initialize knowledge interface and agents
        from interfaces.knowledge_interface import create_knowledge
        from tools.directory_loader import load_directory
        from agents.scout import ScoutAgent
        from agents.navigator import NavigatorAgent
        
        # Load directory data
        directory_data = load_directory()
        knowledge = create_knowledge(directory_data)
        
        # Scout without resource_verifier — trusts Curator's weekly verification
        # User requests should NOT perform runtime URL checks (would cause timeout)
        scout = ScoutAgent(knowledge=knowledge)  # resource_verifier=None by default
        navigator = NavigatorAgent()
        orchestrator = Orchestrator(scout=scout, navigator=navigator)
        profile = orchestrator.process_vibe_check(vibe_check_responses)

        logger.info("[lambda:vibe_check] Profile generated successfully")
        return {
            "statusCode": 200,
            "headers": _cors_headers(event),
            "body": json.dumps({"profile": profile}),
        }

    except json.JSONDecodeError as e:
        logger.warning("[lambda:vibe_check] Invalid JSON: %s", e)
        return {
            "statusCode": 400,
            "headers": _cors_headers(event),
            "body": json.dumps({
                "error": "Invalid JSON in request body",
                "retry_allowed": False,
            }),
        }

    except ClewException as e:
        # Our custom exceptions have user-friendly messages
        logger.warning("[lambda:vibe_check] ClewException: %s", e.technical_message)
        return {
            "statusCode": e.http_status,
            "headers": _cors_headers(event),
            "body": json.dumps({
                "error": e.user_message,
                "retry_allowed": e.retry_allowed,
            }),
        }

    except Exception as e:
        logger.error("[lambda:vibe_check] Unexpected error: %s", e, exc_info=True)
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
