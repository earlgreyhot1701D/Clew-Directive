# Clew Directive - Next Steps

**Date**: February 15, 2026  
**Current Status**: 95% Complete - API Deployed, Frontend Ready  
**Target Launch**: March 12-13, 2026

---

## 🎯 IMMEDIATE PRIORITY (Next 1-2 Hours)

### 1. Deploy PDF Generator Fix 🔴 CRITICAL
**Why**: Complete the end-to-end user experience  
**Effort**: 15 minutes  
**Impact**: HIGH - Users can download their learning path

**Steps**:
```bash
cd infrastructure
cdk deploy ClewDirective-Api --require-approval never --force
```

**What This Does**:
- Updates Lambda functions with PDF generator fix
- Enables S3 upload to `tmp/briefings/` folder
- Returns presigned PDF URLs to users
- Completes the full user journey

**Validation**:
```powershell
# Test generate-briefing endpoint
$body = '{"approved_profile":"You want to learn AI fundamentals"}'
$result = Invoke-RestMethod -Uri "https://27o094toch.execute-api.us-east-1.amazonaws.com/prod/generate-briefing" -Method Post -Headers @{"Content-Type"="application/json"} -Body $body

# Should now have pdf_url (not null)
Write-Host "PDF URL: $($result.pdf_url)"
```

---

## 📋 HIGH PRIORITY (Next 1-2 Days)

### 2. Deploy Frontend to AWS Amplify 🔴 CRITICAL
**Why**: Make the app publicly accessible  
**Effort**: 2-4 hours  
**Impact**: HIGH - Required for competition submission

**Prerequisites**:
- GitHub repository (✅ done)
- AWS account (✅ done)

**Steps**:

#### Option A: CDK Deployment (Recommended)
```bash
cd infrastructure
cdk deploy ClewDirective-Frontend --require-approval never
```

#### Option B: AWS Console (If CDK fails)
1. Go to AWS Amplify Console
2. Click "New app" → "Host web app"
3. Connect to GitHub: `earlgreyhot1701D/Clew-Directive`
4. Branch: `main`
5. Build settings (auto-detected for Next.js):
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd frontend
           - npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: frontend/.next
       files:
         - '**/*'
     cache:
       paths:
         - frontend/node_modules/**/*
   ```
6. Environment variables:
   - `NEXT_PUBLIC_API_URL` = `https://27o094toch.execute-api.us-east-1.amazonaws.com/prod`
7. Click "Save and deploy"

**Validation**:
- Visit Amplify URL (e.g., `https://main.d1234567890.amplifyapp.com`)
- Complete full flow: Vibe Check → Profile → Briefing → PDF
- Test on mobile device
- Verify API calls work from public URL

**Estimated Time**: 30 min setup + 15 min build + 15 min testing = 1 hour

---

### 3. Deploy Curator Lambda 🟢 MEDIUM PRIORITY
**Why**: Automated weekly freshness checks for resources  
**Effort**: 30 minutes  
**Impact**: MEDIUM - Ensures resource quality over time

**Steps**:
```bash
cd infrastructure
cdk deploy ClewDirective-Curator --require-approval never
```

**What This Does**:
- Deploys Curator Lambda function
- Sets up EventBridge schedule (weekly, Sundays 2AM UTC)
- Enables automated URL verification
- Updates directory.json with freshness status

**Validation**:
```bash
# Manually invoke to test
aws lambda invoke --function-name ClewDirective-Curator-CuratorFunction... response.json
cat response.json
```

---

## 🧪 TESTING & QA (Next 2-3 Days)

### 4. End-to-End Testing 🔴 CRITICAL
**Why**: Ensure everything works in production  
**Effort**: 2-3 hours  
**Impact**: HIGH - Catch bugs before launch

**Test Scenarios**:

#### Happy Path
1. **New User Flow**:
   - Complete Vibe Check with realistic answers
   - Review profile (should be personalized)
   - Click "That's Me"
   - Wait for briefing generation (30-45 seconds)
   - Verify 4-6 resources returned
   - Download PDF
   - Open PDF, verify clickable links

2. **Refinement Flow**:
   - Complete Vibe Check
   - Click "Not Quite"
   - Provide correction: "I prefer hands-on learning"
   - Verify refined profile incorporates feedback
   - Continue to briefing

3. **Different User Profiles**:
   - Test with skeptical learner
   - Test with enthusiastic builder
   - Test with business professional
   - Verify different resources recommended

#### Error Scenarios
4. **Invalid Input**:
   - Submit empty Vibe Check responses
   - Verify error message is user-friendly
   - Verify retry is allowed

5. **Network Issues**:
   - Disable internet mid-request
   - Verify timeout handling
   - Verify retry logic works

6. **Edge Cases**:
   - Very long user corrections (200+ chars)
   - Special characters in responses
   - Multiple rapid submissions

**Documentation**: Create test report with screenshots

---

### 5. Accessibility Testing 🔴 CRITICAL
**Why**: WCAG 2.1 AA compliance is a requirement  
**Effort**: 2 hours  
**Impact**: HIGH - Competition judges will check

**Tools**:
- axe DevTools (Chrome extension)
- NVDA screen reader (Windows)
- Keyboard-only navigation

**Tests**:
1. **Automated Scan**:
   ```bash
   npm install -g @axe-core/cli
   axe https://your-amplify-url.amplifyapp.com --tags wcag2a,wcag2aa
   ```
   - Target: Zero violations

2. **Screen Reader Test** (NVDA):
   - Navigate Vibe Check with screen reader only
   - Verify all questions are announced
   - Verify progress is communicated
   - Verify buttons have clear labels

3. **Keyboard Navigation**:
   - Tab through entire flow
   - Verify focus indicators visible
   - Verify no keyboard traps
   - Verify logical tab order

4. **Text Resize**:
   - Zoom to 200% in browser
   - Verify no text overlap
   - Verify all content still accessible

**Documentation**: Screenshot axe report showing zero violations

---

## 🔧 INFRASTRUCTURE & MONITORING (Next 3-4 Days)

### 6. Set Up CloudWatch Alarms 🟢 MEDIUM PRIORITY
**Why**: Get notified of issues before users complain  
**Effort**: 1 hour  
**Impact**: MEDIUM - Production monitoring

**Alarms to Create**:
1. **Bedrock Cost Alarm**:
   - Threshold: $50/day
   - Action: Email notification

2. **API Gateway 5xx Errors**:
   - Threshold: >5% error rate
   - Action: Email notification

3. **Lambda Errors**:
   - Threshold: >10 errors/hour
   - Action: Email notification

**Steps**:
```bash
# Add to infrastructure/lib/monitoring-stack.ts (create if needed)
# Then deploy
cdk deploy ClewDirective-Monitoring
```

---

### 7. Configure AWS Budgets 🟢 LOW PRIORITY
**Why**: Prevent surprise bills  
**Effort**: 15 minutes  
**Impact**: LOW - Safety net

**Steps**:
1. Go to AWS Budgets Console
2. Create budget:
   - Type: Cost budget
   - Amount: $200
   - Period: Monthly
3. Set alerts:
   - 50% ($100) - Email warning
   - 75% ($150) - Email warning
   - 90% ($180) - Email alert
   - 100% ($200) - Email alert

---

### 8. Verify Rate Limiting 🟢 LOW PRIORITY
**Why**: Ensure cost controls work  
**Effort**: 30 minutes  
**Impact**: LOW - Already configured in CDK

**Test**:
```bash
# Install Artillery
npm install -g artillery

# Create test script (test-load.yml)
config:
  target: "https://27o094toch.execute-api.us-east-1.amazonaws.com/prod"
  phases:
    - duration: 60
      arrivalRate: 20
scenarios:
  - flow:
      - post:
          url: "/vibe-check"
          json:
            vibe_check_responses:
              skepticism: "test"
              goal: "test"
              learning_style: "test"
              context: "test"

# Run test
artillery run test-load.yml
```

**Expected**: 429 responses after 10 req/sec threshold

---

## 📝 DOCUMENTATION & LAUNCH PREP (Next 4-5 Days)

### 9. Update README 🔴 CRITICAL
**Why**: First impression for judges and users  
**Effort**: 2 hours  
**Impact**: HIGH - Required for competition

**Sections to Add**:
1. **Project Overview**:
   - What is Clew Directive?
   - Problem it solves
   - Key features

2. **Live Demo**:
   - Link to Amplify URL
   - Screenshots of UI

3. **Architecture**:
   - System diagram
   - Tech stack
   - AWS services used

4. **Local Development**:
   - Prerequisites
   - Setup instructions
   - Running tests

5. **Deployment**:
   - AWS requirements
   - CDK deployment steps
   - Environment variables

6. **Competition Info**:
   - AWS 10,000 AIdeas
   - Social Impact Category
   - Team Docket 1701D

7. **License**: MIT or Apache 2.0

---

### 10. Write Competition Article 🔴 CRITICAL
**Why**: Required for competition submission  
**Effort**: 4-6 hours  
**Impact**: HIGH - Judges read this

**Outline** (1500-2000 words):

1. **Hook** (200 words):
   - "AI learning is overwhelming. 100,000+ resources, most low-quality or paywalled."
   - Personal story: Why we built this

2. **The Problem** (300 words):
   - Choice paralysis
   - Hype vs. reality
   - Cost barriers
   - One-size-fits-all approaches

3. **Our Solution** (400 words):
   - Clew Directive: Personalized, curated, free
   - How it works: Vibe Check → Scout → Navigator → Curator
   - Stateless by design (privacy)
   - 5-gate quality standard

4. **Technical Highlights** (400 words):
   - Serverless architecture (<$1 per briefing)
   - AI agents (Claude Sonnet 4.5 + Nova Micro)
   - WCAG 2.1 AA compliant
   - Automated freshness checks
   - Cost controls (rate limiting, budgets)

5. **Impact** (300 words):
   - Democratizing AI education
   - Removing cost barriers
   - Respecting privacy
   - Designed for expansion (multi-domain future)

6. **Call to Action** (100 words):
   - Try it: [Amplify URL]
   - Vote for us: [Competition link]
   - Open source: [GitHub link]

**Include**:
- 3-4 screenshots
- Architecture diagram
- Test results showing personalization

---

### 11. Create Demo Video (Optional) 🟢 LOW PRIORITY
**Why**: Engaging way to show the product  
**Effort**: 2-3 hours  
**Impact**: MEDIUM - Nice to have

**Script** (2-3 minutes):
1. **Intro** (15 sec):
   - "Meet Clew Directive - your AI learning navigator"

2. **Problem** (30 sec):
   - Show overwhelming Google search results
   - "Where do you even start?"

3. **Solution** (90 sec):
   - Walk through Vibe Check
   - Show profile generation
   - Show personalized learning path
   - Download PDF

4. **Outro** (15 sec):
   - "Free, private, personalized. Try it today."
   - Show URL

**Tools**: OBS Studio (free), DaVinci Resolve (free)

---

## 🚀 LAUNCH CHECKLIST (March 12-13)

### Pre-Launch (Day Before)
- [ ] All endpoints tested and working
- [ ] Frontend deployed to Amplify
- [ ] PDF generation working
- [ ] Accessibility tested (zero violations)
- [ ] README complete
- [ ] Article drafted and reviewed
- [ ] Demo video uploaded (optional)
- [ ] CloudWatch alarms active
- [ ] AWS Budgets configured

### Launch Day
- [ ] Submit article to competition
- [ ] Share on social media (LinkedIn, Twitter)
- [ ] Post in relevant communities (r/artificial, r/learnmachinelearning)
- [ ] Email friends/colleagues to try it
- [ ] Monitor CloudWatch for errors
- [ ] Respond to feedback

### During Voting Period (March 13-20)
- [ ] Monitor usage metrics
- [ ] Fix any critical bugs immediately
- [ ] Respond to user feedback
- [ ] Share updates on social media
- [ ] Encourage people to vote

---

## 📊 TIMELINE

**Week 4 (Feb 26 - Mar 4)**: Current Week
- ✅ Phase 8C deployed
- ⏳ PDF fix deployment (1 hour)
- ⏳ Frontend to Amplify (4 hours)
- ⏳ Curator deployment (1 hour)
- ⏳ E2E testing (3 hours)

**Week 5 (Mar 5-11)**: Final Push
- Accessibility testing (2 hours)
- CloudWatch alarms (1 hour)
- README update (2 hours)
- Article writing (6 hours)
- Demo video (3 hours, optional)
- Final testing (2 hours)

**Week 6 (Mar 12-13)**: Launch
- Article submission
- Social media promotion
- Monitor and respond

**Week 7 (Mar 13-20)**: Voting Period
- Daily monitoring
- Bug fixes as needed
- Community engagement

---

## 🎯 SUCCESS METRICS

**Technical**:
- [ ] All 3 endpoints: 200 OK
- [ ] PDF generation: Working
- [ ] Response time: <5 sec (vibe check), <45 sec (briefing)
- [ ] Error rate: <1%
- [ ] Accessibility: Zero axe violations
- [ ] Test coverage: >85%

**User Experience**:
- [ ] 500+ briefings generated during voting period
- [ ] <5% refinement rate (profiles accurate first try)
- [ ] >60% PDF download rate
- [ ] Positive user feedback

**Cost**:
- [ ] <$30 total during voting period
- [ ] <$1 per briefing average
- [ ] No budget overruns

---

## 🚨 RISK MITIGATION

**Risk 1: Bedrock Throttling**
- **Mitigation**: Rate limiting at API Gateway (10 req/sec)
- **Backup**: Increase limits if needed (costs more)

**Risk 2: High Traffic Costs**
- **Mitigation**: AWS Budgets + CloudWatch alarms
- **Backup**: Temporarily disable service if budget exceeded

**Risk 3: PDF Generation Failures**
- **Mitigation**: Graceful degradation (show path without PDF)
- **Status**: Already implemented ✅

**Risk 4: Accessibility Issues**
- **Mitigation**: Test with axe + NVDA before launch
- **Status**: UI already WCAG AAA compliant ✅

---

## 📞 NEED HELP?

**Stuck on deployment?**
- Check `SUCCESS_SUMMARY.md` for deployment details
- Check `PHASE_8C_API_DEPLOYMENT_GUIDE.md` for AWS setup
- Review CloudWatch logs for errors

**Questions about architecture?**
- See `.kiro/steering/tech.md` for technical decisions
- See `ARCHITECTURE_REVIEW.md` for system design

**Competition questions?**
- See `REQUIREMENTS.md` for original requirements
- See `.kiro/steering/product.md` for product vision

---

**Last Updated**: February 15, 2026  
**Status**: Ready for final push! 🚀
