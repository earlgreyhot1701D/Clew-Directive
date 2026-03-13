# test_fallback_bias.py
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, '.')

from agents.navigator import NavigatorAgent

nav = NavigatorAgent()

# Load resources
import json
with open('../data/directory.json') as f:
    resources = json.load(f)['resources']

# Filter to active ones
active = [r for r in resources if r.get('status') == 'active']

profiles = {
    "Skeptical business reader": (
        "You are approaching AI with healthy skepticism. "
        "Your goal is to understand what AI actually is "
        "and isn't for business decisions. You prefer "
        "reading at your own pace. Background: business "
        "operations."
    ),
    "Hands-on career switcher": (
        "You are excited about AI and want to build "
        "things. Your goal is creating AI applications. "
        "You learn through hands-on projects. Background: "
        "non-technical, career switching."
    ),
    "Creative professional": (
        "You work in design and creative media. You want "
        "AI tools for your creative workflow. You prefer "
        "video with examples. Background: creative/design."
    ),
}

all_results = {}
for label, profile in profiles.items():
    result = nav._fallback_learning_path(profile, active)
    ids = [r['resource_id'] for r in result['recommended_resources']]
    all_results[label] = ids
    
    print(f"\n{label}:")
    for r in result['recommended_resources']:
        print(f"  {r['sequence_order']}. {r['resource_id']} "
              f"({r['difficulty']}) - {r['provider']}")

# Check for identical results
values = list(all_results.values())
if values[0] == values[1] == values[2]:
    print("\n*** FAIL: All 3 profiles returned identical "
          "resources. Fix did not work. ***")
    sys.exit(1)
else:
    print("\n*** PASS: Profiles returned different "
          "resources. Fallback is profile-aware. ***")

# Check Helsinki dominance
for label, ids in all_results.items():
    helsinki_count = sum(1 for id in ids if id.startswith('elements-ai'))
    if helsinki_count >= 3:
        print(f"\n*** WARNING: {label} still has "
              f"{helsinki_count} Helsinki resources. ***")
