# Agent Implementation Guide - Clew Directive

**Version**: 1.0  
**Date**: February 12, 2026  
**Purpose**: Step-by-step implementation guide for Scout and Navigator agents

---

## Prerequisites

Before implementing agents:
1. ✅ Scaffold unzipped
2. ✅ Docker Compose running (`docker-compose up`)
3. ✅ Python 3.12+ installed
4. ✅ Dependencies installed (`pip install -r requirements.txt`)
5. ✅ Strands SDK installed (`pip install strands-agents-sdk`)

---

## Agent 1: Scout Agent

**Purpose**: Load and verify curated learning resources  
**Model**: Amazon Nova Micro ($0.000035/1K tokens)  
**Location**: `backend/agents/scout.py`

---

### Step 1: Understand the Stub

The scaffold already has a stub implementation. Open `backend/agents/scout.py`:

```python
class ScoutAgent:
    def __init__(self, knowledge: KnowledgeInterface, resource_verifier: Any = None):
        self.knowledge = knowledge
        self.resource_verifier = resource_verifier
        self.model = SCOUT_MODEL

    def gather_resources(self, domain: str = "ai-foundations", verify_urls: bool = True) -> list[dict]:
        # TODO: Implement
        raise NotImplementedError("Scout agent — implement with Nova Micro")
```

**Current State**: Stub only  
**Goal**: Implement `gather_resources()`

---

### Step 2: Implement Resource Loading

Replace the stub with:

```python
def gather_resources(
    self,
    domain: str = "ai-foundations",
    verify_urls: bool = True,
) -> list[dict]:
    """
    Load and verify resources for the given domain.
    
    Args:
        domain: Knowledge domain to load resources for.
        verify_urls: If True, perform runtime HTTP HEAD checks.
        
    Returns:
        List of verified, active resource dicts.
    """
    logger.info(
        "[agent:scout] Loading resources for domain=%s, verify=%s",
        domain,
        verify_urls,
    )

    # Step 1: Load all active resources from knowledge interface
    resources = self.knowledge.load_resources(domain)
    logger.info("[agent:scout] Loaded %d active resources", len(resources))

    if not verify_urls or self.resource_verifier is None:
        return resources

    # Step 2: Runtime URL verification (spot-check)
    verified = []
    for resource in resources:
        url = resource.get("resource_url", "")
        try:
            is_live = self.resource_verifier(url)
            if is_live:
                verified.append(resource)
            else:
                logger.warning(
                    "[agent:scout] Resource failed verification: id=%s url=%s",
                    resource.get("id"),
                    url,
                )
        except Exception:
            # Graceful degradation: if verification fails, include the
            # resource anyway (Curator verified it within the last week)
            logger.warning(
                "[agent:scout] Verification error for id=%s, including anyway",
                resource.get("id"),
                exc_info=True,
            )
            verified.append(resource)

    logger.info(
        "[agent:scout] Verification complete: %d/%d resources passed",
        len(verified),
        len(resources),
    )
    return verified
```

**Key Design Decisions**:
- **Graceful Degradation**: If URL check fails → include resource anyway
- **Logging**: Structured logs with `[agent:scout]` prefix
- **No AI Needed**: Scout is pure Python logic (Nova Micro not used here)

---

### Step 3: Test the Scout

Run the existing test:

```bash
pytest backend/tests/test_scout.py -v
```

**Expected Test**:
```python
def test_scout_gathers_resources():
    knowledge = MockKnowledgeInterface()
    scout = ScoutAgent(knowledge)
    
    resources = scout.gather_resources(domain="ai-foundations")
    
    assert len(resources) > 0
    assert all(r["status"] == "active" for r in resources)
```

**If Test Fails**: Check KnowledgeInterface implementation first

---

### Step 4: Deploy Scout (Optional for Local Dev)

Scout doesn't run as standalone Lambda. It's called by Navigator. No separate deployment needed.

---

## Agent 2: Navigator Agent

**Purpose**: Deep reasoning over profile and resources  
**Model**: Claude 4 Sonnet (Strands default)  
**Location**: `backend/agents/navigator.py`

---

### Step 1: Install Strands SDK

```bash
pip install strands-agents-sdk
```

**Verify Installation**:
```python
import strands
print(strands.__version__)  # Should show v1.0+
```

---

### Step 2: Initialize Strands Client

At the top of `navigator.py`, add:

```python
import logging
from strands import Agent, BedrockClient

logger = logging.getLogger("clew.agent.navigator")

# Initialize Bedrock client for Strands
bedrock_config = {
    "region": "us-east-1",
    "model_id": "anthropic.claude-v4-sonnet",  # Claude 4 Sonnet
}

client = BedrockClient(**bedrock_config)
```

**For Local Dev**: Use mocked Bedrock from Docker Compose

---

### Step 3: Implement Profile Synthesis

**Task**: Transform Vibe Check responses into 3-4 sentence narrative

Replace the stub in `synthesize_profile()`:

```python
def synthesize_profile(self, vibe_check_responses: dict) -> str:
    """
    Generate a 3-4 sentence profile summary from Vibe Check answers.
    
    Args:
        vibe_check_responses: Dict mapping question IDs to selected option text.
            Example: {"skepticism": "Curious but haven't started", ...}
    
    Returns:
        A natural language profile summary string.
    """
    logger.info("[agent:navigator] Synthesizing profile from Vibe Check")

    # Build prompt for Sonnet
    prompt = f"""You are a learning advisor helping someone understand their AI learning journey.

Based on their Vibe Check responses, write a 3-4 sentence profile in second person ("You're...").

Vibe Check Responses:
- Skepticism: {vibe_check_responses.get('skepticism')}
- Goal: {vibe_check_responses.get('goal')}
- Learning Style: {vibe_check_responses.get('learning_style')}
- Context: {vibe_check_responses.get('context')}

Requirements:
1. 3-4 sentences maximum
2. Use second person ("You're approaching AI with...")
3. Empathetic and encouraging tone, not clinical
4. Accurately reflect their skepticism level
5. Note their goal, learning preference, and professional context

Profile:"""

    # Create Strands agent
    agent = Agent(
        name="ProfileSynthesizer",
        model=client,
        instructions=prompt,
    )

    # Call agent (Sonnet)
    response = agent.run(prompt)
    
    profile = response.get("output", "").strip()
    
    logger.info("[agent:navigator] Profile synthesized: %d chars", len(profile))
    
    return profile
```

---

### Step 4: Implement Profile Refinement

Replace the stub in `refine_profile()`:

```python
def refine_profile(self, original_profile: str, user_correction: str) -> str:
    """
    Re-generate profile incorporating user's correction.
    
    Called when user clicks "Not quite" in the feedback loop.
    Capped at one refinement — second rejection resets the flow.
    
    Args:
        original_profile: The first profile summary that was rejected.
        user_correction: User's feedback (e.g., "I'm more hands-on, not just reading")
    
    Returns:
        Revised profile string.
    """
    logger.info("[agent:navigator] Refining profile with user correction")

    prompt = f"""You previously generated this profile:

"{original_profile}"

The user said it doesn't quite match them. Their correction:
"{user_correction}"

Rewrite the profile incorporating their feedback. Keep it 3-4 sentences, second person, empathetic.

Revised Profile:"""

    agent = Agent(
        name="ProfileRefiner",
        model=client,
        instructions=prompt,
    )

    response = agent.run(prompt)
    revised_profile = response.get("output", "").strip()
    
    logger.info("[agent:navigator] Profile refined: %d chars", len(revised_profile))
    
    return revised_profile
```

---

### Step 5: Implement Learning Path Generation

**Task**: Match profile to 4-6 resources, sequence them, provide reasoning

Replace the stub in `generate_learning_path()`:

```python
def generate_learning_path(
    self,
    profile_summary: str,
    verified_resources: list[dict]
) -> dict:
    """
    Generate a personalized learning path from verified resources.
    
    Args:
        profile_summary: Navigator's profile summary (approved by user).
        verified_resources: List of active resources from Scout (50-100 items).
    
    Returns:
        Dict with learning_path, total_hours, next_steps.
    """
    logger.info(
        "[agent:navigator] Generating learning path from %d resources",
        len(verified_resources)
    )

    # Build structured prompt
    resources_json = json.dumps(verified_resources, indent=2)
    
    prompt = f"""You are a learning path designer. Create a personalized AI learning path.

User Profile:
{profile_summary}

Available Resources (curated, all free):
{resources_json}

Task:
1. Select 4-6 resources that best match the profile
2. Sequence them from easier → harder
3. Respect prerequisites (if resource A requires B, B comes first)
4. Provide 2-3 sentence reasoning for each resource
5. Total time budget: 30-60 hours

Output ONLY valid JSON (no preamble):
{{
  "learning_path": [
    {{
      "resource_id": "elements-ai-intro",
      "sequence": 1,
      "reasoning": "Perfect starting point for skeptics who want conceptual understanding...",
      "estimated_hours": 30
    }},
    ...
  ],
  "total_hours": 45,
  "next_steps": "After completing these foundational courses, you'll be ready to..."
}}"""

    agent = Agent(
        name="PathGenerator",
        model=client,
        instructions="You are a learning path designer. Output only valid JSON.",
    )

    response = agent.run(prompt)
    output_text = response.get("output", "").strip()
    
    # Parse JSON response
    try:
        # Strip markdown code fences if present
        if output_text.startswith("```"):
            output_text = output_text.split("```")[1]
            if output_text.startswith("json"):
                output_text = output_text[4:]
            output_text = output_text.strip()
        
        path_data = json.loads(output_text)
        
        # Validate structure
        assert "learning_path" in path_data
        assert len(path_data["learning_path"]) >= 4
        assert len(path_data["learning_path"]) <= 6
        assert "total_hours" in path_data
        assert "next_steps" in path_data
        
        logger.info(
            "[agent:navigator] Path generated: %d resources, %d hours",
            len(path_data["learning_path"]),
            path_data["total_hours"]
        )
        
        return path_data
        
    except (json.JSONDecodeError, AssertionError) as e:
        logger.error("[agent:navigator] Failed to parse path JSON: %s", e)
        # Fallback: return empty path
        return {
            "learning_path": [],
            "total_hours": 0,
            "next_steps": "We encountered an error generating your path. Please try again."
        }
```

**Key Design Decisions**:
- **Structured Output**: Prompt Sonnet to return JSON only
- **Validation**: Assert 4-6 resources, validate structure
- **Graceful Degradation**: If JSON parse fails → return empty path
- **Markdown Fence Handling**: Strip ```json``` if Sonnet adds it

---

### Step 6: Test the Navigator

Run the existing test:

```bash
pytest backend/tests/test_navigator.py -v
```

**Expected Test**:
```python
def test_navigator_synthesizes_profile():
    navigator = NavigatorAgent()
    
    responses = {
        "skepticism": "Curious but haven't started learning",
        "goal": "Understand what AI actually is and isn't",
        "learning_style": "Reading and thinking at my own pace",
        "context": "Business / Marketing / Operations"
    }
    
    profile = navigator.synthesize_profile(responses)
    
    assert len(profile) > 100  # Reasonable length
    assert "you" in profile.lower()  # Second person
    assert len(profile.split(".")) >= 3  # 3+ sentences
```

---

### Step 7: Golden Test for Consistency

Create `backend/tests/test_navigator_golden.py`:

```python
import pytest
from backend.agents.navigator import NavigatorAgent

def test_profile_synthesis_consistency():
    """
    Golden test: Same input should produce similar output.
    
    Run this test 3 times, verify profiles are semantically consistent.
    """
    navigator = NavigatorAgent()
    
    responses = {
        "skepticism": "Skeptical — I want to understand what's real",
        "goal": "Understand what AI actually is and isn't",
        "learning_style": "Reading and thinking at my own pace",
        "context": "Business / Marketing / Operations"
    }
    
    profiles = [navigator.synthesize_profile(responses) for _ in range(3)]
    
    # All should mention skepticism
    for profile in profiles:
        assert "skeptic" in profile.lower() or "understand" in profile.lower()
    
    # All should mention business context
    for profile in profiles:
        assert "business" in profile.lower() or "marketing" in profile.lower()
    
    # Lengths should be similar (within 50 chars)
    lengths = [len(p) for p in profiles]
    assert max(lengths) - min(lengths) < 50
```

**Run 3 Times**:
```bash
pytest backend/tests/test_navigator_golden.py -v
pytest backend/tests/test_navigator_golden.py -v
pytest backend/tests/test_navigator_golden.py -v
```

**All Should Pass**: Verifies Sonnet consistency

---

## Integration Testing (Scout + Navigator)

Create `backend/tests/test_integration.py`:

```python
import pytest
from backend.agents.scout import ScoutAgent
from backend.agents.navigator import NavigatorAgent
from backend.interfaces.knowledge_interface import KnowledgeInterface

def test_end_to_end_flow():
    """
    Full flow: Vibe Check → Profile → Path
    """
    # Setup
    knowledge = KnowledgeInterface()
    scout = ScoutAgent(knowledge)
    navigator = NavigatorAgent()
    
    # Step 1: Vibe Check responses
    vibe_responses = {
        "skepticism": "Curious but haven't started learning",
        "goal": "Understand what AI actually is and isn't",
        "learning_style": "Reading and thinking at my own pace",
        "context": "Business / Marketing / Operations"
    }
    
    # Step 2: Synthesize profile
    profile = navigator.synthesize_profile(vibe_responses)
    assert len(profile) > 100
    
    # Step 3: Gather resources
    resources = scout.gather_resources(domain="ai-foundations")
    assert len(resources) >= 10  # Need enough to choose from
    
    # Step 4: Generate path
    path = navigator.generate_learning_path(profile, resources)
    
    # Validate path
    assert "learning_path" in path
    assert len(path["learning_path"]) >= 4
    assert len(path["learning_path"]) <= 6
    assert path["total_hours"] >= 30
    assert path["total_hours"] <= 60
    assert "next_steps" in path
    
    # Validate each resource in path
    for item in path["learning_path"]:
        assert "resource_id" in item
        assert "sequence" in item
        assert "reasoning" in item
        assert "estimated_hours" in item
        assert len(item["reasoning"]) > 50  # Non-trivial reasoning
```

**Run**:
```bash
pytest backend/tests/test_integration.py -v
```

---

## Debugging Tips

### Issue 1: Strands SDK Import Error
```
ModuleNotFoundError: No module named 'strands'
```

**Solution**: Install SDK:
```bash
pip install strands-agents-sdk --break-system-packages
```

---

### Issue 2: Bedrock Permission Denied
```
AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel
```

**Solution**: Update IAM role with Bedrock permissions:
```json
{
  "Effect": "Allow",
  "Action": "bedrock:InvokeModel",
  "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-v4-sonnet"
}
```

---

### Issue 3: Navigator Returns Empty JSON
```
json.JSONDecodeError: Expecting value
```

**Solution**: Sonnet didn't return valid JSON. Check prompt:
- Add "Output ONLY valid JSON, no preamble"
- Add example JSON in prompt
- Strip markdown fences in parsing

---

### Issue 4: Profile Too Short
```
AssertionError: assert len(profile) > 100
```

**Solution**: Prompt not clear enough. Update to:
```
"Write exactly 3-4 complete sentences. Each sentence should be 20-30 words."
```

---

## Performance Optimization

### Caching Scout Results

**Problem**: Scout runs on every path generation, even if resources haven't changed

**Solution**: Cache in Redis for 1 hour:

```python
import redis

cache = redis.Redis(host='localhost', port=6379)

def gather_resources(self, domain: str, verify_urls: bool = True) -> list[dict]:
    cache_key = f"scout:resources:{domain}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Load fresh
    resources = self.knowledge.load_resources(domain)
    # ... verification logic ...
    
    # Cache for 1 hour
    cache.setex(cache_key, 3600, json.dumps(verified))
    
    return verified
```

---

## Next Steps

After implementing both agents:

1. **Implement Orchestrator** (Phase 5)
2. **Implement PDF Generator** (Phase 6)
3. **Create Lambda Handlers** (Phase 8)
4. **Build Frontend** (Phase 9)

See `BUILD_ORDER.md` for detailed sequence.

---

**Document Owner**: Engineering Lead  
**Last Updated**: February 12, 2026