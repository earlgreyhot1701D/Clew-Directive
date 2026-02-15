# Phase 8C: API Deployment to AWS — Complete Guide

**Date**: February 14, 2026  
**Status**: Ready for Deployment  
**Estimated Time**: 4-6 hours

---

## Overview

Deploy the Clew Directive API to AWS using CDK. This includes:
- 3 Lambda functions (Vibe Check, Refine Profile, Generate Briefing)
- API Gateway with rate limiting
- S3 bucket for directory.json and PDFs
- Curator Lambda with weekly EventBridge schedule
- IAM roles with least-privilege permissions

---

## Prerequisites

### 1. AWS Account Setup
- [ ] AWS account created
- [ ] AWS CLI installed and configured
- [ ] AWS credentials configured (`aws configure`)
- [ ] Bedrock access enabled in us-east-1 region
  - Models needed: `amazon.nova-micro-v1:0`, `anthropic.claude-sonnet-4-20250514-v1:0`

### 2. Local Environment
- [ ] Node.js 20+ installed
- [ ] Python 3.12+ installed
- [ ] AWS CDK CLI installed: `npm install -g aws-cdk`
- [ ] All backend dependencies installed: `cd backend && pip install -r requirements.txt`
- [ ] All infrastructure dependencies installed: `cd infrastructure && npm install`

### 3. Verification
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Verify CDK version
cdk --version

# Verify Python version
python --version

# Verify backend tests pass
cd backend && pytest tests/ -v
```

---

## Deployment Steps

### Step 1: Bootstrap CDK (First Time Only)

If this is your first time using CDK in this AWS account/region:

```bash
cd infrastructure
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

Replace `ACCOUNT-ID` with your AWS account ID (from `aws sts get-caller-identity`).

**What this does**: Creates an S3 bucket and IAM roles for CDK deployments.

---

### Step 2: Review and Customize Configuration

#### 2.1: Lambda Container Image Architecture (Already Configured)

The CDK stack now uses **Docker container images** for Lambda deployment:

```typescript
// Shared Lambda configuration using Docker container images
const commonLambdaProps = {
  code: lambda.Code.fromAssetImage('../backend', {
    file: 'Dockerfile.lambda',
  }),
  memorySize: 512,
  environment: {
    CD_ENVIRONMENT: 'prod',
    // ...
  },
};

// Lambda functions use the container image
const vibeCheckFn = new lambda.Function(this, 'VibeCheckFunction', {
  ...commonLambdaProps,
  handler: lambda.Handler.FROM_IMAGE,
  functionName: 'ClewDirective-Api-VibeCheckFunction',
  // ...
});
```

**What this does**:
- Builds a Docker container image from `backend/Dockerfile.lambda`
- Container includes Python 3.12 runtime + all dependencies + application code
- Same container image used for all 3 Lambda functions (different CMD/handlers)
- Pushed to Amazon ECR (Elastic Container Registry) during deployment

**Benefits**:
- ✅ No size constraints: Container images support up to 10GB (vs 250MB for ZIP)
- ✅ Simplified deployment: Single artifact contains everything
- ✅ Better for complex dependencies: WeasyPrint system libraries included
- ✅ Consistent environments: Same container runs locally and in Lambda
- ✅ Docker layer caching: Faster rebuilds when only code changes
- ✅ Cross-platform builds: Works consistently across Windows/Mac/Linux

#### 2.2: Update API Stack CORS Origins

Edit `infrastructure/lib/api-stack.ts`:

```typescript
// Line 68: Update CORS origins for production
defaultCorsPreflightOptions: {
  allowOrigins: ['https://your-amplify-domain.amplifyapp.com'], // Update after Amplify deployment
  allowMethods: ['POST', 'OPTIONS'],
  allowHeaders: ['Content-Type'],
},
```

**For now**: Leave as `apigateway.Cors.ALL_ORIGINS` for testing, update after frontend deployment.

#### 2.3: Update Bedrock Model ARNs (Optional)

Edit `infrastructure/lib/api-stack.ts` and `infrastructure/lib/curator-stack.ts`:

```typescript
// Replace line 59 in api-stack.ts:
resources: ['*'], // TODO: Scope to specific model ARNs

// With:
resources: [
  'arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0',
  'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0',
],
```

**For now**: Leave as `*` for simplicity, tighten in production.

---

### Step 3: Build and Synthesize CloudFormation Templates

```bash
cd infrastructure
npm run build
npm run synth
```

**Expected output**: 
```
Successfully synthesized to infrastructure/cdk.out
Supply a stack id to display its template.
```

**What this does**: 
- Compiles TypeScript CDK code
- Generates CloudFormation templates
- **Triggers Docker build** for Lambda container image (from `backend/Dockerfile.lambda`)

**Note**: First synthesis may take 5-10 minutes as Docker builds the container image with all dependencies. Subsequent builds are faster:
- **Code-only changes**: Docker layer caching speeds up builds (~2-3 minutes)
- **Dependency changes**: Full rebuild required (~5-10 minutes)

**Lambda Container Image Architecture**:
- Single container image contains runtime + dependencies + application code
- Built from `backend/Dockerfile.lambda`
- Pushed to Amazon ECR during deployment
- Same image used for all 3 Lambda functions (different handlers via CMD)
- Supports up to 10GB (vs 250MB for ZIP deployment)

---

### Step 4: Deploy Storage Stack

```bash
cdk deploy ClewDirective-Storage
```

**What this creates**:
- S3 bucket: `clew-directive-data-{account-id}`
- Versioning enabled
- Lifecycle rule: Delete PDFs in `tmp/briefings/` after 1 day
- Block all public access

**Expected time**: 2-3 minutes

**Output**: Note the bucket name from the CloudFormation outputs.

---

### Step 5: Upload directory.json to S3

```bash
# From project root
aws s3 cp data/directory.json s3://clew-directive-data-{account-id}/data/directory.json
```

**Verify**:
```bash
aws s3 ls s3://clew-directive-data-{account-id}/data/
```

**Expected output**: `directory.json` listed with size ~50KB.

---

### Step 6: Deploy API Stack

```bash
cd infrastructure
cdk deploy ClewDirective-Api
```

**What this creates**:
- 3 Lambda functions:
  - `ClewDirective-Api-VibeCheckFunction`
  - `ClewDirective-Api-RefineProfileFunction`
  - `ClewDirective-Api-GenerateBriefingFunction`
- API Gateway: `Clew Directive API`
- IAM roles with Bedrock and S3 permissions
- Rate limiting: 10 req/sec, burst 20

**Note**: Lambda functions use automatic scaling (no reserved concurrency) to avoid issues in new AWS accounts. Functions will scale up to your account's concurrent execution limit.

**Expected time**: 5-7 minutes

**Output**: Note the `ApiUrl` from CloudFormation outputs (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/prod/`).

---

### Step 7: Test API Endpoints

#### 7.1: Test Vibe Check

```bash
curl -X POST https://YOUR-API-URL/prod/vibe-check \
  -H "Content-Type: application/json" \
  -d '{
    "vibe_check_responses": {
      "skepticism": "Curious but haven'\''t started",
      "goal": "Understand what AI is",
      "learning_style": "Reading at own pace",
      "context": "Business"
    }
  }'
```

**Expected response**:
```json
{
  "profile": "You're approaching AI with curiosity..."
}
```

#### 7.2: Test Refine Profile

```bash
curl -X POST https://YOUR-API-URL/prod/refine-profile \
  -H "Content-Type: application/json" \
  -d '{
    "original_profile": "You'\''re approaching AI with curiosity...",
    "user_correction": "Actually I prefer hands-on learning"
  }'
```

**Expected response**:
```json
{
  "profile": "You're approaching AI with hands-on curiosity..."
}
```

#### 7.3: Test Generate Briefing

```bash
curl -X POST https://YOUR-API-URL/prod/generate-briefing \
  -H "Content-Type: application/json" \
  -d '{
    "approved_profile": "You'\''re approaching AI with curiosity..."
  }'
```

**Expected response**:
```json
{
  "learning_path": [...],
  "total_hours": 45,
  "next_steps": "...",
  "pdf_url": "https://..."
}
```

**Note**: This endpoint takes 30-60 seconds to complete.

---

### Step 8: Deploy Curator Stack

```bash
cd infrastructure
cdk deploy ClewDirective-Curator
```

**What this creates**:
- Lambda function: `ClewDirective-Curator-CuratorFunction`
- EventBridge rule: Runs every Sunday at 2:00 AM UTC
- IAM role with S3 read/write and Bedrock access

**Expected time**: 3-4 minutes

---

### Step 9: Test Curator Lambda (Manual Invocation)

```bash
aws lambda invoke \
  --function-name ClewDirective-Curator-CuratorFunction \
  --payload '{}' \
  response.json

cat response.json
```

**Expected response**:
```json
{
  "statusCode": 200,
  "resources_checked": 23,
  "resources_failed": 0,
  "resources_updated": 23
}
```

**Check CloudWatch Logs**:
```bash
aws logs tail /aws/lambda/ClewDirective-Curator-CuratorFunction --follow
```

---

### Step 10: Update Frontend API URL

Edit `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://YOUR-API-URL/prod
```

**Restart frontend dev server**:
```bash
cd frontend
npm run dev
```

**Test complete flow**:
1. Navigate to http://localhost:3000
2. Complete Vibe Check
3. Approve profile
4. Generate briefing
5. Download PDF

---

## Verification Checklist

- [ ] Storage stack deployed successfully
- [ ] directory.json uploaded to S3
- [ ] API stack deployed successfully
- [ ] All 3 API endpoints respond correctly
- [ ] Curator stack deployed successfully
- [ ] Curator Lambda runs without errors
- [ ] Frontend connects to deployed API
- [ ] Complete flow works end-to-end
- [ ] CloudWatch logs show no errors
- [ ] Rate limiting works (test with >10 req/sec)

---

## Cost Monitoring

### CloudWatch Dashboard

Create a dashboard to monitor costs:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ClewDirective \
  --dashboard-body file://cloudwatch-dashboard.json
```

**Metrics to track**:
- Lambda invocations (count)
- Lambda duration (milliseconds)
- API Gateway requests (count)
- API Gateway 4xx/5xx errors (count)
- Bedrock token usage (estimated cost)

### AWS Budgets

Create a budget alert:

```bash
aws budgets create-budget \
  --account-id YOUR-ACCOUNT-ID \
  --budget file://budget.json
```

**Budget configuration**:
- Total: $200
- Alerts at 50%, 75%, 90%
- Email notifications

---

## Troubleshooting

### Issue: CDK Bootstrap Fails

**Error**: `Unable to resolve AWS account to use`

**Solution**:
```bash
aws configure
# Enter your AWS credentials
cdk bootstrap --profile default
```

---

### Issue: Lambda Function Fails with "Module not found"

**Error**: `Unable to import module 'backend.agents.orchestrator'`

**Solution**: Ensure `backend/` directory structure is correct:
```
backend/
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   └── ...
├── lambda_vibe_check.py
└── requirements.txt
```

All `__init__.py` files must exist for Python imports to work.

---

### Issue: Bedrock Access Denied

**Error**: `AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel`

**Solution**:
1. Go to AWS Console → Bedrock → Model access
2. Request access to:
   - Amazon Nova Micro
   - Anthropic Claude 4 Sonnet
3. Wait for approval (usually instant)

---

### Issue: API Gateway CORS Error

**Error**: `Access to fetch at 'https://...' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solution**: Update `infrastructure/lib/api-stack.ts`:
```typescript
defaultCorsPreflightOptions: {
  allowOrigins: ['http://localhost:3000', 'https://your-amplify-domain.amplifyapp.com'],
  allowMethods: ['POST', 'OPTIONS'],
  allowHeaders: ['Content-Type'],
},
```

Redeploy: `cdk deploy ClewDirective-Api`

---

### Issue: PDF Generation Fails in Lambda

**Error**: `OSError: cannot load library 'gobject-2.0-0'`

**Solution**: WeasyPrint requires system libraries. Add Lambda layer:

```typescript
// In api-stack.ts
const pdfLayer = lambda.LayerVersion.fromLayerVersionArn(
  this,
  'WeasyPrintLayer',
  'arn:aws:lambda:us-east-1:123456789012:layer:weasyprint:1'
);

generateBriefingFn.addLayers(pdfLayer);
```

**Alternative**: Use Docker-based Lambda deployment (see AWS docs).

---

## Rollback Procedure

If deployment fails or causes issues:

```bash
# Rollback API stack
cdk destroy ClewDirective-Api

# Rollback Curator stack
cdk destroy ClewDirective-Curator

# Rollback Storage stack (WARNING: Deletes S3 bucket)
cdk destroy ClewDirective-Storage
```

**Note**: Storage stack has `removalPolicy: RETAIN`, so S3 bucket won't be deleted automatically.

---

## Next Steps

After successful deployment:

1. **Phase 10**: Deploy frontend to Amplify
2. **Phase 10.5**: Complete Docker configuration
3. **Phase 11**: End-to-end testing
4. **Phase 12**: Set up monitoring and alerts
5. **Phase 13**: Write competition article

---

## Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/)
- [API Gateway](https://docs.aws.amazon.com/apigateway/)

---

**Document Owner**: DevOps / Technical Lead  
**Status**: Ready for Deployment  
**Last Updated**: February 14, 2026
