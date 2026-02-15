"""
Directory Loader Tool — Reads directory.json from S3.

Loads the curated resource directory. In local dev, reads from
the filesystem. In production, reads from S3.

Returns the parsed JSON as a Python dict.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("clew.tool.loader")


def load_directory_from_file(filepath: str | Path | None = None) -> dict:
    """
    Load directory.json from local filesystem (dev mode).

    Args:
        filepath: Path to directory.json. Defaults to data/directory.json
                  relative to project root.

    Returns:
        Parsed directory dict.
    """
    if filepath is None:
        # Default: project_root/data/directory.json
        filepath = Path(__file__).parent.parent.parent / "data" / "directory.json"

    filepath = Path(filepath)
    if not filepath.exists():
        logger.error("[tool:loader] Directory file not found: %s", filepath)
        return {"resources": []}

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(
        "[tool:loader] Loaded directory v%s with %d resources",
        data.get("version", "unknown"),
        len(data.get("resources", [])),
    )
    return data


def load_directory_from_s3(bucket: str, key: str) -> dict:
    """
    Load directory.json from S3 (staging/production).

    Args:
        bucket: S3 bucket name.
        key: S3 object key for directory.json.

    Returns:
        Parsed directory dict.
    """
    import boto3
    
    # Input validation
    if not bucket or not isinstance(bucket, str):
        logger.error("[tool:loader] Invalid bucket parameter")
        return {"resources": []}
    if not key or not isinstance(key, str):
        logger.error("[tool:loader] Invalid key parameter")
        return {"resources": []}
    
    try:
        # Respect AWS_ENDPOINT_URL for LocalStack/MinIO in dev
        endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        s3_config = {"endpoint_url": endpoint_url} if endpoint_url else {}
        s3 = boto3.client("s3", **s3_config)
        
        logger.info("[tool:loader] Loading directory from s3://%s/%s", bucket, key)
        
        response = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(response["Body"].read().decode("utf-8"))
        
        logger.info(
            "[tool:loader] Loaded directory v%s with %d resources from S3",
            data.get("version", "unknown"),
            len(data.get("resources", [])),
        )
        return data
    except Exception as e:
        logger.error("[tool:loader] Failed to load from S3: %s", e)
        return {"resources": []}


def load_directory() -> dict:
    """
    Factory: loads directory from appropriate source based on environment.
    """
    from config.settings import load_settings
    
    settings = load_settings()
    
    if settings.env.value == "dev":
        return load_directory_from_file()
    else:
        return load_directory_from_s3(settings.s3.bucket_name, settings.s3.directory_key)
