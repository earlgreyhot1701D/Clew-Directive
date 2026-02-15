# Phase 8C: Quick Start Guide

**Status**: ✅ Ready for AWS Deployment  
**Time Required**: 4-6 hours

---

## Prerequisites Checklist

- [ ] AWS account created
- [ ] AWS CLI installed: `aws --version`
- [ ] AWS credentials configured: `aws configure`
- [ ] Bedrock access enabled in AWS Console
  - Go to: AWS Console → Bedrock → Model access
  - Enable: Amazon Nova Micro, Anthropic Claude 4 Sonnet
- [ ] CDK CLI installed: `npm install -g aws-cdk`
- [ ] Verify: `cdk --version` (should be 2.170.0+)

---

## Deployment (Windows)

```powershell
# 1. Bootstrap CDK (first time only)
cd infrastructure
cdk bootstrap

# 2. Deploy all stacks
.\deploy.ps1 all

# 3. Upload directory.json
$accountId = (aws sts get-caller-identity --query Account --output text)
aws s3 cp ../data/directory.json s3://clew-directive-data-$accountId/data/directory.json

# 4. Get API URL
aws cloudformation describe-stacks --stack-name ClewDirective-Api --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text

# 5. Update frontend/.env.local
# NEXT_PUBLIC_API_URL=https://YOUR-API-URL/prod

# 6. Test API
curl -X POST https://YOUR-API-URL/prod/vibe-check `
  -H "Content-Type: application/json" `
  -d '{"vibe_check_responses":{"skepticism":"Curious","goal":"Understand AI","learning_style":"Reading","context":"Business"}}'
```

---

## Deployment (Linux/Mac)

```bash
# 1. Bootstrap CDK (first time only)
cd infrastructure
cdk bootstrap

# 2. Deploy all stacks
chmod +x deploy.sh
./deploy.sh all

# 3. Upload directory.json
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 cp ../data/directory.json s3://clew-directive-data-$ACCOUNT_ID/data/directory.json

# 4. Get API URL
aws cloudformation describe-stacks --stack-name ClewDirective-Api --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text

# 5. Update frontend/.env.local
# NEXT_PUBLIC_API_URL=https://YOUR-API-URL/prod

# 6. Test API
curl -X POST https://YOUR-API-URL/prod/vibe-check \
  -H "Content-Type: application/json" \
  -d '{"vibe_check_responses":{"skepticism":"Curious","goal":"Understand AI","learning_style":"Reading","context":"Business"}}'
```

---

## Troubleshooting

### "Unable to resolve AWS account"
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, Region (us-east-1)
```

### "Bedrock AccessDeniedException"
1. Go to AWS Console → Bedrock → Model access
2. Click "Manage model access"
3. Enable: Amazon Nova Micro, Anthropic Claude 4 Sonnet
4. Wait for approval (usually instant)

### "Module not found" in Lambda
- Ensure all `__init__.py` files exist in backend directories
- Check Lambda handler paths in CDK stacks

### CORS errors
- Update `infrastructure/lib/api-stack.ts` line 68
- Add your frontend domain to `allowOrigins`
- Redeploy: `cdk deploy ClewDirective-Api`

---

## Verification

After deployment, verify:

1. **Storage Stack**:
   ```bash
   aws s3 ls s3://clew-directive-data-{account-id}/data/
   # Should show directory.json
   ```

2. **API Stack**:
   ```bash
   # Test Vibe Check endpoint
   curl -X POST https://YOUR-API-URL/prod/vibe-check \
     -H "Content-Type: application/json" \
     -d '{"vibe_check_responses":{"skepticism":"Curious","goal":"Understand AI","learning_style":"Reading","context":"Business"}}'
   # Should return: {"profile": "You're approaching AI..."}
   ```

3. **Curator Stack**:
   ```bash
   # Manually invoke
   aws lambda invoke --function-name ClewDirective-Curator-CuratorFunction --payload '{}' response.json
   cat response.json
   # Should return: {"statusCode": 200, "resources_checked": 23, ...}
   ```

4. **Frontend**:
   ```bash
   cd frontend
   npm run dev
   # Navigate to http://localhost:3000
   # Complete Vibe Check → should call deployed API
   ```

---

## Cost Estimate

**During deployment**: $0 (all Free Tier)  
**During voting period** (500 briefings): ~$15-20  
**Ongoing** (50 briefings/month): ~$1-2/month

---

## Next Steps

After successful deployment:

1. ✅ Phase 8C complete
2. 🔴 Phase 10: Deploy frontend to Amplify
3. 🔴 Phase 10.5: Complete Docker configuration
4. 🔴 Phase 11: End-to-end testing
5. 🔴 Phase 12: Set up monitoring
6. 🔴 Phase 13: Write competition article

---

## Full Documentation

- **Complete Guide**: `PHASE_8C_API_DEPLOYMENT_GUIDE.md`
- **Completion Summary**: `PHASE_8C_API_DEPLOYMENT_COMPLETE.md`
- **Build Order**: `BUILD_ORDER.md`
- **Current Status**: `CURRENT_STATUS.md`

---

**Ready to deploy?** Run `.\deploy.ps1 all` (Windows) or `./deploy.sh all` (Linux/Mac)
