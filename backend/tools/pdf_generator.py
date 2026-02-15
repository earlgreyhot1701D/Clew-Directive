"""
PDF Generator Tool — Creates Command Briefing PDFs via WeasyPrint.

Flow:
    1. Receives structured learning path from Navigator
    2. Renders HTML using Jinja2 template (command_briefing.html)
    3. Converts HTML to PDF via WeasyPrint (preserves clickable links)
    4. In production: uploads to S3, returns pre-signed URL
    5. In dev: saves to /tmp, returns local path

The HTML template preserves the retro-terminal aesthetic with
WCAG 2.1 AA compliant contrast ratios.
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("clew.tool.pdf")

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Try to import WeasyPrint, but allow graceful degradation for testing
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning("[tool:pdf] WeasyPrint not available: %s", e)
    WEASYPRINT_AVAILABLE = False
    HTML = None


def generate_command_briefing(learning_path: dict) -> str:
    """
    Generate a Command Briefing PDF from the Navigator's learning path.

    Args:
        learning_path: Dict with structure from NavigatorAgent.generate_learning_path():
            {
                "profile_summary": str,
                "recommended_resources": list[dict],
                "approach_guidance": str,
                "total_estimated_hours": int,
            }

    Returns:
        URL or filepath to the generated PDF.
    """
    logger.info("[tool:pdf] Generating Command Briefing PDF")

    try:
        # Prepare template data
        template_data = {
            "profile_summary": learning_path.get("profile_summary", ""),
            "recommended_resources": learning_path.get("recommended_resources", []),
            "approach_guidance": learning_path.get("approach_guidance", ""),
            "total_estimated_hours": learning_path.get("total_estimated_hours", 0),
            "generated_date": datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
            "verification_date": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        }

        # Render HTML template
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        template = env.get_template("command_briefing.html")
        html_content = template.render(**template_data)
        
        logger.info("[tool:pdf] Template rendered successfully")

        # Convert HTML to PDF
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint is not available. Install GTK libraries for PDF generation.")
        
        pdf_bytes = HTML(string=html_content).write_pdf()
        logger.info("[tool:pdf] PDF generated: %d bytes", len(pdf_bytes))

        # Generate unique filename
        filename = f"command-briefing-{uuid.uuid4().hex[:8]}.pdf"

        # Determine environment and save accordingly
        env_name = os.getenv("CD_ENVIRONMENT", "dev")

        if env_name in ("prod", "staging"):
            # Upload to S3 and return presigned URL
            pdf_url = _upload_to_s3(pdf_bytes, filename)
            logger.info("[tool:pdf] Uploaded to S3: %s", pdf_url)
            return pdf_url
        else:
            # Save to local /tmp for development
            pdf_path = _save_to_tmp(pdf_bytes, filename)
            logger.info("[tool:pdf] Saved locally: %s", pdf_path)
            return pdf_path

    except Exception as e:
        logger.error("[tool:pdf] PDF generation failed: %s", e, exc_info=True)
        raise


def generate_pdf(learning_path: dict) -> bytes:
    """
    Generate PDF bytes directly (for testing).

    Args:
        learning_path: Dict with learning path structure.

    Returns:
        PDF as bytes.
    """
    logger.info("[tool:pdf] Generating PDF bytes")

    try:
        # Prepare template data
        template_data = {
            "profile_summary": learning_path.get("profile_summary", ""),
            "recommended_resources": learning_path.get("recommended_resources", []),
            "approach_guidance": learning_path.get("approach_guidance", ""),
            "total_estimated_hours": learning_path.get("total_estimated_hours", 0),
            "generated_date": datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
            "verification_date": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        }

        # Render HTML template
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        template = env.get_template("command_briefing.html")
        html_content = template.render(**template_data)

        # Convert HTML to PDF
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint is not available. Install GTK libraries for PDF generation.")
        
        pdf_bytes = HTML(string=html_content).write_pdf()
        logger.info("[tool:pdf] PDF generated: %d bytes", len(pdf_bytes))

        return pdf_bytes

    except Exception as e:
        logger.error("[tool:pdf] PDF generation failed: %s", e, exc_info=True)
        raise


def render_html(learning_path: dict) -> str:
    """
    Render HTML template without converting to PDF (for testing).

    Args:
        learning_path: Dict with learning path structure.

    Returns:
        Rendered HTML as string.
    """
    template_data = {
        "profile_summary": learning_path.get("profile_summary", ""),
        "recommended_resources": learning_path.get("recommended_resources", []),
        "approach_guidance": learning_path.get("approach_guidance", ""),
        "total_estimated_hours": learning_path.get("total_estimated_hours", 0),
        "generated_date": datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
        "verification_date": datetime.now(timezone.utc).strftime("%B %d, %Y"),
    }

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("command_briefing.html")
    return template.render(**template_data)


def _upload_to_s3(pdf_bytes: bytes, filename: str) -> str:
    """
    Upload PDF to S3 and return a pre-signed URL (24 hour expiry).
    
    Args:
        pdf_bytes: PDF content as bytes.
        filename: Name for the PDF file.
    
    Returns:
        Pre-signed S3 URL (valid for 24 hours).
    """
    import boto3
    from botocore.exceptions import ClientError

    try:
        s3_client = boto3.client("s3")
        bucket_name = os.getenv("PDF_BUCKET_NAME", "clew-directive-pdfs")
        
        # Upload with 24-hour lifecycle policy
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=pdf_bytes,
            ContentType="application/pdf",
            # Tag for lifecycle policy (auto-delete after 24h)
            Tagging="temporary=true",
        )
        
        # Generate presigned URL (valid for 24 hours)
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": filename},
            ExpiresIn=86400,  # 24 hours
        )
        
        logger.info("[tool:pdf] Uploaded to S3: %s/%s", bucket_name, filename)
        return presigned_url
        
    except ClientError as e:
        logger.error("[tool:pdf] S3 upload failed: %s", e, exc_info=True)
        # Fallback to local save
        return _save_to_tmp(pdf_bytes, filename)


def _save_to_tmp(pdf_bytes: bytes, filename: str) -> str:
    """
    Save PDF to /tmp for local development.
    
    Args:
        pdf_bytes: PDF content as bytes.
        filename: Name for the PDF file.
    
    Returns:
        Local file path.
    """
    # Use current directory's tmp folder for Windows compatibility
    tmp_dir = Path.cwd() / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    
    tmp_path = tmp_dir / filename
    tmp_path.write_bytes(pdf_bytes)
    logger.info("[tool:pdf] Saved PDF to %s", tmp_path)
    return str(tmp_path)


