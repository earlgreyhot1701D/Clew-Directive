# Clew Directive

**Stop following the hype. Start directing the search.**

Clew Directive is a free, open-source, stateless AI tool that generates personalized **Learning Path** PDFs — mapping new AI learners to the best free learning resources based on their goals, experience, and learning style.

No accounts. No tracking. No paywalls. Your briefing is yours.

**Built on Amazon Nova** for fast, cost-effective reasoning at scale — enabling global access without resource constraints.

**Privacy by Design**:
- Sessions are stateless — no database, no user accounts, no tracking pixels
- PDFs are stored temporarily in S3 (auto-deleted after 24 hours)
- Lambda execution logs are retained for 7 days then auto-deleted
- No personally identifiable information is collected

**🚀 Live Demo**: [https://clewdirective.com](https://clewdirective.com)

**Status**: ✅ Deployed to AWS | ✅ AI Personalization Active | ✅ WCAG 2.1 AAA contrast ratios (13.24:1)

---

## Why This Exists

The AI education landscape is overwhelming. Thousands of courses, tutorials, and certifications compete for attention — most behind paywalls, many outdated, few personalized. People who could benefit most from AI literacy are the most likely to be lost in the noise.

Clew Directive cuts through it. Take a 60-second **Vibe Check**, get a personalized learning path from verified, free resources, download your **Learning Path** PDF, and go. That's it.

**Impact**: Democratizing AI education access globally by removing financial and cognitive barriers. One personalized learning path eliminates hours of research and removes paywalls entirely—making AI literacy available to educators, career-changers, and lifelong learners regardless of geography or budget.

---

## How It Works

```
User arrives → Privacy notice
     ↓
Vibe Check (4 questions)
     ↓
Navigator synthesizes profile → "Does this sound like you?"
     ↓                               ↓
[That's me ✓]                  [Not quite ✗] → correction → re-generate
     ↓
Scout verifies resources (live URL checks)
     ↓
Navigator generates personalized learning path
     ↓
UI displays results with live links + PDF download
     ↓
Session ends — PDFs auto-delete after 24h, logs expire after 7 days
```

The interface guides users through one profile refinement. Users confirm their profile before proceeding to plan generation.

---

## Screenshots

### Landing Page
![Opening Page](docs/Opening%20Page.png)

### Vibe Check (4 Questions)
<table>
<tr>
<td width="50%">

![AI Experience](docs/AI%20Experience.png)
*Question 1: AI Experience Level*

</td>
<td width="50%">

![Primary Goal](docs/Primary%20Goal.png)
*Question 2: Primary Goal*

</td>
</tr>
<tr>
<td width="50%">

![Learning Style](docs/Learning%20Style.png)
*Question 3: Learning Style*

</td>
<td width="50%">

![Background](docs/Background%20See%20My%20Plan.png)
*Question 4: Background*

</td>
</tr>
</table>

### Profile & Approval
![Learning Profile](docs/Learning%20Profile%20.png)
*AI-generated profile summary with approval options*

### Generation Process
![Generating Your Learning Path](docs/Generating%20Your%20Learning%20Path.png)
*Progressive loading states with real-time updates*

### Learning Plan Results
![Learning Plan Source 1](docs/Learning%20Plan%20Source%201.png)
*Personalized resource recommendations with reasoning*

![Time Resources Next Step](docs/Time%20Resources%20Next%20Step.png)
*Summary with total hours and next steps*

### PDF Download
![Download My Plan](docs/Download%20My%20Plan.png)
*Download button for Learning Path PDF*

### Learning Path PDF
![Command Briefing](docs/Command%20Briefing.png)
*Example PDF output with clickable resource links*

### About Modal
![About Clew Directive](docs/About%20Clew%20Directive.png)
*Philosophy, privacy, and curation standards*

---

## Personalization in Action

**Real test results** showing how Clew Directive adapts to different learners:

### Skeptical Academic
*"I want to understand what's real"*
- **4 resources** (ethics-focused) — **105 hours**
- Introduction to AI → Ethics of AI → Building AI → CS50's AI with Python
- **Why different**: Includes ethics course for critical thinking approach

### Hands-on Builder  
*"I use AI tools already and want to go deeper"*
- **4 resources** (project-based) — **115 hours**
- Introduction to AI → Building AI → CS50's AI with Python → Generative AI for Beginners
- **Why different**: Skips ethics, adds hands-on generative AI projects

### Business Professional
*"Use AI tools to be better at my current job"*
- **5 resources** (business tools) — **56 hours**
- Introduction to AI → AI for Everyone → Google Prompting Essentials → AI for Business Users → Google AI Essentials
- **Why different**: Shorter, practical courses focused on business applications and prompting

**Key Metrics**:
- ✅ **9 unique resources** across 3 users (vs 4 identical in fallback mode)
- ✅ **Profiles are unique** and AI-generated (not template-based)
- ✅ **Path length varies** (4-5 resources, 56-115 hours) based on user needs
- ✅ **Resource selection adapts** to learning style, goals, and professional context

This demonstrates genuine AI reasoning, not keyword matching or collaborative filtering.

## Why Amazon Nova

Clew Directive is built as a **multi-agent reasoning system**, and Nova's agentic capabilities are the technical foundation.

**Agent-Driven Architecture**:
- **Scout Agent (Nova Micro)**: Independently reasons about resource freshness. Not simple keyword matching—it evaluates URL validity, content currency, pedagogical alignment, and global accessibility as part of a systematic verification pipeline. Runs weekly via EventBridge, keeping the resource directory trustworthy without manual curation.
- **Navigator Agent (Nova 2 Lite)**: Synthesizes a user's 4-question profile into a coherent learning persona, then **reasons step-by-step through 28 curated resources** to select a personalized path. This isn't collaborative filtering or rule-based matching. Nova 2 Lite's extended thinking and multi-step reasoning capabilities enable it to understand nuance—balancing user goals, learning style, background, and time constraints in a single coherent decision.

**Why This Matters for Learning Paths**:
Traditional AI systems for recommendations rely on pattern matching or heuristic scoring. Clew Directive uses **reasoning-driven personalization**—Nova 2 Lite thinks through trade-offs (ethics-heavy vs. hands-on vs. business-focused paths) and justifies each resource selection with explicit reasoning visible to users. This produces genuinely different paths for different learners, not template variations.

**Technical Efficiency Without Compromise**:
- **Nova Micro**: 71x cheaper than comparable models, enabling continuous autonomous curation (weekly URL freshness checks cost ~$0.00/month on Free Tier).
- **Nova 2 Lite**: Fast reasoning model with tunable thinking effort—striking the balance between instant response times (no user frustration) and deep reasoning quality (no shallow personalization).
- **Result**: A production reasoning system that costs **~$11-12/month**, allowing 6-8 months of runway on $100 AWS credit. Cost efficiency doesn't dilute reasoning quality—it enables scalable impact. The system remains free forever, globally accessible, because Nova's price-to-reasoning ratio makes it economically sustainable.

## Architecture

**Deployment**: Serverless on AWS using CDK (Infrastructure-as-Code)

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│   Next.js   │────▶│ API Gateway  │────▶│    Lambda       │
│  (Amplify)  │     │ (rate limit) │     │  (Orchestrator) │
└─────────────┘     └──────────────┘     └───────┬────────┘
                                                  │
                                    ┌─────────────┴─────────────┐
                                    │                           │
                              ┌─────▼──────┐            ┌──────▼──────┐
                              │   Scout    │            │  Navigator  │
                              │ (Nova Micro)│            │(Nova 2 Lite)│
                              │ $0.000035/  │            │            │
                              │  1K tokens  │            │            │
                              └─────┬──────┘            └──────┬──────┘
                                    │                          │
                              ┌─────▼──────┐            ┌──────▼──────┐
                              │ S3 JSON    │            │  WeasyPrint │
                              │ directory  │            │  PDF Gen    │
                              └────────────┘            └─────────────┘

     ┌─────────────┐
     │   Curator   │  ← EventBridge (weekly cron)
     │ (Nova Micro)│  → Verifies URLs, updates directory.json
     └─────────────┘
```

**Infrastructure Components**:
- **3 Lambda Functions**: Vibe Check, Profile Refinement, Briefing Generation
  - **Docker-based bundling**: Dependencies automatically installed during CDK synthesis
  - Deployment packages include all Python dependencies from `requirements.txt`
  - Consistent builds across Windows/Mac/Linux development environments
- **API Gateway**: REST API with 10 req/sec rate limiting, CORS enabled
- **S3 Bucket**: Stores directory.json and temporary PDFs (24h TTL)
- **EventBridge**: Weekly cron trigger for Curator Lambda
- **IAM Roles**: Least-privilege access for each Lambda function
- **CloudWatch**: Logs and metrics for monitoring

### Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Agent framework | Strands Agents SDK (Python, v1.0 GA) | Production-grade, official Lambda Layer, battle-tested |
| Scout model | Amazon Nova Micro | 71x cheaper than Sonnet; sufficient for URL verification |
| Navigator model | Amazon Nova 2 Lite | Fast reasoning for profile analysis and path generation; instant access |
| Knowledge layer | Curated S3 JSON | Occam's Razor — 28 handpicked resources don't need vector search |
| Freshness | Curator Lambda (weekly) | Automated URL verification; ~$0.00/month on Free Tier |
| PDF generation | WeasyPrint | HTML→PDF with clickable links; preserves terminal aesthetic |
| Frontend | Next.js on Amplify | Live URL for voting period; Free Tier hosting |
| IaC | TypeScript CDK | All infrastructure defined in code |
| Accessibility | WCAG 2.1 AAA contrast ratios (13.24:1) | Social good tool must be accessible to all |
| Lambda scaling | Reserved concurrency (10 per function) | Cost control: caps concurrent executions at 10 per function |

### Cost (Voting Period Estimate)

| Component | Expected Cost |
|-----------|--------------|
| Bedrock (500 briefings) | ~$5-15 |
| Lambda | Free Tier |
| API Gateway | Free Tier |
| S3 | Free Tier |
| Amplify | Free Tier |
| EventBridge | Free Tier |
| **Total** | **~$5-15** (covered by $200 credits) |

---

## Resource Curation

Every resource in `directory.json` passes a **5-gate quality standard**:

1. **Authority**: University (Tier 1), major tech provider (Tier 2), or respected platform (Tier 3)
2. **Truly free**: Learning content accessible without payment
3. **Current**: Created or updated within 18 months
4. **Pedagogically sound**: Structured progression with exercises
5. **Accessible**: No prerequisites to purchase, globally available, self-paced

Resources are hand-curated against these standards. The directory is reviewed and updated regularly.

Current directory: **28 resources** from Helsinki, Stanford, MIT, Harvard, Google, AWS, Microsoft, NVIDIA, DeepLearning.AI, Hugging Face, IBM, fast.ai, Kaggle, LinkedIn Learning, and Adobe.

The Curator Lambda verifies every URL weekly. Status progression: `active → degraded → stale → dead`. Only `active` resources reach users.

---

## Resource Database (v1.0 - MVP)

**Current State**: 28 curated resources covering AI foundations through advanced topics

**Quality Over Quantity**: Each resource passes our 5-gate curation standard:
1. Authority (trusted source)
2. Accessibility (free access)
3. Currency (updated recently)
4. Clarity (clear outcomes)
5. Verified (URL checked weekly)

**Coverage**:
- ✅ Complete beginners → Advanced learners
- ✅ Conceptual understanding → Hands-on building
- ✅ Multiple learning styles (courses, tutorials, labs)
- ✅ Ethics & responsible AI

**Growth Plan**:
- 🎯 **Q2 2026**: Expand to 50 resources
- 🎯 **Q3 2026**: Add specialized domains (NLP, Computer Vision, RL)
- 🎯 **Q4 2026**: Community curation (vetted submissions)

**Why Start Small?** We're validating the curation process and personalization algorithms before scaling. 28 resources is enough to demonstrate meaningful personalization while maintaining quality standards.

---

## Testing

Clew Directive follows a **QA-First** approach: tests are written before or alongside features, not as an afterthought.

### Backend Tests (Python + pytest)

**Test Coverage**: 17 test files covering agents, tools, interfaces, and Lambda handlers

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v --cov=backend --cov-report=term-missing
```

**Test Suites**:

| Test File | Coverage | Key Tests |
|-----------|----------|-----------|
| `test_lambda_handlers.py` | Lambda entry points | Vibe Check, Profile Refinement, Briefing Generation |
| `test_navigator.py` | Navigator agent | Profile synthesis, path generation, output structure |
| `test_navigator_profile.py` | Profile synthesis | Second-person voice, empathetic tone, no PII |
| `test_navigator_path.py` | Path generation | Resource selection, sequencing, reasoning quality |
| `test_scout.py` | Scout agent | Resource loading, URL verification, graceful degradation |
| `test_orchestrator.py` | Orchestration | Agent coordination, error handling, session flow |
| `test_knowledge_interface.py` | Knowledge layer | S3 directory loading, resource filtering |
| `test_directory_loader.py` | Directory tool | JSON parsing, schema validation |
| `test_resource_verifier.py` | URL verification | HTTP HEAD checks, timeout handling, retry logic |
| `test_pdf.py` | PDF generation | WeasyPrint integration, template rendering |
| `test_curator.py` | Curator Lambda | Weekly freshness checks, status updates |

**Mocks**:
- `mocks/bedrock_mocks.py`: Mock Bedrock responses (profiles, paths)
- `mocks/s3_mocks.py`: Mock S3 directory.json data

**Test Principles**:
- ✅ No real AWS calls (all mocked)
- ✅ No real Bedrock calls (mocked responses)
- ✅ Fast execution (<5 seconds for full suite)
- ✅ Isolated tests (no shared state)
- ✅ Clear assertions with descriptive messages

### Frontend Tests (Jest + React Testing Library)

**Test Coverage**: Landing page, accessibility, color contrast

```bash
cd frontend
npm test
```

**Test Suites**:

| Test File | Coverage | Key Tests |
|-----------|----------|-----------|
| `tests/landing.test.tsx` | Landing page | Terminal aesthetic, WCAG contrast ratios, component structure |

**Accessibility Tests**:
- ✅ WCAG AAA contrast (Osprey Navy + Cyber Gold: 13.24:1)
- ✅ WCAG AAA contrast (Osprey Navy + Dim Gold: 7.18:1)
- ✅ Color calculations verified programmatically

**Planned Tests** (Phase 8B):
- Vibe Check form validation
- Profile feedback flow
- Learning path display
- Error handling UI
- Retry logic
- Loading states

### Integration Tests

**End-to-End Flow** (Planned for Phase 8C):
```bash
# Start local stack
docker-compose up -d

# Run integration tests
pytest tests/integration/ -v
```

**Scenarios**:
1. Complete flow: Vibe Check → Profile → Refinement → Briefing → PDF
2. Error scenarios: Timeout, throttle, resource load failure
3. Graceful degradation: PDF failure, partial resource availability
4. Performance: Latency targets (<5s profile, <45s briefing)

### Test Commands

**Run all backend tests**:
```bash
cd backend
pytest tests/ -v
```

**Run specific test file**:
```bash
pytest tests/test_navigator.py -v
```

**Run with coverage report**:
```bash
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

**Run frontend tests**:
```bash
cd frontend
npm test
```

**Run frontend tests in watch mode**:
```bash
npm test -- --watch
```

### Quality Gates

**Before Merge**:
- ✅ All tests pass
- ✅ Coverage >80% for new code
- ✅ No linting errors
- ✅ Type checking passes (TypeScript)

**Before Deploy**:
- ✅ Integration tests pass
- ✅ Accessibility tests pass (WCAG 2.1 AA)
- ✅ Performance tests pass (latency targets)
- ✅ Cost estimation within budget

---

## Quick Start (Local Development)

```bash
# Clone
git clone https://github.com/earlgreyhot1701D/Clew-Directive.git
cd clew-directive

# Copy environment config
cp .env.example .env

# Run with Docker
docker-compose up

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

### Try the Live Demo

**Production URL**: [https://clewdirective.com](https://clewdirective.com)

The live site is deployed on AWS Amplify with:
- ✅ Real AI personalization (Amazon Nova 2 Lite)
- ✅ PDF generation with clickable links
- ✅ WCAG 2.1 AAA contrast ratios (13.24:1)
- ✅ Progressive loading states
- ✅ Stateless sessions (PDFs auto-delete after 24h, logs expire after 7 days)

### Run Tests
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## Deployment to AWS

Clew Directive uses **AWS CDK** (TypeScript) for infrastructure-as-code deployment.

### Prerequisites

- AWS account with Bedrock access
- AWS CLI installed and configured (`aws configure`)
- Node.js 20+ and Python 3.12+
- AWS CDK CLI: `npm install -g aws-cdk`

### Lambda Deployment Package

The CDK deployment uses **Docker container images** for Lambda functions:

**Architecture**:
- **Container Image**: Self-contained Lambda runtime with all dependencies
  - Built from `backend/Dockerfile.lambda`
  - Includes Python 3.12 runtime + all dependencies from `requirements-lambda.txt`
  - Strands Agents SDK (GA), boto3, WeasyPrint, Jinja2, FastAPI, Pydantic
  - Application code (agents, tools, handlers)
- **Size Limit**: Up to 10GB (vs 250MB for ZIP deployment)

**Benefits**:
- **No size constraints**: Container images support up to 10GB (vs 250MB for ZIP)
- **Simplified deployment**: Single artifact contains runtime + dependencies + code
- **Consistent environments**: Same container runs locally and in Lambda
- **Better for complex dependencies**: WeasyPrint and system libraries included
- **Faster cold starts**: Optimized container layers
- **Cross-platform builds**: Docker ensures consistent builds across Windows/Mac/Linux

### Deploy All Stacks

```bash
cd infrastructure

# Bootstrap CDK (first time only)
cdk bootstrap

# Build and deploy all stacks
npm run build
cdk deploy --all
```

**Deployed Stacks**:
1. **ClewDirective-Storage**: S3 bucket for directory.json and PDFs
2. **ClewDirective-Api**: 3 Lambda functions + API Gateway
3. **ClewDirective-Curator**: Weekly resource verification
4. **ClewDirective-Frontend**: Amplify hosting for Next.js app

**What happens during deployment**:
1. TypeScript CDK code compiles
2. **Container image build**: Docker builds Lambda container from `backend/Dockerfile.lambda`
   - Installs Python 3.12 runtime
   - Installs all dependencies from `requirements-lambda.txt`
   - Copies application code (agents, tools, handlers)
3. **Image push**: Container image pushed to Amazon ECR (Elastic Container Registry)
4. CloudFormation templates generated
5. Stacks deployed to AWS
6. **Frontend deployment**: Amplify connects to GitHub and auto-builds on push

**Note**: First deployment may take 5-10 minutes as Docker builds the container image. Subsequent deployments are faster:
- **Code-only changes**: Docker layer caching speeds up builds (~2-3 minutes)
- **Dependency changes**: Full rebuild required (~5-10 minutes)

### Upload Resources

```bash
# Upload directory.json to S3
aws s3 cp data/directory.json s3://clew-directive-data-{account-id}/data/directory.json
```

### Get Deployment URLs

```bash
# API Gateway URL
aws cloudformation describe-stacks \
  --stack-name ClewDirective-Api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text

# Amplify Frontend URL
aws cloudformation describe-stacks \
  --stack-name ClewDirective-Frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`AmplifyAppUrl`].OutputValue' \
  --output text
```

**Current Production URLs**:
- **Frontend**: https://clewdirective.com
- **API**: https://27o094toch.execute-api.us-east-1.amazonaws.com/prod/

### Test Deployment

```bash
# Test Vibe Check endpoint
curl -X POST https://27o094toch.execute-api.us-east-1.amazonaws.com/prod/vibe-check \
  -H "Content-Type: application/json" \
  -d '{"vibe_check_responses":{"skepticism":"Curious but haven'\''t started learning","goal":"Understand what AI actually is and isn'\''t","learning_style":"Reading and thinking at my own pace","context":"Business / Marketing / Operations"}}'

# Expected response: JSON with "profile" field containing personalized summary
```

Or visit the live frontend: **https://clewdirective.com**

### Bedrock Model Access

**AWS now automatically enables Bedrock models on first use.** No manual setup required!

**Models Used**:
- **Amazon Nova Micro**: Scout agent (resource verification)
- **Amazon Nova 2 Lite**: Navigator agent (profile synthesis, path generation)

Both Nova models are instantly available in all AWS accounts. No approval process needed.

**If you encounter access errors**:
1. Verify your AWS account has Bedrock enabled in your region (us-east-1 recommended)
2. Check IAM permissions include `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`
3. Try invoking the model once from the Bedrock Playground to activate it

### Monitoring

**CloudWatch Dashboard**: View real-time metrics at `ClewDirective-Monitoring` dashboard

**Alarms** (email notifications via SNS):
1. **High Traffic**: >200 briefings/day
2. **Lambda Errors**: >5 errors in 5 minutes (per function)
3. **API Gateway 5xx**: >5 server errors in 5 minutes
4. **API Gateway 4xx**: >20 client errors in 5 minutes

View Lambda logs:
```bash
# Vibe Check logs
aws logs tail /aws/lambda/ClewDirective-Api-VibeCheckFunction --follow

# Briefing generation logs
aws logs tail /aws/lambda/ClewDirective-Api-GenerateBriefingFunction --follow
```

### Cost Management

All infrastructure runs on AWS Free Tier during development. Expected cost during voting period (500 briefings):
- Bedrock: ~$5-15
- Infrastructure: $0 (Free Tier)

### Rollback

```bash
cd infrastructure

# Destroy stacks in reverse order
cdk destroy ClewDirective-Frontend
cdk destroy ClewDirective-Curator
cdk destroy ClewDirective-Api
cdk destroy ClewDirective-Storage
```

**Note**: Destroying the Storage stack will delete the S3 bucket and all PDFs. Make sure to backup `directory.json` first if needed.

**Detailed deployment guide**: See `PHASE_8C_API_DEPLOYMENT_GUIDE.md`

---

## Project Structure

```
clew-directive/
├── .kiro/                    # Kiro IDE: steering files, hooks, specs
├── backend/
│   ├── agents/               # Scout, Navigator, Orchestrator
│   ├── tools/                # Resource verifier, directory loader, PDF gen
│   ├── curator/              # Weekly freshness Lambda
│   ├── interfaces/           # Abstraction contracts (memory, knowledge, tools, email)
│   ├── config/               # Centralized settings + model tiers
│   ├── templates/            # Jinja2 HTML for PDF generation
│   ├── tests/                # QA-First test suite with mocks
│   ├── requirements.txt      # All dependencies (dev + test + prod)
│   └── requirements-lambda.txt # Production-only dependencies for Lambda deployment
├── frontend/                 # Next.js with retro-terminal UI
├── infrastructure/           # TypeScript CDK stacks
├── data/                     # directory.json (curated resources)
└── docs/                     # Accessibility checklist
```

---

## Development Workflow

**Opus (CTO)** scaffolds architecture, interface contracts, and reviews code.
**Kiro** generates specs and implements tasks via spec-driven development.
**Opus** audits Kiro's output for correctness, security, and alignment.

```
Opus scaffold → Kiro generates specs → Kiro implements → Opus audits
```

Kiro hooks automate quality gates during development:
- **test-sync**: Auto-generates tests when agent code changes
- **security-scan**: Catches leaked credentials and unsafe patterns
- **cost-check**: Estimates cost impact of infrastructure changes
- **doc-update**: Keeps API docs current

---

## What's Next

Shipped today as a focused tool for **new AI learners**. The architecture supports expansion:

- **Multiple domains**: Schema includes a `domain` field. MVP uses "ai-foundations." Future: AI for healthcare, educators, creatives, etc.
- **Community partnerships**: Integration pathways with education nonprofits, bootcamps, and public libraries to embed Clew Directive into existing learning ecosystems.
- **Email briefings**: Interface stubbed, HTML template ready. Wire up Amazon SES.
- **AgentCore Memory**: Interface exists. Swap in for cross-session context (with consent).
- **Long-term memory with consent**: Privacy-first opt-in for returning users.
- **Community curation**: GitHub issues workflow for resource contributions.

**Adoption vision**: Clew Directive becomes the default "entry point" for new AI learners globally—a trusted, free, accessible resource that removes barriers and directs learners toward verified knowledge, regardless of geography, background, or budget.

---

## About

Clew Directive is an open-source AI learning navigator built to democratize AI education.

**Creator**: [La-Shara Cordero](https://www.linkedin.com/in/la-shara-cordero-a0017a11/)  
**GitHub**: [earlgreyhot1701D/Clew-Directive](https://github.com/earlgreyhot1701D/Clew-Directive)

---

## Development Approach

**This is an AI-assisted, human-reviewed build.** All decisions and mistakes are mine. I used Kiro IDE, Claude, ChatGPT, Gemini, and other AI tools throughout development for scaffolding, code generation, testing, and architectural review. Every output was reviewed, tested, and integrated with full accountability for correctness and alignment.

---

## License

MIT — see [LICENSE](LICENSE)

---

*"Clew Directive ships today as a focused tool for new AI learners. The architecture is domain-agnostic — designed for expansion, shipped for impact."*