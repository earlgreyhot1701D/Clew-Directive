# Product Vision — Clew Directive

**Last Updated**: February 12, 2026  
**Source**: Enriched from conversation transcript and original scaffold

---

## Mission

Clew Directive (CD) is a free, open-source, stateless AI tool that generates personalized "Command Briefing" PDFs mapping new AI learners to verified free learning resources. No accounts, no tracking, no paywalls.

**Tagline**: "Stop following the hype. Start directing the search."

**Competition**: AWS 10,000 AIdeas (Social Impact Category)  
**Team**: Docket 1701D  
**Status**: Semi-finalist

---

## Target Users (MVP)

New AI learners — people who are curious about AI but overwhelmed by options. They range from skeptics who want to understand what's real, to enthusiasts who want structured guidance.

**Primary Persona**: Marketing Manager Sarah
- Age: 32, Business/Marketing role
- Skeptical about AI hype, wants to understand what's real
- Learns by reading at her own pace
- Needs: Foundational understanding to make informed business decisions

**Secondary Persona**: Career Switcher Marcus
- Age: 28, currently in retail
- Wants to build things with AI
- Prefers hands-on projects
- Needs: Structured path from beginner to builder

**Anti-Persona**: CS Students with AI Background
- Already have access to university resources
- Need advanced topics, not foundations

**MVP Scope**: Domain "ai-foundations" only

---

## Core User Journey

### 1. Landing Page (5 seconds)
- One-shot privacy notice (dismissible):
  > "Welcome, Learner. This is a stateless tool. We don't track you, we don't store your answers. Your briefing is yours. Let's begin."
- Clean retro-terminal aesthetic (Osprey Navy #0A1128 + Cyber Gold #FFD60A)
- Single CTA: "Begin" button
- Optional: Boot sequence animation

### 2. Vibe Check (60-90 seconds)
**Sequential UI** (one question at a time, not all-at-once):

**Q1 (Skepticism)**: "Which best describes your current take on AI?"
1. Skeptical — I want to understand what's real
2. Curious but haven't started learning
3. I've dabbled and want more structure
4. I use AI tools already and want to go deeper

**Q2 (Goal)**: "If AI could help you with one thing, what would it be?"
1. Understand what AI actually is and isn't
2. Use AI tools to be better at my current job
3. Build things with AI
4. Make career decisions about AI

**Q3 (Learning Style)**: "How do you prefer to learn new things?"
1. Reading and thinking at my own pace
2. Watching videos with examples
3. Hands-on projects and exercises
4. Structured courses with a clear path

**Q4 (Context)**: "What's your professional context?"
1. Education / Academia
2. Business / Marketing / Operations
3. Technical / Engineering / IT
4. Creative / Design / Media
5. Other / Career switching

**UX Details**:
- Progress indicator: "Question 2 of 4"
- Radio buttons for selection
- "Next" button appears after selection
- No back button (one-directional flow for simplicity)

### 3. Profile Feedback (15-30 seconds)
```
Here's how we see your learning journey:

[Navigator's 3-4 sentence profile summary]

Does this sound like you?

[Yes, that's me]  [Not quite]
```

**If "Yes"**: Proceed to resource verification + path generation  
**If "Not quite"**:
```
Help us refine this. What should we adjust?

[Text area - 200 char limit]

[Regenerate Profile]
```

**One Refinement Cap**:
- First refinement: Navigator incorporates feedback
- Second "Not quite": Reset to Vibe Check Q1
- Rationale: Cost control + UX simplicity

### 4. Processing (30-45 seconds)
**Loading States** (show progress without overwhelming):
1. "Verifying resources..." (Scout running)
2. "Crafting your learning path..." (Navigator reasoning)
3. "Preparing your briefing..." (PDF generation)

**No progress bar** (too granular, induces anxiety)  
**No ETA** (too variable)

### 5. Results Display
```
Your Learning Path is Ready

[Download Command Briefing (PDF)]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Resource 1: Introduction to AI
University of Helsinki | 30 hours | Self-paced course

Why this resource:
[Navigator's 2-3 sentence reasoning]

👉 Start Learning: https://course.elementsofai.com/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[4-6 resources displayed]
```

**Key Features**:
- All resource links clickable in UI AND PDF
- PDF opens in new tab + auto-downloads
- Resources display in sequence order
- Each shows: Name, Provider, Time, Format, Reasoning, Link

### 6. Session Purge (Immediate)
- User downloads PDF → that's the only record
- Lambda terminates → all Vibe Check responses purged from memory
- After 24 hours → PDF auto-deleted from S3
- No cookies persist beyond session

---

## Key Differentiators

### 1. Stateless by Design
**Principle**: We don't keep your data because we don't need it.

**What This Means**:
- No user accounts required
- No email addresses collected
- No Vibe Check responses stored
- No profile summaries saved
- No "resume where you left off" feature

**Why It Matters**: 
- Privacy-first in an age of surveillance
- Removes friction (no signup wall)
- GDPR/CCPA compliant by architecture

### 2. Curated, Not Crawled
**5-Gate Quality Standard**:

**Gate 1 - Authority**: University / Major tech / Respected platform  
**Gate 2 - Truly Free**: No paywalls, freemium OK if core is free  
**Gate 3 - Current**: Updated within 18 months (or maintained classic)  
**Gate 4 - Pedagogically Sound**: Structured, has exercises, clear objectives  
**Gate 5 - Accessible**: No region-locks, English, self-paced  

**Process**: Manual curation by team, not automated scraping  
**Result**: ~50-100 hand-picked resources (vs. 10,000+ low-quality results)

### 3. Automated Freshness
**Curator Lambda**: Runs weekly (Sundays 2AM UTC)
- HTTP HEAD check on every resource URL
- Updates `last_verified` timestamp
- Marks dead links as `status: "inactive"`
- Alerts if >10% fail

**Why It Matters**: Free resources go offline. We catch it automatically.

### 4. Personalized Reasoning
**Navigator Agent**: Uses Claude 4 Sonnet for deep reasoning
- Synthesizes profile from Vibe Check (not just keyword matching)
- Reasons holistically over resources (not just tags)
- Provides 2-3 sentence "why" for each resource
- Sequences from easier → harder, respects prerequisites

**Not a Recommendation Engine**: This is AI reasoning, not collaborative filtering

---

## Brand Voice & Aesthetic

### Voice
- **Empowering, not condescending**: "You're approaching AI with curiosity" (not "You don't know AI yet")
- **Honest, not hyped**: Acknowledge limitations, set expectations
- **Encouraging, not pushy**: "When you're ready" (not "Start now!")

### Visual Language
- **Retro-terminal aesthetic** (guidance, can evolve)
  - Colors: Osprey Navy (#0A1128) + Cyber Gold (#FFD60A)
  - Font: Monospace (JetBrains Mono or similar)
  - Optional: Boot sequence animation on landing
- **Clean and professional** (not overly "hacker" themed)
- **High contrast for accessibility** (WCAG 2.1 AA compliant)

---

## Competitive Landscape

### Direct Competitors
1. **Coursera / edX Free Courses**
   - Strength: Reputable, structured
   - Weakness: Overwhelming choice, no personalization
   - **Our Advantage**: Curated + personalized in 90 seconds

2. **YouTube AI Tutorials**
   - Strength: Free, abundant
   - Weakness: Quality varies wildly, no structure
   - **Our Advantage**: Vetted resources only, sequenced paths

### Indirect Competitors
3. **Google Search + ChatGPT**
   - Strength: Instant, familiar
   - Weakness: No curation, hallucination risk
   - **Our Advantage**: 5-gate quality standard, Navigator reasons over verified resources

4. **Paid Bootcamps (Udacity, Coursera Plus)**
   - Strength: Job-focused, comprehensive
   - Weakness: $300-2,000 cost barrier
   - **Our Advantage**: 100% free resources, zero cost

---

## Success Metrics (Post-Launch)

### Primary Metric: Briefings Downloaded
- **Target**: 500+ during voting period (March 13-20, 2026)
- **Why**: Measures actual value delivered

### Secondary Metrics:
1. **Profile Refinement Rate** (expect 20-30%)
   - Too low: Users happy with first attempt OR frustrated and leaving
   - Too high: Navigator synthesis needs improvement
2. **Resource Click-Through Rate** (from PDF)
   - Target: 60%+ click at least one link
   - Measures engagement with recommendations
3. **Curator Failure Rate** (expect <5%)
   - % of resources marked inactive each week
   - Measures directory health

---

## Out of Scope (v1)

**Will NOT Build for Competition**:
- ❌ Multi-domain support (only "ai-foundations")
- ❌ User accounts / saved briefings
- ❌ Email delivery of PDFs
- ❌ Resource ratings/reviews
- ❌ Community features (forums, comments)
- ❌ Mobile app (responsive web only)
- ❌ Non-English languages
- ❌ Progress tracking

**Future Roadmap** (Post-Competition):

**Phase 2** (Q2 2026): Email Briefing
- User provides email → PDF sent via SES
- No account required, one-time delivery
- Tagline in article: "Coming soon: Email your briefing"

**Phase 3** (Q3 2026): Domain Expansion
- ai-security
- ai-healthcare
- ai-for-education
- Each domain: separate curated directory

**Phase 4** (Q4 2026): Progress Tracking (requires accounts)
- Save briefings
- Track completed resources
- Update recommendations based on progress

---

## Competition Narrative

### For Judges

**Innovation**: "AI teaching AI about AI" — meta approach to democratizing learning

**Social Impact**: 
- Removes cost barrier (100% free resources)
- Removes choice paralysis (curated paths)
- Respects privacy (stateless architecture)

**Technical Excellence**:
- Serverless, cost-efficient (<$1 per briefing)
- WCAG 2.1 AA compliant (inclusive by design)
- Kiro spec-driven development (quality gates)

**Presentation Hook**: 
> "Clew Directive ships today as a focused tool for new AI learners. The architecture is domain-agnostic — we designed for expansion, shipped for impact."

### Article Angle

**Title**: "Stop Following the Hype: Building a Stateless AI Learning Navigator"

**Key Points**:
1. Problem: AI learning is overwhelming (100,000+ resources, most low-quality or paywalled)
2. Solution: Curated + personalized in 90 seconds
3. How: Scout (verification) + Navigator (reasoning) + Curator (freshness)
4. Why stateless: Privacy as a feature, not an afterthought
5. Impact: 500+ learners guided during voting period

---

## Privacy Principles

### Core Tenet
**We don't keep your data because we don't need it. Your briefing is yours.**

### Implementation
- No database (stateless architecture)
- No cookies beyond session
- No analytics beyond aggregate counts
- PDF self-destructs after 24 hours
- Session ID is random UUID (not user-identifiable)

### Messaging
**On Landing Page**:
> "This is a stateless tool. We don't track you, we don't store your answers."

**In PDF Footer**:
> "We don't keep your data because we don't need it. Your briefing is yours."

**In Article**:
> "Privacy isn't a feature we bolted on — it's the architecture."

---

## Accessibility Commitment

**Target**: WCAG 2.1 AA Compliance

**Why**: 
> "A social impact tool that excludes people with disabilities contradicts its own mission."

**Implementation**:
- ARIA labels on all interactive elements
- Keyboard-only navigation tested
- Screen reader tested (NVDA)
- High contrast mode (Osprey Navy + Cyber Gold = 7:1 ratio)
- Text resize to 200% without breaking
- Focus indicators on all focusable elements

**For Article**: 
> "Clew Directive targets WCAG 2.1 AA compliance because a social impact tool that excludes people with disabilities contradicts its own mission."

---

**Document Owner**: Product Manager  
**Stakeholders**: Engineering, Competition Judges, Community  
**Review Cadence**: Weekly during development  
**Status**: Ready for Kiro implementation