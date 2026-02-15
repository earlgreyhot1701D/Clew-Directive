# Lambda Container Image Deployment Status

**Date**: February 15, 2026  
**Task**: Convert Lambda deployment from ZIP to Docker container images

## Problem
ZIP-based Lambda deployment failed because dependencies (Strands SDK + WeasyPrint) exceeded 250MB unzipped limit (~375MB actual size).

## Solution Implemented
Converted to Lambda container images (supports up to 10GB).

## Changes Made

### 1. Created Dockerfile for Lambda
- **File**: `backend/Dockerfile.lambda`
- Uses AWS Lambda Python 3.12 base image
- Installs dependencies without `--target` flag (installs to default Python path)
- Copies application code to `/var/task/`

### 2. Fixed Import Paths
All backend files updated to remove `backend.` prefix from imports since code is copied directly to `/var/task/`:
- `backend/lambda_vibe_check.py`
- `backend/lambda_refine_profile.py`
- `backend/lambda_generate_briefing.py`
- `backend/agents/orchestrator.py`
- `backend/agents/navigator.py`
- `backend/agents/scout.py`
- `backend/curator/freshness_check.py`
- `backend/tools/directory_loader.py`

### 3. Fixed Agent Initialization
Updated all three Lambda handlers to properly initialize agents with required dependencies:
```python
# Load directory data
directory_data = load_directory()
knowledge = create_knowledge(directory_data)

# Initialize agents with dependencies
scout = ScoutAgent(knowledge=knowledge)
navigator = NavigatorAgent()
orchestrator = Orchestrator(scout=scout, navigator=navigator)
```

### 4. Updated CDK Stack
- **File**: `infrastructure/lib/api-stack.ts`
- Changed from `lambda.Function` to `lambda.DockerImageFunction`
- Uses `DockerImageCode.fromImageAsset()` to build and push images to ECR
- Removed reserved concurrency (not needed for new AWS accounts)

## Deployment Status

### Successfully Deployed
✅ Docker images built and pushed to ECR  
✅ Lambda functions created with container images  
✅ API Gateway endpoints configured  
✅ IAM permissions set up (Bedrock, S3)

### Current Issue
⚠️ CDK not detecting code changes after initial deployment

**Problem**: CDK caches Docker image hashes. After fixing the agent initialization code, running `cdk deploy` shows "no changes" even though the Python files have been updated.

**Attempted Solutions**:
1. ✅ Removed `cdk.out` directory - didn't help
2. ✅ Updated Dockerfile comments to change hash - didn't help  
3. ✅ Ran `docker system prune -af` to clear cache - didn't help
4. ✅ Touched Python files to update timestamps - didn't help

**Root Cause**: CDK uses a hash of the entire `backend/` directory contents. The hash calculation might be cached or the changes aren't being detected properly.

## Next Steps

### Option 1: Force Rebuild (Recommended)
Delete the CloudFormation stack and redeploy from scratch:
```bash
cd infrastructure
cdk destroy ClewDirective-Api
cdk deploy ClewDirective-Api --require-approval never
```

### Option 2: Manual Lambda Update
Update the Lambda function code directly using AWS CLI after building the Docker image locally.

### Option 3: Change CDK Asset Path
Modify the CDK stack to use a different asset path or add a build argument to force a new hash.

## Testing Checklist

Once redeployed with latest code:
- [ ] Test `/vibe-check` endpoint with valid payload
- [ ] Verify Scout agent loads directory.json from S3
- [ ] Verify Navigator agent can synthesize profiles
- [ ] Test `/refine-profile` endpoint
- [ ] Test `/generate-briefing` endpoint
- [ ] Check CloudWatch logs for errors
- [ ] Verify Bedrock API calls work
- [ ] Test PDF generation (will need WeasyPrint system libraries)

## Known Issues to Address

### 1. WeasyPrint System Libraries
WeasyPrint requires system libraries (libpango, libcairo, etc.) that aren't in the base Lambda image.

**Solution**: Update Dockerfile to install required system packages:
```dockerfile
RUN yum install -y \
    pango \
    cairo \
    gdk-pixbuf2 \
    libffi \
    && yum clean all
```

### 2. Environment Variables
Lambda functions need these environment variables set:
- `CD_ENVIRONMENT=prod`
- `CD_S3_BUCKET=clew-directive-data-831889733571`
- `CD_DIRECTORY_KEY=directory.json`

Already configured in CDK stack ✅

### 3. Bedrock Model Access
Ensure Bedrock models are enabled in the AWS account:
- Nova Micro (for Scout)
- Claude 4 Sonnet (for Navigator)

Models auto-enable on first use ✅

## API Endpoints

- **Base URL**: `https://inpf5v2xh1.execute-api.us-east-1.amazonaws.com/prod/`
- **Vibe Check**: `POST /vibe-check`
- **Refine Profile**: `POST /refine-profile`
- **Generate Briefing**: `POST /generate-briefing`

## Resources

- **S3 Bucket**: `clew-directive-data-831889733571`
- **AWS Account**: `831889733571`
- **Region**: `us-east-1`
- **Lambda Functions**:
  - `ClewDirective-Api-VibeCheckFunction3620F876-EdgwmHeucBhk`
  - `ClewDirective-Api-RefineProfileFunction2A81E4B5-*`
  - `ClewDirective-Api-GenerateBriefingFunctionA362FC43-*`

## Summary

We've successfully converted the Lambda deployment to use Docker container images, which solves the 250MB ZIP size limit. All import paths have been fixed and agent initialization code has been updated. The main blocker is getting CDK to detect and deploy the latest code changes. Once we force a rebuild (Option 1 above), we should be able to test the full API flow.
