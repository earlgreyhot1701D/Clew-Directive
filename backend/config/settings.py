"""
Environment-aware configuration for Clew Directive.

All environment-specific values are centralized here.
No hardcoded config anywhere else in the codebase.
"""

import os
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    DEV = "dev"          # Local Docker, mocked Bedrock
    STAGING = "staging"  # Real AWS, lower limits
    PRODUCTION = "prod"  # Full deployment


@dataclass(frozen=True)
class BedrockConfig:
    """Bedrock model configuration."""
    region: str = "us-east-1"
    scout_model_id: str = "amazon.nova-micro-v1:0"
    navigator_model_id: str = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
    curator_model_id: str = "amazon.nova-micro-v1:0"
    max_scout_tokens: int = 500
    max_navigator_tokens: int = 2000
    max_curator_tokens: int = 500


@dataclass(frozen=True)
class S3Config:
    """S3 configuration for directory.json and temporary PDF storage."""
    bucket_name: str = ""
    directory_key: str = "data/directory.json"
    pdf_prefix: str = "tmp/briefings/"
    pdf_expiry_seconds: int = 3600  # Pre-signed URL expires in 1 hour


@dataclass(frozen=True)
class CostLimits:
    """Cost control boundaries."""
    max_daily_requests: int = 200
    max_tokens_per_session: int = 5000
    lambda_timeout_seconds: int = 30
    lambda_memory_mb: int = 512


@dataclass(frozen=True)
class Settings:
    """Root configuration object."""
    env: Environment = Environment.DEV
    bedrock: BedrockConfig = field(default_factory=BedrockConfig)
    s3: S3Config = field(default_factory=S3Config)
    cost_limits: CostLimits = field(default_factory=CostLimits)
    log_level: str = "INFO"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])


def load_settings() -> Settings:
    """
    Load settings from environment variables.
    Falls back to defaults for local development.
    """
    env = Environment(os.getenv("CD_ENVIRONMENT", "dev"))

    bedrock = BedrockConfig(
        region=os.getenv("AWS_REGION", "us-east-1"),
        scout_model_id=os.getenv("CD_SCOUT_MODEL", "amazon.nova-micro-v1:0"),
        navigator_model_id=os.getenv(
            "CD_NAVIGATOR_MODEL",
            "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        ),
    )

    s3 = S3Config(
        bucket_name=os.getenv("CD_S3_BUCKET", "clew-directive-data"),
        directory_key=os.getenv("CD_DIRECTORY_KEY", "data/directory.json"),
    )

    cost_limits = CostLimits(
        max_daily_requests=int(os.getenv("CD_MAX_DAILY_REQUESTS", "200")),
        max_tokens_per_session=int(os.getenv("CD_MAX_TOKENS_SESSION", "5000")),
    )

    cors = os.getenv("CD_CORS_ORIGINS", "http://localhost:3000").split(",")

    return Settings(
        env=env,
        bedrock=bedrock,
        s3=s3,
        cost_limits=cost_limits,
        log_level=os.getenv("CD_LOG_LEVEL", "DEBUG" if env == Environment.DEV else "INFO"),
        cors_origins=cors,
    )
