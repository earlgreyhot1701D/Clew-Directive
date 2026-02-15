"""
Mock Bedrock responses for testing.

These mocks simulate Nova Micro (Scout) and Claude 4 Sonnet (Navigator)
responses without calling real AWS services.

Usage:
    from backend.tests.mocks.bedrock_mocks import MOCK_PROFILE_RESPONSE
"""

# Mock Navigator profile synthesis response
MOCK_PROFILE_RESPONSE = (
    "You're approaching AI with healthy curiosity — you haven't started "
    "learning yet but you're open to understanding what's real. Your primary "
    "goal is using AI tools to be more effective in your marketing work. "
    "You prefer structured courses with a clear path, and you learn best "
    "when there's a logical progression to follow."
)

# Mock Navigator learning path response
MOCK_LEARNING_PATH = {
    "profile_summary": MOCK_PROFILE_RESPONSE,
    "recommended_resources": [
        {
            "resource_id": "elements-ai-intro",
            "resource_name": "Introduction to AI",
            "resource_url": "https://course.elementsofai.com/",
            "provider": "University of Helsinki / MinnaLearn",
            "provider_url": "https://www.elementsofai.com/",
            "why_for_you": (
                "This is the perfect starting point for someone curious but new to AI. "
                "It covers what AI actually is without requiring any technical background."
            ),
            "difficulty": "beginner",
            "estimated_hours": 30,
            "format": "course",
            "free_model": "Fully free",
            "sequence_note": "Start here",
            "sequence_order": 1,
        },
        {
            "resource_id": "google-ai-essentials",
            "resource_name": "Google AI Essentials",
            "resource_url": "https://grow.google/certificates/ai-essentials/",
            "provider": "Google / Grow with Google",
            "provider_url": "https://grow.google/",
            "why_for_you": (
                "Practical and hands-on — this course bridges the gap between "
                "understanding AI and actually using it in your daily work."
            ),
            "difficulty": "beginner",
            "estimated_hours": 10,
            "format": "course",
            "free_model": "Fully free",
            "sequence_note": "Take after Introduction to AI",
            "sequence_order": 2,
        },
        {
            "resource_id": "google-prompting-essentials",
            "resource_name": "Google Prompting Essentials",
            "resource_url": "https://grow.google/certificates/prompting-essentials/",
            "provider": "Google / Grow with Google",
            "provider_url": "https://grow.google/",
            "why_for_you": (
                "As a marketer, prompt engineering is your highest-leverage AI skill. "
                "This gives you a practical framework for getting better results."
            ),
            "difficulty": "beginner",
            "estimated_hours": 5,
            "format": "course",
            "free_model": "Fully free",
            "sequence_note": "Take after Google AI Essentials",
            "sequence_order": 3,
        },
    ],
    "approach_guidance": (
        "Start with the Introduction to AI course — spend about a week on it, "
        "a chapter a day. It will give you the conceptual foundation to make "
        "sense of everything else. Then move to Google AI Essentials for practical "
        "skills. Don't rush — understanding beats speed."
    ),
    "total_estimated_hours": 45,
}

# Mock Vibe Check responses (for golden tests)
MOCK_VIBE_CHECK_CURIOUS_MARKETER = {
    "skepticism": "Curious but haven't started learning",
    "goal": "Use AI tools to be better at my current job",
    "learning_style": "Structured courses with a clear path",
    "context": "Business / Marketing / Operations",
}

MOCK_VIBE_CHECK_SKEPTICAL_TEACHER = {
    "skepticism": "Skeptical — I want to understand what's real",
    "goal": "Understand what AI actually is and isn't",
    "learning_style": "Reading and thinking at my own pace",
    "context": "Education / Academia",
}

MOCK_VIBE_CHECK_BUILDER_ENGINEER = {
    "skepticism": "I use AI tools already and want to go deeper",
    "goal": "Build things with AI",
    "learning_style": "Hands-on projects and exercises",
    "context": "Technical / Engineering / IT",
}
