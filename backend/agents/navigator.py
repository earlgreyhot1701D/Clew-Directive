"""
Navigator Agent — Reasoning and path generation using Amazon Nova 2 Lite.

Responsibilities:
    - Analyze Vibe Check responses to generate a learner profile summary
    - Match the profile against verified resources to build a personalized path
    - Generate reasoning for why each resource was selected
    - Produce structured output for the Command Briefing PDF

Uses Amazon Nova 2 Lite (us.amazon.nova-2-lite-v1:0). Originally planned for
Claude Sonnet 4.5, but pivoted mid-build to Nova 2 Lite because it is instantly
available in all AWS regions without cross-region inference profiles, and its
lower token cost keeps per-briefing spend well within the $200 credit budget.
"""

import asyncio
import json
import logging
import re
from typing import Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from strands import Agent
from config.models import NAVIGATOR_MODEL
from exceptions import (
    BedrockTimeoutError,
    BedrockThrottleError,
    InvalidLLMResponseError,
)

logger = logging.getLogger("clew.agent.navigator")

# Timeout for Bedrock calls (seconds)
BEDROCK_TIMEOUT = 30


def fix_capitalization(text: str) -> str:
    """
    Fix common capitalization issues in generated text.
    
    Handles:
    - Sentence starts (after . ! ? followed by space)
    - Standalone "I" and I-contractions (I've, I'm, I'll, I'd, I're)
    - AI acronym (should always be uppercase)
    - First character of entire text
    
    Args:
        text: The text to fix
        
    Returns:
        Text with corrected capitalization
    """
    if not text:
        return text
    
    # Fix sentence starts (after . ! ? followed by space)
    sentences = re.split(r'([.!?]\s+)', text)
    fixed = []
    for i, part in enumerate(sentences):
        if i % 2 == 0 and part:  # Text parts, not delimiters
            part = part[0].upper() + part[1:] if part else part
        fixed.append(part)
    text = ''.join(fixed)
    
    # Fix standalone I and I-contractions
    text = re.sub(r'\bi\b', 'I', text)
    text = re.sub(r"\bi'(ve|m|ll|d|re)\b", r"I'\1", text, flags=re.IGNORECASE)
    
    # Fix AI acronym (should always be uppercase)
    text = re.sub(r'\bai\b', 'AI', text, flags=re.IGNORECASE)
    
    # Ensure first character of entire text is capitalized
    if text:
        text = text[0].upper() + text[1:]
    
    return text


# Vibe Check question definitions
VIBE_CHECK_QUESTIONS = [
    {
        "id": "skepticism",
        "question": "Which best describes your current take on AI?",
        "options": [
            "Skeptical — I want to understand what's real",
            "Curious but haven't started learning",
            "I've dabbled and want more structure",
            "I use AI tools already and want to go deeper",
        ],
    },
    {
        "id": "goal",
        "question": "If AI could help you with one thing, what would it be?",
        "options": [
            "Understand what AI actually is and isn't",
            "Use AI tools to be better at my current job",
            "Build things with AI",
            "Make career decisions about AI",
        ],
    },
    {
        "id": "learning_style",
        "question": "How do you prefer to learn new things?",
        "options": [
            "Reading and thinking at my own pace",
            "Watching videos with examples",
            "Hands-on projects and exercises",
            "Structured courses with a clear path",
        ],
    },
    {
        "id": "context",
        "question": "What's your professional context?",
        "options": [
            "Education / Academia",
            "Business / Marketing / Operations",
            "Technical / Engineering / IT",
            "Creative / Design / Media",
            "Other / Career switching",
        ],
    },
]


class NavigatorAgent:
    """
    Navigator agent: reasons over user profile and curated resources
    to generate a personalized learning path.

    The Navigator is the only agent that uses Amazon Nova 2 Lite
    (chosen over Claude Sonnet 4.5 for regional availability and cost).
    It handles two key tasks:
        1. Profile synthesis — turning Vibe Check answers into a narrative
        2. Path generation — matching the profile to sequenced resources
    """

    def __init__(self, bedrock_client: Any = None) -> None:
        self.model = NAVIGATOR_MODEL
        self.bedrock_client = bedrock_client
        
        # Initialize Strands agent for profile synthesis
        self.agent = Agent(
            model=self.model.model_id,
            system_prompt="""You are an empathetic AI learning advisor. Your role is to understand 
            learners' backgrounds and goals, then guide them to the right resources. You communicate 
            in a warm, supportive tone using second person ("you"). You're knowledgeable but never 
            condescending.""",
        )

    def synthesize_profile(self, vibe_check_responses: dict) -> str:
        """
        Generate a 3-4 sentence profile summary from Vibe Check answers.

        This is shown to the user in the feedback loop:
        "Does this sound like you?"

        Args:
            vibe_check_responses: Dict mapping question IDs to selected option text.
                Example: {"skepticism": "Curious but haven't started", ...}

        Returns:
            A natural language profile summary string.
            
        Raises:
            BedrockTimeoutError: If Bedrock call exceeds timeout
            BedrockThrottleError: If rate limit exceeded
            InvalidLLMResponseError: If response is unparseable
        """
        logger.info("[agent:navigator] Synthesizing profile from Vibe Check")

        # Build the prompt for profile synthesis
        prompt = f"""Based on these responses from a learner, create a 3-4 sentence profile summary.

Vibe Check Responses:
- Current take on AI: {vibe_check_responses.get('skepticism', 'Not specified')}
- Primary goal: {vibe_check_responses.get('goal', 'Not specified')}
- Learning style: {vibe_check_responses.get('learning_style', 'Not specified')}
- Professional context: {vibe_check_responses.get('context', 'Not specified')}

Requirements:
- Write in second person ("You're approaching AI...")
- Be empathetic and supportive, not clinical
- Reflect their skepticism level accurately
- Note their goal, learning preference, and professional context
- Keep it to 3-4 sentences
- Make it feel personal and encouraging

Generate the profile summary:"""

        try:
            # Uses ThreadPoolExecutor instead of asyncio.run() to avoid RuntimeError if an event loop is already running (Strands SDK issue)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self.agent, prompt)
                try:
                    response = future.result(timeout=BEDROCK_TIMEOUT)
                except FuturesTimeout:
                    raise BedrockTimeoutError("profile_synthesis", BEDROCK_TIMEOUT)
            
            # Extract text from response
            if hasattr(response, 'output'):
                profile = response.output.strip()
            elif hasattr(response, 'content'):
                profile = str(response.content).strip()
            else:
                profile = str(response).strip()
            
            # Validate response
            if not profile or len(profile) < 50:
                raise InvalidLLMResponseError(
                    "profile_synthesis",
                    f"Response too short: {len(profile)} chars"
                )
            
            # Fix capitalization issues before returning
            profile = fix_capitalization(profile)
            
            logger.info("[agent:navigator] Profile synthesized: %d chars", len(profile))
            return profile
            
        except asyncio.TimeoutError:
            logger.error("[agent:navigator] Profile synthesis timed out after %ds", BEDROCK_TIMEOUT)
            raise BedrockTimeoutError("profile_synthesis", BEDROCK_TIMEOUT)
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for throttling
            if "throttl" in error_str or "rate limit" in error_str or "429" in error_str:
                logger.error("[agent:navigator] Bedrock throttling detected")
                raise BedrockThrottleError()
            
            # Check for timeout
            if "timeout" in error_str or "timed out" in error_str:
                logger.error("[agent:navigator] Bedrock timeout detected")
                raise BedrockTimeoutError("profile_synthesis", BEDROCK_TIMEOUT)
            
            # Generic error - use fallback
            logger.error("[agent:navigator] Profile synthesis failed: %s", e, exc_info=True)
            logger.warning("[agent:navigator] Using fallback profile generation")
            return self._fallback_profile(vibe_check_responses)

    def refine_profile(self, original_profile: str, user_correction: str) -> str:
        """
        Re-generate profile incorporating user's correction.

        Called when user clicks "Not quite" in the feedback loop.
        Capped at one refinement — second rejection resets the flow.

        Args:
            original_profile: The first profile summary that was rejected.
            user_correction: Free text from user explaining what was wrong.

        Returns:
            Updated profile summary string.
            
        Raises:
            BedrockTimeoutError: If Bedrock call exceeds timeout
            BedrockThrottleError: If rate limit exceeded
        """
        logger.info("[agent:navigator] Refining profile with user correction")

        prompt = f"""A learner was shown this profile summary, but said it wasn't quite right:

Original Profile:
{original_profile}

Their Feedback:
{user_correction}

Please revise the profile to incorporate their feedback. Keep it to 3-4 sentences, 
use second person, and maintain an empathetic tone. Don't start from scratch - 
update the existing profile based on what they said.

Revised profile:"""

        try:
            # Uses ThreadPoolExecutor instead of asyncio.run() to avoid RuntimeError if an event loop is already running (Strands SDK issue)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self.agent, prompt)
                try:
                    response = future.result(timeout=BEDROCK_TIMEOUT)
                except FuturesTimeout:
                    raise BedrockTimeoutError("profile_refinement", BEDROCK_TIMEOUT)
            
            # Extract text from response
            if hasattr(response, 'output'):
                refined_profile = response.output.strip()
            elif hasattr(response, 'content'):
                refined_profile = str(response.content).strip()
            else:
                refined_profile = str(response).strip()
            
            # Validate response
            if not refined_profile or len(refined_profile) < 50:
                logger.warning("[agent:navigator] Refined profile too short, using original")
                return original_profile
            
            # Fix capitalization issues before returning
            refined_profile = fix_capitalization(refined_profile)
            
            logger.info("[agent:navigator] Profile refined: %d chars", len(refined_profile))
            return refined_profile
            
        except asyncio.TimeoutError:
            logger.error("[agent:navigator] Profile refinement timed out after %ds", BEDROCK_TIMEOUT)
            raise BedrockTimeoutError("profile_refinement", BEDROCK_TIMEOUT)
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for throttling
            if "throttl" in error_str or "rate limit" in error_str or "429" in error_str:
                logger.error("[agent:navigator] Bedrock throttling detected")
                raise BedrockThrottleError()
            
            # Check for timeout
            if "timeout" in error_str or "timed out" in error_str:
                logger.error("[agent:navigator] Bedrock timeout detected")
                raise BedrockTimeoutError("profile_refinement", BEDROCK_TIMEOUT)
            
            # Generic error - return original with note
            logger.error("[agent:navigator] Profile refinement failed: %s", e, exc_info=True)
            logger.warning("[agent:navigator] Returning original profile with note")
            return f"{original_profile}\n\n(Note: {user_correction})"
    
    def _fallback_profile(self, vibe_check_responses: dict) -> str:
        """Fallback profile generation if Strands call fails."""
        skepticism = vibe_check_responses.get('skepticism', 'interested in AI')
        goal = vibe_check_responses.get('goal', 'learn about AI')
        style = vibe_check_responses.get('learning_style', 'at your own pace')
        context = vibe_check_responses.get('context', 'your field')
        
        profile = f"""You're approaching AI with a {skepticism.lower()} mindset, which is exactly 
        the right place to start. Your main goal is to {goal.lower()}, and you prefer learning 
        by {style.lower()}. Given your background in {context.lower()}, we'll focus on resources 
        that connect AI concepts to practical applications in your domain."""
        
        return fix_capitalization(profile)

    def generate_learning_path(
        self,
        profile_summary: str,
        verified_resources: list[dict],
    ) -> dict:
        """
        Generate a personalized, sequenced learning path.

        Args:
            profile_summary: The confirmed profile summary.
            verified_resources: List of Scout-verified resource dicts.

        Returns:
            Dict with structure:
            {
                "profile_summary": str,
                "recommended_resources": [
                    {
                        "resource_id": str,
                        "resource_name": str,
                        "resource_url": str,
                        "provider": str,
                        "provider_url": str,
                        "why_for_you": str,    # 1-2 sentences of reasoning
                        "difficulty": str,
                        "estimated_hours": int,
                        "format": str,
                        "free_model": str,
                        "sequence_note": str,  # "Start here" / "Take after X" / "Optional"
                        "sequence_order": int,
                    }
                ],
                "approach_guidance": str,       # "What to Expect" section
                "total_estimated_hours": int,
            }
        """
        logger.info(
            "[agent:navigator] Generating path from %d resources",
            len(verified_resources),
        )

        # Build resource catalog for the prompt
        resource_catalog = self._format_resource_catalog(verified_resources)
        
        # Build the prompt for path generation
        prompt = f"""You are creating a personalized learning path for this learner:

LEARNER PROFILE:
{profile_summary}

AVAILABLE RESOURCES:
{resource_catalog}

TASK:
Select 4-6 resources from the catalog above and sequence them into a learning path.

REQUIREMENTS:
1. Select 4-6 resources (not more, not less)
2. Sequence from easier to harder, respecting prerequisites
3. Total estimated hours should be 30-60 hours
4. For each resource, explain WHY it's right for THIS learner (2-3 sentences)
5. Provide approach guidance (2-3 sentences on how to tackle this path)
6. Weight higher authority_tier resources (tier 1 > tier 2 > tier 3)
7. Match learning style from profile (courses for structured learners, projects for hands-on, etc.)

OUTPUT FORMAT (JSON):
{{
  "recommended_resources": [
    {{
      "resource_id": "exact-id-from-catalog",
      "resource_name": "exact name from catalog",
      "resource_url": "exact URL from catalog",
      "provider": "exact provider from catalog",
      "provider_url": "exact provider_url from catalog",
      "why_for_you": "2-3 sentences explaining why this resource fits THIS learner",
      "difficulty": "exact difficulty from catalog",
      "estimated_hours": exact number from catalog,
      "format": "exact format from catalog",
      "free_model": "exact free_model from catalog",
      "sequence_note": "Start here" or "Take after [previous resource name]" or "Optional",
      "sequence_order": 1
    }}
  ],
  "approach_guidance": "2-3 sentences on how to approach this learning path",
  "total_estimated_hours": sum of all selected resources
}}

Generate the learning path JSON now:"""

        try:
            # Uses ThreadPoolExecutor instead of asyncio.run() to avoid RuntimeError if an event loop is already running (Strands SDK issue)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(self.agent, prompt)
                try:
                    response = future.result(timeout=BEDROCK_TIMEOUT * 2)
                except FuturesTimeout:
                    raise BedrockTimeoutError("path_generation", BEDROCK_TIMEOUT * 2)
            
            # Extract text from response
            if hasattr(response, 'output'):
                response_text = response.output.strip()
            elif hasattr(response, 'content'):
                response_text = str(response.content).strip()
            else:
                response_text = str(response).strip()
            
            # Parse JSON from response
            # Handle markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            try:
                path_data = json.loads(response_text)
            except json.JSONDecodeError as json_err:
                logger.error("[agent:navigator] Failed to parse JSON: %s", json_err)
                logger.debug("[agent:navigator] Raw response: %s", response_text[:500])
                raise InvalidLLMResponseError(
                    "path_generation",
                    f"Invalid JSON: {str(json_err)}"
                )
            
            # Add profile summary to output
            path_data["profile_summary"] = fix_capitalization(profile_summary)
            
            # Validate structure
            if not self._validate_learning_path(path_data):
                logger.error("[agent:navigator] Invalid path structure from model")
                raise InvalidLLMResponseError(
                    "path_generation",
                    "Missing required fields in learning path"
                )
            
            logger.info(
                "[agent:navigator] Path generated: %d resources, %d total hours",
                len(path_data["recommended_resources"]),
                path_data["total_estimated_hours"],
            )
            return path_data
            
        except asyncio.TimeoutError:
            logger.error("[agent:navigator] Path generation timed out after %ds", BEDROCK_TIMEOUT * 2)
            raise BedrockTimeoutError("path_generation", BEDROCK_TIMEOUT * 2)
            
        except InvalidLLMResponseError:
            # Re-raise our custom exceptions
            raise
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for throttling
            if "throttl" in error_str or "rate limit" in error_str or "429" in error_str:
                logger.error("[agent:navigator] Bedrock throttling detected")
                raise BedrockThrottleError()
            
            # Check for timeout
            if "timeout" in error_str or "timed out" in error_str:
                logger.error("[agent:navigator] Bedrock timeout detected")
                raise BedrockTimeoutError("path_generation", BEDROCK_TIMEOUT * 2)
            
            # Generic error - use fallback
            logger.error("[agent:navigator] Path generation failed: %s", e, exc_info=True)
            logger.warning("[agent:navigator] Using fallback path generation")
            return self._fallback_learning_path(profile_summary, verified_resources)
    
    def _format_resource_catalog(self, resources: list[dict]) -> str:
        """Format resources into a readable catalog for the prompt."""
        catalog_lines = []
        for i, r in enumerate(resources, 1):
            catalog_lines.append(f"""
{i}. ID: {r.get('id')}
   Name: {r.get('name')}
   Provider: {r.get('provider')}
   Provider URL: {r.get('provider_url')}
   Resource URL: {r.get('resource_url')}
   Authority Tier: {r.get('authority_tier')}
   Difficulty: {r.get('difficulty')}
   Format: {r.get('format')}
   Estimated Hours: {r.get('estimated_hours')}
   Free Model: {r.get('free_model')}
   Prerequisites: {', '.join(r.get('prerequisites', [])) or 'None'}
   Tags: {', '.join(r.get('tags', []))}
   Description: {r.get('description')}
   Best For: {r.get('best_for')}
""")
        return "\n".join(catalog_lines)
    
    def _validate_learning_path(self, path_data: dict) -> bool:
        """Validate that the learning path has all required fields."""
        required_top_level = {"recommended_resources", "approach_guidance", "total_estimated_hours"}
        if not all(k in path_data for k in required_top_level):
            return False
        
        resources = path_data.get("recommended_resources", [])
        if not (4 <= len(resources) <= 6):
            logger.warning("[agent:navigator] Path has %d resources (expected 4-6)", len(resources))
            # Allow it but log warning
        
        required_resource_fields = {
            "resource_id", "resource_name", "resource_url", "provider",
            "provider_url", "why_for_you", "difficulty", "estimated_hours",
            "format", "free_model", "sequence_note", "sequence_order",
        }
        
        for r in resources:
            if not all(k in r for k in required_resource_fields):
                missing = required_resource_fields - set(r.keys())
                logger.error("[agent:navigator] Resource missing fields: %s", missing)
                return False
        
        return True
    
    def _fallback_learning_path(
        self,
        profile_summary: str,
        verified_resources: list[dict],
    ) -> dict:
        """Fallback path generation if Strands call fails."""
        logger.warning("[agent:navigator] Using fallback path generation")
        
        # Simple heuristic: pick top 4 resources by authority tier (lower is better) and difficulty
        sorted_resources = sorted(
            verified_resources,
            key=lambda r: (
                r.get('authority_tier', 3),  # Lower tier number = higher authority
                0 if r.get('difficulty') == 'beginner' else 1,  # Prefer beginner
            ),
        )
        
        selected = sorted_resources[:4]
        
        recommended = []
        total_hours = 0
        for i, r in enumerate(selected, 1):
            recommended.append({
                "resource_id": r.get('id'),
                "resource_name": r.get('name'),
                "resource_url": r.get('resource_url'),
                "provider": r.get('provider'),
                "provider_url": r.get('provider_url'),
                "why_for_you": f"This {r.get('format')} from {r.get('provider')} provides {r.get('description', 'quality content')}",
                "difficulty": r.get('difficulty'),
                "estimated_hours": r.get('estimated_hours', 10),
                "format": r.get('format'),
                "free_model": r.get('free_model'),
                "sequence_note": "Start here" if i == 1 else f"Take after resource {i-1}",
                "sequence_order": i,
            })
            total_hours += r.get('estimated_hours', 10)
        
        return {
            "profile_summary": profile_summary,
            "recommended_resources": recommended,
            "approach_guidance": f"Begin with {selected[0].get('name')} to build your foundation, then progress through the remaining resources in sequence. Each builds on the previous one.",
            "total_estimated_hours": total_hours,
        }
