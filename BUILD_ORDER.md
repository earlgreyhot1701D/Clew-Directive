# Clew Directive Build Order

**Version**: 1.0  
**Date**: February 12, 2026  
**Purpose**: Sequenced implementation plan for building Clew Directive

---

## Current Status: Phase 8C Code Complete ✅

**Last Updated**: February 14, 2026  
**Completed**: Phases 0-8C (Foundation → API Deployment Code)  
**Next**: AWS Deployment Execution (requires AWS account setup)

### Recently Completed:
- ✅ Phase 8C: API Deployment Code
  - CDK infrastructure stacks verified
  - Lambda handlers ready with correct imports
  - Deployment scripts created (Bash + PowerShell)
  - Comprehensive deployment guide written
  - CDK synthesis successful
  - TypeScript compilation successful
  - All code ready for AWS deployment
- ✅ Phase 8B: Frontend Integration with Real API
  - API client layer with TypeScript interfaces
  - Real API calls replacing all mock data
  - Comprehensive error handling with retry logic
  - PDF warning handling for graceful degradation
  - All TypeScript diagnostics passing
- ✅ Phase 7: Curator Lambda
  - Automated freshness checks for resources
  - Status progression (active → degraded → stale → dead)
  - S3 integration for directory.json updates
  - CloudWatch metrics for failure tracking
  - Lambda wrapper ready for deployment
  - All 17 curator tests passing

### What's Working:
- Backend API server running at http://localhost:8000
- Frontend dev server running at http://localhost:3000
- 17 backend tests passing (including all curator tests)
- Frontend UI complete (terminal aesthetic, WCAG AAA compliant)
- Frontend connected to real API (no more mock data)
- Curator logic complete and tested
- All Lambda handlers ready for deployment
- CDK infrastructure code complete and verified
- Deployment scripts ready (Bash + PowerShell)

---

## How to Use This Document

Kiro will execute tasks in order. Each phase has:
- **Prerequisites**: What must exist first
- **Deliverables**: Concrete outputs
- **Validation**: How to verify completion
- **Effort**: S (Small), M (Medium), L (Large)

**Critical Path Items**: 🔴 Must complete before next phase  
**Parallelizable Items**: 🟢 Can work on simultaneously

---

## Phase 0: Foundation Setup ✅ COMPLETE

**Goal**: Establish development environment  
**Status**: ✅ Complete  
**Completed**: February 12, 2026

### Task 0.1: Local Development Environment 🔴
**Prerequisites**: Docker installed

**Actions**:
1. Verify Docker Compose at `docker-compose.yml`
2. Build services: `docker-compose build`
3. Start: `docker-compose up -d`
4. Verify mocked Bedrock container running
5. Verify S3-compatible store (MinIO) running

**Deliverables**:
- Running Docker containers
- `.env.local` with connection strings

**Validation**: `docker ps` shows 2+ containers  
**Effort**: S

---

### Task 0.2: Install Dependencies 🔴
**Prerequisites**: Python 3.12+, Node 20+

**Actions**:
1. Backend: `cd backend && pip install -r requirements.txt`
2. Frontend: `cd frontend && npm install`
3. Infrastructure: `cd infrastructure && npm install`

**Deliverables**: All dependencies installed

**Validation**: No errors during install  
**Effort**: S

---

### Task 0.3: Configure AWS CDK 🟢
**Prerequisites**: AWS CLI configured

**Actions**:
1. Review `infrastructure/bin/app.ts`
2. Initialize: `cd infrastructure && cdk init`
3. Bootstrap: `cdk bootstrap`
4. Validate: `cdk synth` (don't deploy yet)

**Deliverables**: CDK bootstrapped, synth succeeds

**Validation**: `cdk synth` outputs CloudFormation  
**Effort**: M

---

## Phase 1: Knowledge Interface & Directory ✅ COMPLETE

**Goal**: Build data layer for resource loading  
**Status**: ✅ Complete  
**Completed**: February 13, 2026

### Task 1.1: Implement KnowledgeInterface 🔴
**Prerequisites**: Phase 0 complete

**Location**: `backend/interfaces/knowledge_interface.py`

**Actions**:
1. Review existing stub
2. Implement `load_resources(domain: str)`:
   - Read directory.json from S3 (or local file in dev)
   - Filter by domain
   - Filter by status="active"
   - Return list of resource dicts
3. Add error handling (file not found → empty list)

**Deliverables**: `knowledge_interface.py` complete

**Validation**: 
```python
from backend.interfaces.knowledge_interface import KnowledgeInterface
k = KnowledgeInterface()
resources = k.load_resources("ai-foundations")
assert len(resources) > 0
```

**Effort**: M

---

### Task 1.2: Populate directory.json 🟢
**Prerequisites**: None (can run parallel)

**Location**: `data/directory.json`

**Actions**:
1. Verify existing sample resources
2. Add 10-15 real resources from:
   - Elements of AI (Helsinki)
   - Fast.ai courses
   - Google AI courses
   - Microsoft Learn AI
3. Ensure variety in:
   - Difficulty (beginner, intermediate)
   - Format (course, tutorial, article)
   - Category (foundations, building, responsible-ai)

**Deliverables**: directory.json with 15+ resources

**Validation**: JSON validates, all URLs are live  
**Effort**: L (manual research)

---

## Phase 2: Scout Agent ✅ COMPLETE

**Goal**: Implement resource verification agent  
**Status**: ✅ Complete  
**Completed**: February 13, 2026

### Task 2.1: Implement Resource Verifier Tool 🔴
**Prerequisites**: Task 1.1 complete

**Location**: `backend/tools/resource_verifier.py`

**Actions**:
1. Review stub
2. Implement `verify_url(url: str) -> bool`:
   - HTTP HEAD request with 5-second timeout
   - Return True if status 200-399
   - Return False otherwise
3. Add retry logic (2 retries with backoff)

**Deliverables**: `resource_verifier.py` complete

**Test**:
```python
from backend.tools.resource_verifier import verify_url
assert verify_url("https://course.elementsofai.com/") == True
assert verify_url("https://broken-url-12345.com/") == False
```

**Effort**: S

---

### Task 2.2: Implement Scout Agent 🔴
**Prerequisites**: Tasks 1.1, 2.1 complete

**Location**: `backend/agents/scout.py`

**Actions**:
1. Review existing stub
2. Wire KnowledgeInterface to `gather_resources()`
3. Add optional URL verification using resource_verifier
4. Implement graceful degradation (see REQUIREMENTS.md §2.1)

**Deliverables**: `scout.py` complete

**Test**: Run `backend/tests/test_scout.py`

**Effort**: M

---

## Phase 3: Navigator Agent (Profile Synthesis) ✅ COMPLETE

**Goal**: Implement profile generation from Vibe Check  
**Status**: ✅ Complete  
**Completed**: February 13, 2026

### Task 3.1: Strands SDK Integration 🔴
**Prerequisites**: Phase 0 complete

**Location**: `backend/agents/navigator.py`

**Actions**:
1. Install Strands SDK: `pip install strands-agents-sdk`
2. Review Strands docs for Claude 4 Sonnet usage
3. Initialize Strands client with Bedrock config
4. Test basic agent call with mock prompt

**Deliverables**: Strands client working

**Validation**: Successfully call Bedrock via Strands  
**Effort**: M

---

### Task 3.2: Implement Profile Synthesis 🔴
**Prerequisites**: Task 3.1 complete

**Location**: `backend/agents/navigator.py → synthesize_profile()`

**Actions**:
1. Build prompt template:
   - Input: Vibe Check responses dict
   - Instructions: Generate 3-4 sentence profile, second person, empathetic
   - Output: String
2. Call Strands agent with Claude 4 Sonnet
3. Parse and return profile string

**Deliverables**: `synthesize_profile()` complete

**Test**:
```python
responses = {
  "skepticism": "Curious but haven't started",
  "goal": "Understand what AI is",
  "learning_style": "Reading at own pace",
  "context": "Business"
}
profile = navigator.synthesize_profile(responses)
assert len(profile) > 100  # Reasonable length
assert "you" in profile.lower()  # Second person
```

**Effort**: L

---

### Task 3.3: Implement Profile Refinement 🟢
**Prerequisites**: Task 3.2 complete

**Location**: `backend/agents/navigator.py → refine_profile()`

**Actions**:
1. Build refinement prompt:
   - Input: Original profile + user correction
   - Instructions: Regenerate incorporating feedback
   - Output: Revised profile
2. Call Strands agent
3. Return revised profile

**Deliverables**: `refine_profile()` complete

**Test**: Similar to 3.2

**Effort**: M

---

## Phase 4: Navigator Agent (Learning Path) ✅ COMPLETE

**Goal**: Implement path generation  
**Status**: ✅ Complete  
**Completed**: February 13, 2026

### Task 4.1: Implement Path Generation 🔴
**Prerequisites**: Tasks 2.2, 3.2 complete

**Location**: `backend/agents/navigator.py → generate_learning_path()`

**Actions**:
1. Build path generation prompt:
   - Input: Profile + array of resources from Scout
   - Instructions: Select 4-6 resources, sequence them, provide reasoning
   - Output: Structured JSON (see REQUIREMENTS.md §2.2)
2. Parse JSON response from Sonnet
3. Validate:
   - 4-6 resources
   - Prerequisites respected
   - Total hours 30-60
4. Return structured path dict

**Deliverables**: `generate_learning_path()` complete

**Test**: Run `backend/tests/test_navigator.py`

**Effort**: L

---

## Phase 5: Orchestrator (Flow Coordination) ✅ COMPLETE

**Goal**: Wire agents together in correct sequence  
**Status**: ✅ Complete  
**Completed**: February 13, 2026

### Task 5.1: Implement Orchestrator 🔴
**Prerequisites**: Phases 2-4 complete

**Location**: `backend/agents/orchestrator.py`

**Actions**:
1. Review existing stub
2. Implement `process_vibe_check()`:
   - Call Navigator.synthesize_profile()
   - Return profile for feedback
3. Implement `process_refinement()`:
   - Call Navigator.refine_profile()
   - Return revised profile
4. Implement `generate_briefing()`:
   - Call Scout.gather_resources()
   - Call Navigator.generate_learning_path()
   - Return path dict
5. Add logging for each step

**Deliverables**: `orchestrator.py` complete

**Test**: Run `backend/tests/test_orchestrator.py`

**Effort**: M

---

## Phase 6: PDF Generation ✅ COMPLETE

**Goal**: Create Command Briefing PDF from path  
**Status**: ✅ Complete  
**Completed**: February 13, 2026  
**Note**: PDF generation works on Linux/Docker; requires GTK+ libraries on Windows

### Task 6.1: Create Jinja2 Template 🟢
**Prerequisites**: None (can run parallel)

**Location**: `backend/templates/command_briefing.html`

**Actions**:
1. Review existing template
2. Enhance with:
   - Header (timestamp, session ID, tagline)
   - Section 1: Profile summary
   - Section 2: Learning path (loop over resources)
   - Section 3: Next steps
   - Footer (verification date, privacy note)
3. Ensure clickable URLs: `<a href="{{ resource.resource_url }}">`
4. Apply clean, professional CSS

**Deliverables**: Jinja2 template complete

**Validation**: Render with sample data, verify structure  
**Effort**: M

---

### Task 6.2: Implement PDF Generator 🔴
**Prerequisites**: Task 6.1 complete

**Location**: `backend/tools/pdf_generator.py`

**Actions**:
1. Review stub
2. Implement `generate_pdf()`:
   - Render Jinja2 template with path data
   - Convert HTML to PDF using WeasyPrint
   - Return PDF bytes
3. Add error handling (WeasyPrint failures)

**Deliverables**: `pdf_generator.py` complete

**Test**:
```python
from backend.tools.pdf_generator import generate_pdf
pdf_bytes = generate_pdf(sample_path_data)
assert len(pdf_bytes) > 0
# Manually open PDF to verify clickable links
```

**Effort**: M

---

## Phase 7: Curator Lambda ✅ COMPLETE

**Goal**: Automated freshness checks  
**Status**: ✅ Complete  
**Completed**: February 14, 2026

### Task 7.1: Implement Curator Logic ✅
**Prerequisites**: Task 2.1 complete

**Location**: `backend/curator/freshness_check.py`

**Status**: ✅ COMPLETE

**Completed Actions**:
1. ✅ Implemented `check_freshness()`:
   - Loads all resources from directory.json
   - Verifies each URL using resource_verifier
   - Updates `last_verified` timestamp
   - Marks dead URLs with status progression (active → degraded → stale → dead)
   - Logs failures with detailed metrics
2. ✅ CloudWatch metric alarm for >10% failure rate
3. ✅ S3 integration for reading/writing directory.json
4. ✅ Comprehensive error handling

**Deliverables**: `freshness_check.py` complete

**Test**: ✅ All 17 curator tests passing (`pytest tests/test_curator.py -v`)

**Effort**: M

---

### Task 7.2: Deploy Curator Lambda ✅
**Prerequisites**: Task 7.1 complete

**Location**: `backend/lambda_curator.py`

**Status**: ✅ COMPLETE (Lambda wrapper ready for deployment)

**Completed Actions**:
1. ✅ Created Lambda wrapper (`backend/lambda_curator.py`)
2. ✅ Integrated with existing curator logic
3. ✅ Error handling and logging
4. 🔴 CDK deployment pending (will deploy with Phase 8C)

**Deliverables**: Lambda handler ready

**Validation**: Code complete, tests passing  
**Effort**: S

**Note**: CDK deployment to AWS will happen in Phase 8C alongside API deployment

---

## Phase 8: API Layer & Error Handling ✅ COMPLETE

**Goal**: Expose backend as REST API with production-quality error handling  
**Status**: ✅ Complete (Phase 8A + 8A.5)  
**Completed**: February 14, 2026

### Task 8A: Local Development API Server ✅
**Prerequisites**: Phase 5 complete

**Location**: `backend/main.py`

**Actions**:
1. ✅ Created FastAPI server wrapping Lambda handlers
2. ✅ Three endpoints: POST /vibe-check, POST /refine-profile, POST /generate-briefing
3. ✅ CORS enabled for localhost:3000
4. ✅ Request/response validation with Pydantic
5. ✅ API docs at http://localhost:8000/docs
6. ✅ Server running successfully

**Deliverables**: FastAPI server at http://localhost:8000

**Validation**: 
```bash
curl -X POST http://localhost:8000/vibe-check \
  -H "Content-Type: application/json" \
  -d '{"vibe_check_responses": {...}}'
```

**Effort**: M  
**Status**: ✅ COMPLETE

---

### Task 8A.5: Production-Quality Error Handling ✅
**Prerequisites**: Task 8A complete

**Location**: `backend/exceptions.py`, all agent files, all Lambda handlers

**Actions**:
1. ✅ Created custom exception system (`backend/exceptions.py`):
   - ClewException base class with user_message, technical_message, retry_allowed, http_status
   - 9 specific exceptions: ValidationError, BedrockTimeoutError, BedrockThrottleError, etc.
2. ✅ Enhanced Navigator agent:
   - Timeout handling (30s for profiles, 60s for paths)
   - Throttle detection
   - Response validation
   - Graceful fallbacks (template-based profile, heuristic path)
3. ✅ Enhanced Scout agent:
   - Resource loading error handling
   - Empty resource checks
   - Verification failure tracking
   - All-failed safety check
4. ✅ Enhanced Orchestrator:
   - Proper exception propagation
   - Wraps generic errors in user-friendly ClewExceptions
5. ✅ Updated all Lambda handlers:
   - Unified error response format: `{error: string, retry_allowed: boolean}`
   - Catches ClewException and uses user-friendly messages
   - PDF failure doesn't fail request (partial success)
6. ✅ Comprehensive logging strategy:
   - INFO: Successful operations
   - WARNING: Fallbacks, high failure rates
   - ERROR: Timeouts, throttling, load failures

**Deliverables**: 
- `backend/exceptions.py` (NEW)
- Enhanced error handling in all agents and handlers
- User-friendly error messages
- Graceful degradation at all levels

**Validation**: 
- All tests passing (17/17)
- Error scenarios handled gracefully
- User-friendly messages for all error types

**Effort**: L  
**Status**: ✅ COMPLETE

**Documentation**: See `PHASE_8A5_ERROR_HANDLING_COMPLETE.md`

---

### Task 8B: Frontend Integration with Real API 🔴 NEXT
**Prerequisites**: Tasks 8A, 8A.5 complete

**Location**: `frontend/src/app/page.tsx`

**Actions**:
1. Replace mock data with real API calls
2. Add error state management to React components
3. Display user-friendly error messages
4. Implement retry logic with exponential backoff
5. Add loading states with timeout warnings
6. Handle partial success (path without PDF)
7. Test with multiple user profiles to verify result variation

**Deliverables**: Frontend connected to real backend API

**Validation**: 
- Complete flow works: Vibe Check → Profile → Briefing → PDF
- Different inputs produce different outputs
- Error messages display correctly
- Retry logic works

**Effort**: L  
**Status**: 🔴 IN PROGRESS

---

### Task 8C: Deploy API Stack (Lambda + API Gateway) ✅
**Prerequisites**: Tasks 8A, 8A.5, 8B complete

**Location**: `infrastructure/lib/api-stack.ts`

**Status**: ✅ CODE COMPLETE, READY FOR AWS DEPLOYMENT

**Completed Actions**:
1. ✅ Reviewed and verified CDK stack configuration
2. ✅ Fixed curator Lambda handler path
3. ✅ Created deployment scripts (deploy.sh, deploy.ps1)
4. ✅ Created comprehensive deployment guide
5. ✅ Verified CDK synthesis works
6. ✅ All TypeScript compiles without errors
7. ✅ All Lambda handlers ready with correct imports

**Deliverables**: 
- CDK stacks ready for deployment
- Deployment scripts created
- Complete deployment guide

**Validation**: 
- ✅ `cdk synth` succeeds
- ✅ TypeScript compiles
- ⏸️ Actual AWS deployment pending (requires AWS account setup)

**Effort**: M (Code: 2 hours, Deployment: 4-6 hours)  
**Status**: ✅ CODE COMPLETE

**Note**: Actual deployment to AWS requires:
- AWS account with Bedrock access
- AWS CLI configured
- CDK bootstrapped
- See `PHASE_8C_API_DEPLOYMENT_GUIDE.md` for complete instructions

---

## Phase 9: Frontend (Next.js) ✅ COMPLETE (UI Only)

**Goal**: Build user interface  
**Status**: ✅ UI Complete, 🔴 API Integration Pending  
**Completed**: February 14, 2026 (UI), In Progress (API Integration)

**Note**: All UI components are complete with terminal aesthetic and WCAG AAA compliance. Currently using mock data. Phase 8B will connect to real API.

### Task 9.1: Landing Page ✅
**Status**: ✅ COMPLETE

**Deliverables**: 
- Two-column landing layout
- Terminal aesthetic (Osprey Navy + Cyber Gold)
- WCAG AAA compliant (13.24:1 contrast ratio)
- "Get Your Free AI Learning Plan" CTA
- "How It Works" section
- About modal with philosophy, privacy, curation
- Everything above fold on desktop

**Validation**: ✅ Running at http://localhost:3000  
**Effort**: M

---

### Task 9.2: Vibe Check Component ✅
**Status**: ✅ COMPLETE

**Deliverables**: 
- Accordion-style wizard (one question active at a time)
- Progressive disclosure with checkmarks
- Edit buttons for completed questions
- Progress bar showing X/4 completion
- 4 questions: Skepticism, Goal, Learning Style, Background
- "See My Plan" button (appears when all 4 answered)

**Validation**: ✅ All 4 questions work, state management correct  
**Effort**: M

---

### Task 9.3: Profile Feedback Component ✅
**Status**: ✅ COMPLETE (using mock data)

**Deliverables**: 
- Displays profile summary
- "That's Me" and "Not Quite" buttons
- Refinement text area (200 char limit)
- One refinement cap
- Reset to Q1 after second rejection

**Validation**: ✅ Feedback loop works with mock data  
**Effort**: L

---

### Task 9.4: Learning Path Display ✅
**Status**: ✅ COMPLETE (using mock data)

**Deliverables**: 
- Visual resource cards with category badges
- Metadata badges (hours/difficulty/format)
- Prominent reasoning panels ("WHY THIS RESOURCE")
- START LEARNING button linking to resources
- Summary section with total hours and next steps
- All animations respect prefers-reduced-motion

**Validation**: ✅ Displays mock learning path correctly  
**Effort**: M

---

### Task 9.5: Download PDF Component ✅
**Status**: ✅ COMPLETE (using mock URL)

**Deliverables**: 
- Download button
- Opens PDF in new tab
- Triggers download to device
- Loading spinner during generation

**Validation**: ✅ Button works with mock URL  
**Effort**: S

---

### Task 9.6: Navigation & UX Enhancements ✅
**Status**: ✅ COMPLETE

**Deliverables**: 
- Start Over button (top-left, sticky header)
- About button (always visible)
- Confirmation dialog for Start Over
- Honest language ("Free to Use" not "Always Free")
- Certificate disclaimer
- Responsive design (mobile + desktop)

**Validation**: ✅ All navigation works  
**Effort**: M

---

## Phase 10: Frontend Deployment 🔴 TODO

**Goal**: Deploy to AWS Amplify  
**Status**: 🔴 TODO (will deploy after Phase 8C)  
**Priority**: High (required for public access)

### Task 10.1: Configure Amplify 🔴
**Prerequisites**: Phase 9 complete

**Location**: `infrastructure/lib/frontend-stack.ts`

**Actions**:
1. Review CDK stack
2. Configure Amplify app:
   - Connect to Git repo
   - Set build settings (Next.js)
   - Configure environment variables (API Gateway URL)
3. Deploy: `cdk deploy FrontendStack`

**Deliverables**: Deployed Amplify app

**Validation**: Visit public URL, test end-to-end  
**Effort**: M

---

### Task 10.2: Configure Custom Domain (Optional) 🟢
**Prerequisites**: Task 10.1 complete

**Actions**:
1. Register domain (clewdirective.com or similar)
2. Add custom domain in Amplify console
3. Verify SSL certificate
4. Update DNS records

**Deliverables**: Custom domain working

**Validation**: Visit https://clewdirective.com  
**Effort**: S

---

## Phase 10.5: Complete Docker Configuration 🔴 TODO

**Goal**: Finalize docker-compose.yml for one-command deployment  
**Status**: 🔴 TODO (will implement after Phase 10)  
**Priority**: High (required for competition submission)

### Task 10.5.1: Update Backend Docker Command 🔴
**Prerequisites**: Phase 9 complete (backend API working)

**Current State**: docker-compose.yml has placeholder command

**Actions**:
1. Open `docker-compose.yml`
2. Replace backend command placeholder with:
```yaml
command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
3. Ensure backend/Dockerfile exists and installs all Python dependencies

**Deliverables**: Backend runs actual API server in Docker

**Validation**: 
```bash
docker-compose up backend
curl http://localhost:8000/health  # Should return 200
```

**Effort**: S

---

### Task 10.5.2: Add LocalStack for S3 Mocking 🟢
**Prerequisites**: Task 10.5.1 complete

**Actions**:
1. Uncomment LocalStack service in docker-compose.yml:
```yaml
localstack:
  image: localstack/localstack:latest
  ports:
    - "4566:4566"
  environment:
    - SERVICES=s3
    - DEBUG=1
```
2. Update backend environment to point to LocalStack:
```yaml
environment:
  - AWS_ENDPOINT_URL=http://localstack:4566
```
3. Create init script to create S3 bucket and upload directory.json

**Deliverables**: LocalStack S3 working in Docker

**Validation**:
```bash
docker-compose up localstack
aws --endpoint-url=http://localhost:4566 s3 ls
```

**Effort**: M

---

### Task 10.5.3: Test Full Docker Stack 🔴
**Prerequisites**: Tasks 10.5.1, 10.5.2 complete

**Actions**:
1. Stop all manually-running services
2. Run: `docker-compose down && docker-compose up --build`
3. Test complete flow:
   - Navigate to http://localhost:3000
   - Complete Vibe Check
   - Generate briefing
   - Download PDF
4. Verify all services communicate
5. Check logs for errors

**Deliverables**: `docker-compose up` works end-to-end

**Validation**: Fresh clone → `docker-compose up` → app works

**Effort**: M

---

### Task 10.5.4: Update README with Docker Instructions 🟢
**Prerequisites**: Task 10.5.3 complete

**Actions**:
1. Add Quick Start section to README.md:
```markdown
## Quick Start (Docker)

1. Install Docker Desktop
2. Clone this repo: `git clone <repo-url>`
3. Copy `.env.example` to `.env`
4. Run: `docker-compose up`
5. Open: http://localhost:3000
```
2. Add troubleshooting section for common Docker issues

**Deliverables**: Clear Docker setup instructions in README

**Validation**: Non-technical user can follow README successfully

**Effort**: S

---

## Phase 11: Testing & Quality Assurance

**Goal**: Ensure production readiness  
**Critical Path**: Required before competition launch

### Task 11.1: Unit Test Coverage 🔴
**Prerequisites**: All phases complete

**Actions**:
1. Run: `pytest backend/tests --cov`
2. Target: 85% coverage
3. Fix failing tests
4. Add missing tests for:
   - Scout edge cases
   - Navigator golden tests
   - Orchestrator error paths

**Deliverables**: 85%+ test coverage

**Validation**: `pytest` all green  
**Effort**: L

---

### Task 11.2: Integration Testing 🔴
**Prerequisites**: API deployed

**Actions**:
1. End-to-end test:
   - Submit Vibe Check responses
   - Verify profile synthesis
   - Test refinement flow
   - Generate learning path
   - Download PDF
   - Verify PDF links are clickable
2. Test error scenarios:
   - Bedrock timeout
   - Invalid Vibe Check input
   - Dead resource URLs
3. Document test results

**Deliverables**: E2E test suite passing

**Validation**: All scenarios pass  
**Effort**: M

---

### Task 11.3: Accessibility Testing 🔴
**Prerequisites**: Frontend deployed

**Actions**:
1. Run axe DevTools on all pages
2. Fix flagged issues (WCAG 2.1 AA)
3. Manual screen reader test (NVDA):
   - Vibe Check flow
   - Profile feedback
   - Learning path display
4. Keyboard-only navigation test
5. Test text resize to 200%

**Deliverables**: Zero axe violations, screen reader works

**Validation**: WCAG 2.1 AA compliant  
**Effort**: M

---

## Phase 12: Monitoring & Cost Controls

**Goal**: Production hardening  
**Critical Path**: Required before public launch

### Task 12.1: CloudWatch Alarms 🔴
**Prerequisites**: All infrastructure deployed

**Actions**:
1. Create alarms in CDK:
   - Bedrock token spend >$50/day
   - API Gateway 5xx errors >5%
   - Lambda errors >10/hour
2. Create SNS topic for alerts
3. Subscribe admin email
4. Deploy: `cdk deploy MonitoringStack`

**Deliverables**: CloudWatch alarms active

**Validation**: Trigger test alarm, verify email  
**Effort**: M

---

### Task 12.2: AWS Budgets 🟢
**Prerequisites**: None

**Actions**:
1. Create budget: $200 total
2. Alerts at 50%, 75%, 90%
3. Email notifications to admin

**Deliverables**: Budget configured

**Validation**: Verify in AWS Console  
**Effort**: S

---

### Task 12.3: Rate Limiting Verification 🔴
**Prerequisites**: API deployed

**Actions**:
1. Load test with Artillery:
   - 20 req/sec for 1 minute
   - Verify throttling at 10 req/sec
   - Check 429 responses
2. Adjust limits if needed

**Deliverables**: Rate limits working

**Validation**: Artillery report shows throttling  
**Effort**: S

---

## Phase 13: Documentation & Launch Prep

**Goal**: Competition readiness  
**Critical Path**: Required for article submission

### Task 13.1: Write README 🟢
**Prerequisites**: All phases complete

**Location**: `README.md`

**Actions**:
1. Project overview
2. Architecture diagram
3. Local dev instructions:
   - Docker Compose setup
   - Environment variables
   - Running tests
4. Deployment instructions
5. Competition details
6. License (open source)

**Deliverables**: Comprehensive README

**Validation**: Fresh clone, follow README, works  
**Effort**: M

---

### Task 13.2: Write Competition Article 🔴
**Prerequisites**: All phases complete

**Actions**:
1. Draft article (1500-2000 words):
   - Problem: AI learning is overwhelming
   - Solution: Clew Directive's approach
   - How it works: Scout + Navigator + Curator
   - Why it matters: Democratizing AI education
   - Technical highlights: Stateless, WCAG AA, cost-efficient
   - Call to action: Try it, vote for us
2. Include screenshots
3. Include architecture diagram
4. Narrative: "Designed for expansion, shipped for impact"

**Deliverables**: Article draft

**Validation**: Peer review  
**Effort**: L

---

### Task 13.3: Create Demo Video (Optional) 🟢
**Prerequisites**: Frontend deployed

**Actions**:
1. Record 2-3 minute walkthrough:
   - Landing page
   - Vibe Check flow
   - Profile feedback
   - Learning path display
   - PDF download
2. Edit with subtitles
3. Upload to YouTube

**Deliverables**: Demo video

**Validation**: Video plays  
**Effort**: M

---

## Success Checklist

**Completed** ✅:
- [x] All unit tests passing (17/17 backend tests including curator)
- [x] Frontend UI complete with terminal aesthetic
- [x] WCAG 2.1 AAA compliant (13.24:1 contrast)
- [x] Backend API server running (http://localhost:8000)
- [x] Frontend dev server running (http://localhost:3000)
- [x] Production-quality error handling implemented
- [x] Custom exception system with user-friendly messages
- [x] Graceful degradation at all levels
- [x] Comprehensive logging strategy
- [x] README updated with testing section
- [x] Architecture review complete
- [x] Frontend connected to real API
- [x] E2E test with real API calls working
- [x] Curator Lambda logic complete and tested
- [x] Lambda wrapper for curator ready
- [x] CDK infrastructure code complete
- [x] CDK stacks synthesize successfully
- [x] Deployment scripts created
- [x] Deployment guide written

**Ready for AWS Deployment** ⏸️:
- [ ] AWS account setup with Bedrock access
- [ ] CDK bootstrap
- [ ] Deploy Storage stack
- [ ] Upload directory.json to S3
- [ ] Deploy API stack
- [ ] Deploy Curator stack
- [ ] Test all endpoints
- [ ] Update frontend API URL

**In Progress** 🔴:
- [ ] Result variation testing (different inputs → different outputs)

**Pending** ⏸️:
- [ ] Frontend deployed on Amplify
- [ ] API deployed to AWS (Lambda + API Gateway)
- [ ] Curator Lambda scheduled
- [ ] CloudWatch alarms active
- [ ] AWS Budgets configured
- [ ] Rate limiting verified
- [ ] `docker-compose up` starts all services
- [ ] Fresh clone works with just Docker
- [ ] Article drafted
- [ ] PDF links confirmed clickable in production

---

## Timeline Estimate

**Original Estimate**: 85-105 hours  
**Actual Progress**: ~60 hours (Phases 0-8A.5 complete)

**Remaining Work**:
- Phase 8C: API Deployment to AWS (4-6 hours)
- Phase 10: Frontend Deployment (8-12 hours)
- Phase 10.5: Docker Configuration (4-6 hours)
- Phase 11: Testing & QA (8-12 hours)
- Phase 12: Monitoring (4-6 hours)
- Phase 13: Documentation (6-8 hours)

**Total Remaining**: ~34-50 hours

**If Working 4 Hours/Day**:
- ✅ Week 1 (Feb 12-18): Phases 0-4 COMPLETE
- ✅ Week 2 (Feb 19-25): Phases 5-8B + Phase 7 COMPLETE (ahead of schedule!)
- 🔴 Week 3 (Feb 26-Mar 4): Phases 8C, 10, 10.5 (current)
- Week 4 (Mar 5-11): Phases 11-13
- **Launch**: March 12-13 (article published)

**Voting Period**: March 13-20

**Current Status**: Ahead of schedule! Backend complete, frontend integrated with real API, curator complete. Next: Deploy to AWS.

---

**Document Owner**: Technical Lead  
**Next Review**: After Phase 8B completion  
**Last Updated**: February 14, 2026