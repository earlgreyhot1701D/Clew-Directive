"""
Lambda Handler: Briefing Generation

Endpoint: POST /generate-briefing
Purpose: Generate learning path and Command Briefing PDF

Input:
    {
        "approved_profile": "You're approaching AI with curiosity..."
    }

Output:
    {
        "learning_path": [...],
        "total_hours": 45,
        "next_steps": "After completing these foundational courses...",
        "pdf_url": "https://s3.amazonaws.com/bucket/briefing-abc123.pdf?presigned"
    }
"""

import json
import logging

from agents.orchestrator import Orchestrator
from tools.pdf_generator import generate_command_briefing
from exceptions import ClewException, ValidationError, PDFGenerationError

logger = logging.getLogger("clew.lambda.generate_briefing")

# CORS headers for all responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
}


def lambda_handler(event, context):
    """
    AWS Lambda entry point for briefing generation.

    Args:
        event: API Gateway event with body containing approved_profile
        context: Lambda context object

    Returns:
        API Gateway response with learning path and PDF URL or error
    """
    logger.info("[lambda:generate_briefing] Request received")

    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        approved_profile = body.get("approved_profile", "")

        # Validate approved_profile present and non-empty
        if not approved_profile or not approved_profile.strip():
            raise ValidationError("approved_profile", "Cannot be empty")

        # Generate learning path
        logger.info("[lambda:generate_briefing] Generating learning path")
        
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
        learning_path_data = orchestrator.generate_briefing(approved_profile)

        # Generate PDF
        logger.info("[lambda:generate_briefing] Generating Command Briefing PDF")
        try:
            pdf_url = generate_command_briefing(learning_path_data)
            learning_path_data["pdf_url"] = pdf_url
            logger.info("[lambda:generate_briefing] PDF generated: %s", pdf_url[:100])
        except Exception as pdf_error:
            logger.warning(
                "[lambda:generate_briefing] PDF generation failed: %s",
                pdf_error,
                exc_info=True,
            )
            # Continue without PDF - user can still see path in UI
            learning_path_data["pdf_url"] = None
            learning_path_data["pdf_warning"] = (
                "We couldn't generate your PDF, but your learning path is ready below. "
                "You can still access all the links here."
            )

        logger.info("[lambda:generate_briefing] Briefing generated successfully")
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(learning_path_data),
        }

    except json.JSONDecodeError as e:
        logger.warning("[lambda:generate_briefing] Invalid JSON: %s", e)
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "error": "Invalid JSON in request body",
                "retry_allowed": False,
            }),
        }

    except ClewException as e:
        logger.warning("[lambda:generate_briefing] ClewException: %s", e.technical_message)
        return {
            "statusCode": e.http_status,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "error": e.user_message,
                "retry_allowed": e.retry_allowed,
            }),
        }

    except Exception as e:
        logger.error("[lambda:generate_briefing] Unexpected error: %s", e, exc_info=True)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "error": (
                    "We encountered an unexpected error. "
                    "Please try again or contact support if the problem persists."
                ),
                "retry_allowed": True,
            }),
        }
