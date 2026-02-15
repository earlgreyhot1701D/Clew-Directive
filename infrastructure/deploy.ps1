# Clew Directive — CDK Deployment Script (PowerShell)
# Usage: .\deploy.ps1 [stack-name]
# Example: .\deploy.ps1 ClewDirective-Api
# Or: .\deploy.ps1 all (deploys all stacks)

param(
    [string]$StackName = "all"
)

$ErrorActionPreference = "Stop"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Clew Directive — CDK Deployment" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Check AWS credentials
Write-Host "🔍 Verifying AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "AWS credentials not configured"
    }
} catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

$accountId = (aws sts get-caller-identity --query Account --output text)
$region = (aws configure get region)
if (-not $region) {
    $region = "us-east-1"
}

Write-Host "✅ AWS Account: $accountId" -ForegroundColor Green
Write-Host "✅ Region: $region" -ForegroundColor Green
Write-Host ""

# Build TypeScript
Write-Host "🔨 Building TypeScript..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Build complete" -ForegroundColor Green
Write-Host ""

# Synthesize CloudFormation
Write-Host "🔨 Synthesizing CloudFormation templates..." -ForegroundColor Yellow
npm run synth | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Synth failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Synth complete" -ForegroundColor Green
Write-Host ""

# Deploy based on argument
if ($StackName -eq "all") {
    Write-Host "🚀 Deploying all stacks..." -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "📦 Deploying Storage Stack..." -ForegroundColor Cyan
    cdk deploy ClewDirective-Storage --require-approval never
    Write-Host ""
    
    Write-Host "📦 Deploying API Stack..." -ForegroundColor Cyan
    cdk deploy ClewDirective-Api --require-approval never
    Write-Host ""
    
    Write-Host "📦 Deploying Curator Stack..." -ForegroundColor Cyan
    cdk deploy ClewDirective-Curator --require-approval never
    Write-Host ""
    
    Write-Host "✅ All stacks deployed successfully!" -ForegroundColor Green
} else {
    Write-Host "🚀 Deploying $StackName..." -ForegroundColor Yellow
    cdk deploy $StackName --require-approval never
    Write-Host ""
    Write-Host "✅ $StackName deployed successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Upload directory.json to S3:" -ForegroundColor Yellow
Write-Host "   aws s3 cp ../data/directory.json s3://clew-directive-data-$accountId/data/directory.json" -ForegroundColor White
Write-Host ""
Write-Host "2. Get API URL:" -ForegroundColor Yellow
Write-Host "   aws cloudformation describe-stacks --stack-name ClewDirective-Api --query 'Stacks[0].Outputs[?OutputKey==``ApiUrl``].OutputValue' --output text" -ForegroundColor White
Write-Host ""
Write-Host "3. Test API endpoints (see PHASE_8C_API_DEPLOYMENT_GUIDE.md)" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Update frontend/.env.local with API URL" -ForegroundColor Yellow
Write-Host ""
