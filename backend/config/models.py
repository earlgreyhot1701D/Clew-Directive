"""
Tiered model configuration for Clew Directive agents.

Scout uses the cheapest model (Nova Micro) for simple verification tasks.
Navigator uses Amazon Nova 2 Lite (us.amazon.nova-2-lite-v1:0) for reasoning.
  Originally planned for Claude Sonnet 4.5, but switched mid-build to Nova 2 Lite
  for instant regional availability and significantly lower cost — Claude required
  cross-region inference profiles and approval delays that blocked deployment.
Curator reuses Scout's model for weekly freshness checks.

Cost per 1K tokens (on-demand, us-east-1):
  Nova Micro:        $0.000035 input / $0.00014 output
  Nova 2 Lite:       ~$0.0001 input  / ~$0.0004 output
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
# Using Amazon Nova 2 Lite with regional prefix for instant availability
# Increased from 2000 to 4000 — 28 resources + profile + JSON schema requires
# more output tokens to complete personalized path generation without hitting
# MaxTokensReachedException. Nova 2 Lite supports up to 5000.
NAVIGATOR_MODEL = ModelTier(
    model_id="us.amazon.nova-2-lite-v1:0",
    max_tokens=4000,
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
