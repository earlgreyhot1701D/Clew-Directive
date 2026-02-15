#!/bin/bash
# Clew Directive — CDK Deployment Script
# Usage: ./deploy.sh [stack-name]
# Example: ./deploy.sh ClewDirective-Api
# Or: ./deploy.sh all (deploys all stacks)

set -e  # Exit on error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Clew Directive — CDK Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check AWS credentials
echo "🔍 Verifying AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-east-1")

echo "✅ AWS Account: $ACCOUNT_ID"
echo "✅ Region: $REGION"
echo ""

# Build TypeScript
echo "🔨 Building TypeScript..."
npm run build
echo "✅ Build complete"
echo ""

# Synthesize CloudFormation
echo "🔨 Synthesizing CloudFormation templates..."
npm run synth > /dev/null
echo "✅ Synth complete"
echo ""

# Deploy based on argument
STACK_NAME=${1:-all}

if [ "$STACK_NAME" = "all" ]; then
    echo "🚀 Deploying all stacks..."
    echo ""
    
    echo "📦 Deploying Storage Stack..."
    cdk deploy ClewDirective-Storage --require-approval never
    echo ""
    
    echo "📦 Deploying API Stack..."
    cdk deploy ClewDirective-Api --require-approval never
    echo ""
    
    echo "📦 Deploying Curator Stack..."
    cdk deploy ClewDirective-Curator --require-approval never
    echo ""
    
    echo "✅ All stacks deployed successfully!"
else
    echo "🚀 Deploying $STACK_NAME..."
    cdk deploy $STACK_NAME --require-approval never
    echo ""
    echo "✅ $STACK_NAME deployed successfully!"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Upload directory.json to S3:"
echo "   aws s3 cp ../data/directory.json s3://clew-directive-data-$ACCOUNT_ID/data/directory.json"
echo ""
echo "2. Get API URL:"
echo "   aws cloudformation describe-stacks --stack-name ClewDirective-Api --query 'Stacks[0].Outputs[?OutputKey==\`ApiUrl\`].OutputValue' --output text"
echo ""
echo "3. Test API endpoints (see PHASE_8C_API_DEPLOYMENT_GUIDE.md)"
echo ""
echo "4. Update frontend/.env.local with API URL"
echo ""
