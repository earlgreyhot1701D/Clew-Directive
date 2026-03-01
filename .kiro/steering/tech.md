# Technical Decisions — Clew Directive

**Last Updated**: February 12, 2026  
**Source**: Enriched from conversation transcript and original scaffold

---

## Architecture Overview

Clew Directive uses a **serverless, event-driven architecture** on AWS with AI agents powered by Amazon Bedrock and Strands SDK.

**Design Philosophy**: 
- Stateless by architecture (not by accident)
- Cost-efficient (<$1 per briefing)
- Production-grade from day one
- Open source, reproducible locally

---

## Tech Stack

### Backend
- **Language**: Python 3.12+
- **Agent Framework**: Strands Agents SDK v1.0 GA
- **AI Models**: 
  - Nova Micro (Scout + Curator)
  - Amazon Nova 2 Lite (Navigator) — pivoted from Claude Sonnet 4.5 for regional availability and cost
- **PDF Engine**: WeasyPrint (HTML→PDF with clickable links)
- **Templates**: Jinja2
- **Local Dev**: Docker Compose with mocked Bedrock

**Why Python**: 
- Strands TypeScript SDK is experimental (Python is GA)
- Team familiarity
- Rich AI/ML ecosystem

### Frontend
- **Framework**: Next.js 14+ (React 18+)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Custom (retro-terminal theme)
- **Hosting**: AWS Amplify
- **State Management**: React hooks (no Redux needed for stateless app)

**Why Next.js**:
- Amplify first-class support
- SSG for landing page (fast load)
- API routes for local dev

### Infrastructure
- **IaC**: AWS CDK (TypeScript)
- **CI/CD**: GitHub Actions → CDK deploy
- **Secrets**: AWS Secrets Manager
- **Monitoring**: CloudWatch

**Why CDK over Terraform**:
- Type safety (TypeScript)
- Better AWS service coverage
- Team familiarity

---

## AWS Services & Cost Strategy

| Service | Purpose | Cost Model | Budget |
|---------|---------|------------|--------|
| **Bedrock (Nova Micro)** | Scout + Curator | $0.000035/1K input | $200 credits |
| **Bedrock (Nova 2 Lite)** | Navigator | ~$0.0001/1K input | $200 credits |
| **Lambda** | Agent execution | Free Tier: 1M req/mo | Free |
| **API Gateway** | REST API | Free Tier: 1M req/mo | Free |
| **S3** | directory.json + PDFs | Free Tier: 5GB | Free |
| **EventBridge Scheduler** | Weekly Curator cron | Free Tier: 14M invokes/mo | Free |
| **Amplify Hosting** | Frontend CDN | Free Tier: 15GB transfer | Free |
| **CloudWatch** | Logs + metrics | Free Tier: 5GB logs | Free |
| **AWS Budgets** | Cost alerts | Free | Free |

**Total Monthly Cost** (assuming 500 briefings during voting period):
- Bedrock: ~$20-30 (Nova Micro cheap, Sonnet for reasoning)
- Infrastructure: $0 (all Free Tier)
- **Total**: <$30 for entire voting period

**Why This Stack is Competition-Friendly**:
- Fits entirely within $200 AWS credits
- Minimal ongoing cost after competition
- All services Free Tier eligible

---

## Model Tiering Strategy

### Tier 1: Nova Micro (Cost-Optimized)
**Use Cases**:
- Scout: Resource verification
- Curator: URL freshness checks

**Cost**: $0.000035 per 1K input tokens  
**Why**: Simple tasks, no deep reasoning needed

**Example**:
```python
# Scout verification (no LLM needed, just HTTP checks)
is_live = requests.head(url, timeout=5).status_code < 400
```

### Tier 2: Amazon Nova 2 Lite (Reasoning — Cost/Availability Optimized)
**Use Cases**:
- Navigator: Profile synthesis
- Navigator: Learning path generation

**Cost**: ~$0.0001/1K input tokens
**Why**: Pivoted from Claude Sonnet 4.5 mid-build — Nova 2 Lite provides instant
regional availability without cross-region inference profiles, and keeps
per-briefing cost well within the $200 credit budget

**Example**:
```python
# Navigator profile synthesis
agent = Agent(
    name="ProfileSynthesizer",
    model=bedrock_client,  # Sonnet via Strands
    instructions=prompt
)
profile = agent.run(vibe_check_responses)
```

**Cost Control**: 
- Profile synthesis: ~500 tokens input, 200 output
- Path generation: ~5,000 tokens input, 1,000 output
- **Total per briefing**: ~$0.02-0.03

---

## Critical Architecture Decisions

### Decision 1: Why NOT Bedrock Knowledge Base

**Option Considered**: Use Bedrock Knowledge Base + OpenSearch Serverless for RAG

**Why Rejected**:
- OpenSearch Serverless minimum cost: ~$700/month
- Overkill for 50-100 curated resources
- Blows entire competition budget in 1 week

**Chosen Alternative**: Load directory.json directly into context
- Resources stored in S3 as JSON
- Scout loads entire JSON (< 100KB)
- Navigator receives full resource list in context
- **Cost**: $0

**Trade-off**: Can't scale to 10,000+ resources (but MVP doesn't need that)

---

### Decision 2: Why Lambda (Not App Runner or ECS)

**Options Considered**:
1. AWS App Runner (always-on container)
2. ECS Fargate (container orchestration)
3. Lambda (serverless functions)

**Chosen**: Lambda

**Rationale**:
- **Pay-per-request**: Only pay during voting period traffic
- **Free Tier**: 1M requests/month free
- **Cold start acceptable**: 2-3 second delay OK for 90-second total flow
- **Amplify integration**: Native support
- **Cost during competition**: ~$0-5 vs. App Runner $60-100/month

**Trade-off**: Cold starts (mitigated by provisioned concurrency if needed)

---

### Decision 3: Why WeasyPrint (Not Puppeteer)

**Options Considered**:
1. Puppeteer (headless Chrome)
2. WeasyPrint (CSS-based PDF rendering)
3. ReportLab (Python PDF library)

**Chosen**: WeasyPrint

**Rationale**:
- **Lightweight**: No Chromium binary (smaller Lambda package)
- **Clickable links**: Full HTML/CSS support
- **Template-friendly**: Works seamlessly with Jinja2
- **Python-native**: No Node.js needed in backend

**Trade-off**: Less visual fidelity than Puppeteer (acceptable for text-heavy PDFs)

---

### Decision 4: Why Stateless (Technical Justification)

**Not Just Privacy**: Stateless architecture has technical benefits

**Advantages**:
- **No database**: Zero DB cost, zero maintenance
- **Horizontal scaling**: Every request independent
- **Fault tolerance**: No shared state to corrupt
- **GDPR compliance**: By architecture, not by policy

**Implementation**:
- Vibe Check responses → Lambda memory (ephemeral)
- PDF → S3 with 24h TTL
- No cookies beyond session ID
- No DynamoDB, no RDS, no Redis (except local dev cache)

---

## Data Flow Architecture

### Happy Path (90 seconds total)

```
User Browser → Amplify (Next.js SPA)
    ↓ POST /vibe-check
API Gateway → Lambda: Vibe Check Handler
    ↓ Call Navigator.synthesize_profile()
Navigator Agent (Bedrock Sonnet via Strands)
    ↓ Return profile summary
Lambda → API Gateway → User Browser
    ↓ User clicks "Yes, that's me"
    ↓ POST /generate-briefing
API Gateway → Lambda: Briefing Handler
    ↓ Call Scout.gather_resources()
Scout Agent (loads directory.json from S3)
    ↓ Return verified resources
    ↓ Call Navigator.generate_learning_path()
Navigator Agent (Bedrock Sonnet via Strands)
    ↓ Return path with 4-6 resources
    ↓ Call PDFGenerator.generate()
PDF Generator (Jinja2 + WeasyPrint)
    ↓ Upload PDF to S3 (24h TTL)
Lambda → API Gateway → User Browser
    ↓ User downloads PDF
S3 → User Browser (presigned URL)
    ↓ After 24 hours
S3 Lifecycle Policy → Delete PDF
```

**Latency Breakdown**:
- Vibe Check processing: 3-5 seconds (Sonnet profile synthesis)
- Briefing generation: 25-40 seconds (Scout + Navigator + PDF)
- **Total**: 30-45 seconds (within 90-second UX budget)

---

## Error Handling Strategy

### Principle: Graceful Degradation

**Never show technical errors to users. Always friendly messages.**

### Error Scenarios

**1. Bedrock API Timeout**
```python
try:
    profile = navigator.synthesize_profile(responses)
except TimeoutError:
    return {
        "error": "user_friendly",
        "message": "Hmm, that took longer than expected. Let's try again.",
        "retry": True
    }
```

**2. Scout Finds No Resources**
```python
resources = scout.gather_resources(domain)
if len(resources) == 0:
    return {
        "error": "user_friendly",
        "message": "We're having trouble loading our resource directory. Please try again in a few minutes.",
        "retry": True
    }
```

**3. Navigator Returns Invalid JSON**
```python
try:
    path = json.loads(navigator_response)
except JSONDecodeError:
    logger.error("[navigator] Invalid JSON response")
    # Fallback: return empty path with error message
    return {
        "learning_path": [],
        "error": "generation_failed",
        "message": "We encountered an error generating your path. Please try again."
    }
```

**4. PDF Generation Fails**
```python
try:
    pdf_bytes = weasyprint.HTML(string=html).write_pdf()
except Exception as e:
    logger.error("[pdf] Generation failed: %s", e)
    # Still show path in UI, just skip PDF
    return {
        "path": learning_path,
        "pdf_url": None,
        "message": "Your learning path is ready below, but we couldn't generate the PDF. You can still access all the links here."
    }
```

---

## Cost Controls (Voting Period)

**Problem**: Voting runs March 13-20. If traffic spikes, costs could explode.

### Control 1: API Gateway Rate Limiting
```typescript
// CDK configuration
const api = new apigateway.RestApi(this, 'ClewAPI', {
  throttle: {
    rateLimit: 10,  // 10 requests/second
    burstLimit: 20
  }
});
```

**Response on limit**: 429 with message "High traffic right now! Refresh in a moment."

### Control 2: Lambda Scaling (Unreserved)

Lambda functions scale without reserved concurrency limits. API Gateway rate limiting (10 req/sec) is the primary cost guardrail.

**Behavior**: 
- Lambda scales naturally based on incoming requests
- API Gateway throttles at 10 req/sec (burst: 20)
- Requests exceeding rate limit receive 429 responses
- Prevents runaway costs from traffic spikes at the API layer
- CloudWatch metrics track API Gateway throttling

**Monitoring**: Watch API Gateway `Count` and `4XXError` metrics in CloudWatch

### Control 3: Bedrock Token Budget Alarm
```typescript
const alarm = new cloudwatch.Alarm(this, 'BedrockCostAlarm', {
  metric: bedrockTokenMetric,
  threshold: 50,  // $50/day
  evaluationPeriods: 1,
  actionsEnabled: true
});

alarm.addAlarmAction(new sns_actions.SnsAction(alertTopic));
```

**Action**: Email admin, manual review

### Control 4: AWS Budgets
- Total budget: $200
- Alerts at 50% ($100), 75% ($150), 90% ($180)
- Email notifications

### Control 5: Front-Door Usage Cap (Optional)
```python
# Track daily briefings in CloudWatch metric
daily_count = cloudwatch.get_metric("BriefingsGenerated", "Today")

if daily_count > 500:
    return {
        "error": "capacity",
        "message": "We're at capacity for today. Try again tomorrow! (This helps us stay within our student budget.)"
    }
```

**Rationale**: 500 briefings/day × 8 days = 4,000 total (well above competition target)

---

## Security & Compliance

### IAM Least Privilege
```typescript
// Scout Lambda: read-only S3 access to directory.json
scoutRole.addToPolicy(new iam.PolicyStatement({
  actions: ['s3:GetObject'],
  resources: [`${directoryBucket.bucketArn}/directory.json`]
}));

// Navigator Lambda: invoke Bedrock only
navigatorRole.addToPolicy(new iam.PolicyStatement({
  actions: ['bedrock:InvokeModel'],
  resources: ['arn:aws:bedrock:*::foundation-model/anthropic.claude-v4-sonnet']
}));
```

### Input Sanitization
```python
# Vibe Check validation
def validate_vibe_check(responses: dict) -> bool:
    required_keys = ['skepticism', 'goal', 'learning_style', 'context']
    if not all(k in responses for k in required_keys):
        return False
    
    # Ensure values are strings, not objects/arrays
    if not all(isinstance(v, str) for v in responses.values()):
        return False
    
    # Max length: 200 chars per answer
    if any(len(v) > 200 for v in responses.values()):
        return False
    
    return True
```

### No PII Storage
- No names, emails, phone numbers collected
- Vibe Check responses never written to disk
- Session ID is random UUID (not user-identifiable)
- PDF filename: `command-briefing-{uuid}.pdf` (no user info)

---

## Build Principles (SHARA)

### S — Single Responsibility
**One file, one job.**

```
backend/agents/scout.py        # Scout agent only
backend/agents/navigator.py    # Navigator agent only
backend/agents/orchestrator.py # Coordinates agents, doesn't implement logic
```

### H — Interface Contracts
**Every external integration has a defined interface.**

```python
# backend/interfaces/knowledge_interface.py
class KnowledgeInterface:
    def load_resources(self, domain: str) -> list[dict]:
        """Load resources from S3 directory.json"""
        raise NotImplementedError
```

**Benefit**: Mock easily in tests

### A — QA-First
**Mocks and golden tests before features.**

```python
# Write test first
def test_navigator_synthesizes_profile():
    navigator = NavigatorAgent()
    profile = navigator.synthesize_profile(sample_responses)
    assert "you" in profile.lower()  # Second person
    assert len(profile) > 100  # Reasonable length

# Then implement
def synthesize_profile(self, responses):
    # Implementation here
    pass
```

### R — Security by Design
**Least-privilege IAM, input sanitization, no PII.**

Already covered in Security section above.

### A — Graceful Degradation
**Timeout → friendly message, not crash.**

Already covered in Error Handling section above.

---

## Logging Strategy

### Structured Logging
```python
import logging

logger = logging.getLogger("clew.agent.scout")

# Good: Structured with context
logger.info(
    "[agent:scout] Loaded %d resources for domain=%s",
    len(resources),
    domain
)

# Bad: Unstructured
logger.info("Scout done")
```

### Log Levels
- **INFO**: Successful operations
  - `[agent:scout] Loaded 47 resources`
  - `[agent:navigator] Profile synthesized: 156 chars`
- **WARNING**: Recoverable issues
  - `[agent:scout] Resource verification failed for id=X, including anyway`
  - `[agent:navigator] Profile refinement cap reached`
- **ERROR**: Unrecoverable failures
  - `[curator] Freshness check failed: >10% resources offline`
  - `[pdf] Generation failed: WeasyPrint error`

### CloudWatch Insights Queries
```
# Find failed briefings
fields @timestamp, @message
| filter @message like /generation_failed/
| sort @timestamp desc

# Navigator latency
fields @timestamp, @duration
| filter @message like /agent:navigator/
| stats avg(@duration), max(@duration), min(@duration)
```

---

## Testing Strategy

### Unit Tests (pytest)
**Target**: 85% coverage for agent logic

```bash
pytest backend/tests/test_scout.py -v --cov=backend/agents/scout
```

**Key Tests**:
- Scout loads resources correctly
- Navigator synthesizes valid profiles
- Orchestrator calls agents in correct order
- PDF generator produces valid PDFs

### Integration Tests
**End-to-end flow**:
```python
def test_e2e_vibe_check_to_pdf():
    # Submit Vibe Check
    response = client.post('/vibe-check', json=vibe_responses)
    profile = response.json()['profile']
    
    # Approve profile
    response = client.post('/generate-briefing', json={'profile': profile})
    pdf_url = response.json()['pdf_url']
    
    # Download PDF
    pdf_response = requests.get(pdf_url)
    assert pdf_response.status_code == 200
    assert pdf_response.headers['Content-Type'] == 'application/pdf'
```

### Accessibility Tests
```bash
# Install axe-core
npm install -D @axe-core/cli

# Run on deployed site
axe https://clewdirective.com --tags wcag2a,wcag2aa
```

**Target**: Zero violations for WCAG 2.1 AA

---

## Local Development

### Docker Compose Setup
```yaml
# docker-compose.yml
services:
  bedrock-mock:
    image: localstack/localstack
    environment:
      SERVICES: bedrock
    ports:
      - "4566:4566"
  
  s3-local:
    image: minio/minio
    ports:
      - "9000:9000"
    volumes:
      - ./data:/data
  
  backend:
    build: ./backend
    environment:
      AWS_ENDPOINT_URL: http://bedrock-mock:4566
      S3_ENDPOINT_URL: http://s3-local:9000
    depends_on:
      - bedrock-mock
      - s3-local
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

**Start**:
```bash
docker-compose up -d
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

---

## Deployment Pipeline

### Environments
1. **Local**: Docker Compose (mocked Bedrock)
2. **Staging**: CDK deploy to dev AWS account
3. **Production**: CDK deploy to prod AWS account

### CI/CD (GitHub Actions)
```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest backend/tests --cov
      - run: npm test frontend/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install -g aws-cdk
      - run: cd infrastructure && npm install
      - run: cdk deploy --all --require-approval never
```

**Stages**:
1. Tests must pass
2. CDK synth validates
3. Deploy to staging
4. Manual approval
5. Deploy to production

---

## Monitoring Dashboard

### CloudWatch Dashboard
**Metrics to Track**:
1. **Usage**:
   - Briefings generated (count)
   - Refinement rate (%)
   - PDF downloads (count)
2. **Performance**:
   - Navigator latency (p50, p95, p99)
   - Scout latency
   - API Gateway latency
3. **Errors**:
   - Lambda errors (count)
   - Bedrock throttles (count)
   - PDF generation failures (count)
4. **Cost**:
   - Bedrock token usage (daily)
   - Estimated daily cost

---

## Open Technical Questions

1. **Provisioned Concurrency for Lambda?**
   - **Current**: On-demand (cold starts 2-3 sec)
   - **Alternative**: Provision 1-2 warm instances
   - **Decision**: Wait for load test results

2. **Redis Caching for Scout Results?**
   - **Current**: Load directory.json on every request
   - **Alternative**: Cache in Redis for 1 hour
   - **Decision**: Implement if latency >500ms

3. **Custom Domain for Amplify?**
   - **Current**: Amplify default (*.amplifyapp.com)
   - **Alternative**: clewdirective.com
   - **Decision**: Nice-to-have, not critical for competition

---

**Document Owner**: CTO / Technical Lead  
**Stakeholders**: Engineering, DevOps, Competition Judges  
**Review Cadence**: Weekly during development  
**Status**: Ready for Kiro implementation