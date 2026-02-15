"""
Tiered model configuration for Clew Directive agents.

Scout uses the cheapest model (Nova Micro) for simple verification tasks.
Navigator uses the most capable model (Claude 4 Sonnet) for reasoning.
Curator reuses Scout's model for weekly freshness checks.

Cost per 1K tokens (on-demand, us-east-1):
  Nova Micro:       $0.000035 input / $0.00014 output
  Claude 4 Sonnet:  ~$0.003 input  / ~$0.015 output
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelTier:
    """Configuration for a single model tier."""
    model_id: str
    max_tokens: int
    temperature: float
    description: str


# Scout: cheap, fast, sufficient for URL checks and simple matching
SCOUT_MODEL = ModelTier(
    model_id="amazon.nova-micro-v1:0",
    max_tokens=500,
    temperature=0.0,
    description="URL verification and simple content checks",
)

# Navigator: capable, reasoning-heavy, generates personalized paths
# Using cross-region inference profile for on-demand throughput support
NAVIGATOR_MODEL = ModelTier(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    max_tokens=2000,
    temperature=0.7,
    description="Profile analysis, path reasoning, briefing generation",
)

# Curator: reuses Scout tier for weekly automated checks
CURATOR_MODEL = ModelTier(
    model_id="amazon.nova-micro-v1:0",
    max_tokens=500,
    temperature=0.0,
    description="Weekly resource freshness verification",
)
