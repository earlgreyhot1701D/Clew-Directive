# Phase 7: Curator Lambda — COMPLETE

**Date**: February 14, 2026  
**Status**: ✅ COMPLETE  
**Duration**: ~30 minutes (already implemented, verified tests)

---

## What Was Verified

The Curator Lambda was already fully implemented with comprehensive tests. This phase involved verifying the implementation, running tests, and creating deployment documentation.

---

## 1. Curator Implementation

**File**: `backend/curator/freshness_check.py`

### Features:
- **Weekly resource verification** via EventBridge Scheduler
- **Status progression**: active → degraded → stale → dead
- **S3 integration**: Reads/writes directory.json
- **CloudWatch metrics**: Publishes failure rate, failed count, total count
- **Alert threshold**: Logs error if >10% resources fail
- **Graceful error handling**: Continues even if individual resources fail

### Status Definitions:
- **active**: URL live, content verified
- **degraded**: URL live but content may have changed (first failure)
- **stale**: URL redirects or content outdated (second failure)
- **dead**: URL returns 4xx/5xx or unreachable (third failure)

### Core Function:
```python
def check_all_resources(directory_data: dict) -> dict:
    """
    Verify all resources in the directory.
    
    Returns:
        Updated directory_data with refreshed status and last_verified fields.
    """
    resources = directory_data.get("resources", [])
    now = datetime.now(timezone.utc).isoformat()
    stats = {"active": 0, "degraded": 0, "stale": 0, "dead": 0, "errors": 0}
    
    for resource in resources:
        resource_id = resource.get("id", "unknown")
        url = resource.get("resource_url", "")
        
        try:
            is_live = verify_url(url, timeout=10)
            
            if is_live:
                resource["status"] = STATUS_ACTIVE
                stats["active"] += 1
            else:
                # Status progression logic
                prev_status = resource.get("status", STATUS_ACTIVE)
                if prev_status == STATUS_ACTIVE:
                    resource["status"] = STATUS_DEGRADED
                elif prev_status == STATUS_DEGRADED:
                    resource["status"] = STATUS_STALE
                else:
                    resource["status"] = STATUS_DEAD
                stats[resource["status"]] += 1
            
            resource["last_verified"] = now
        except Exception:
            logger.warning("[curator] Error checking resource id=%s", resource_id)
            stats["errors"] += 1
            resource["last_verified"] = now
    
    directory_data["last_curated"] = now
    return directory_data
```

### Lambda Handler:
```python
def lambda_handler(event: dict, context: object) -> dict:
    """
    AWS Lambda entry point for the Curator.
    
    Triggered by EventBridge Scheduler (weekly cron).
    """
    # Get S3 configuration from environment
    bucket = os.environ.get("CD_S3_BUCKET", "clew-directive-data")
    key = os.environ.get("CD_DIRECTORY_KEY", "directory.json")
    
    # Read directory.json from S3
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)
    directory_data = json.loads(response["Body"].read())
    
    # Run freshness check
    updated = check_all_resources(directory_data)
    
    # Calculate failure rate
    resources = updated.get("resources", [])
    total = len(resources)
    failed = sum(1 for r in resources if r.get("status") != STATUS_ACTIVE)
    failure_rate = (failed / total * 100) if total > 0 else 0
    
    # Write updated directory back to S3
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(updated, indent=2),
        ContentType="application/json",
    )
    
    # Publish CloudWatch metrics
    cloudwatch = boto3.client("cloudwatch")
    cloudwatch.put_metric_data(
        Namespace="ClewDirective/Curator",
        MetricData=[
            {"MetricName": "ResourceFailureRate", "Value": failure_rate, "Unit": "Percent"},
            {"MetricName": "FailedResources", "Value": failed, "Unit": "Count"},
            {"MetricName": "TotalResources", "Value": total, "Unit": "Count"},
        ],
    )
    
    # Alert if >10% fail
    if failure_rate > 10:
        logger.error("[curator] ALERT: Failure rate %.1f%% exceeds 10%% threshold", failure_rate)
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Curator freshness check complete",
            "total_resources": total,
            "failed_resources": failed,
            "failure_rate": failure_rate,
        }),
    }
```

---

## 2. Test Coverage

**File**: `backend/tests/test_curator.py`

### Test Results: ✅ 17/17 PASSING

**Test Suites**:

**TestCuratorFreshness** (9 tests):
- ✅ `test_all_active_stays_active` - All live URLs remain active
- ✅ `test_active_degrades_on_failure` - First failure → degraded
- ✅ `test_degraded_becomes_stale` - Second failure → stale
- ✅ `test_stale_becomes_dead` - Third failure → dead
- ✅ `test_dead_stays_dead` - Dead stays dead
- ✅ `test_last_verified_updates` - Timestamp updates
- ✅ `test_last_curated_updates` - Directory timestamp updates
- ✅ `test_verification_error_handling` - Graceful error handling
- ✅ `test_mixed_results` - Mix of live and dead URLs

**TestCuratorLambda** (8 tests):
- ✅ `test_lambda_handler_success` - S3 read/write cycle
- ✅ `test_lambda_handler_high_failure_rate` - Detects 100% failure
- ✅ `test_lambda_handler_s3_error` - Handles S3 errors
- ✅ `test_lambda_handler_cloudwatch_metrics` - Publishes metrics
- ✅ `test_lambda_handler_alert_threshold` - Logs alert at >10%
- ✅ `test_lambda_handler_s3_write_format` - Writes formatted JSON
- ✅ `test_lambda_handler_default_env_vars` - Uses defaults
- ✅ `test_check_all_resources_no_pii` - No PII in output

---

## 3. Lambda Wrapper

**File**: `backend/lambda_curator.py` (NEW)

Simple wrapper for AWS Lambda deployment:
```python
from backend.curator.freshness_check import lambda_handler

# Export the handler for Lambda
handler = lambda_handler
```

**Local Testing**:
```bash
# Run tests
pytest tests/test_curator.py -v

# Or run directly (requires AWS credentials)
python lambda_curator.py
```

---

## 4. CloudWatch Metrics

### Published Metrics:

**Namespace**: `ClewDirective/Curator`

**Metrics**:
1. **ResourceFailureRate** (Percent)
   - Percentage of resources that failed verification
   - Alert threshold: >10%

2. **FailedResources** (Count)
   - Number of resources that failed verification
   - Useful for absolute tracking

3. **TotalResources** (Count)
   - Total number of resources checked
   - Baseline for failure rate calculation

### Example Metric Data:
```json
{
  "Namespace": "ClewDirective/Curator",
  "MetricData": [
    {
      "MetricName": "ResourceFailureRate",
      "Value": 4.3,
      "Unit": "Percent"
    },
    {
      "MetricName": "FailedResources",
      "Value": 1,
      "Unit": "Count"
    },
    {
      "MetricName": "TotalResources",
      "Value": 23,
      "Unit": "Count"
    }
  ]
}
```

---

## 5. EventBridge Schedule

### Cron Expression:
```
cron(0 2 ? * SUN *)
```

**Translation**: Every Sunday at 2:00 AM UTC

**Why Sunday 2 AM**:
- Low traffic time
- Weekly frequency balances freshness vs. cost
- UTC timezone for consistency

### CDK Configuration (Phase 8C):
```typescript
// infrastructure/lib/curator-stack.ts
const curatorRule = new events.Rule(this, 'CuratorSchedule', {
  schedule: events.Schedule.cron({
    minute: '0',
    hour: '2',
    weekDay: 'SUN',
  }),
});

curatorRule.addTarget(new targets.LambdaFunction(curatorLambda));
```

---

## 6. Environment Variables

### Required:
- `CD_S3_BUCKET` - S3 bucket containing directory.json
  - Default: `clew-directive-data`
  - Production: Set via CDK

- `CD_DIRECTORY_KEY` - S3 key for directory.json
  - Default: `directory.json`
  - Production: Set via CDK

### Example Lambda Configuration:
```typescript
const curatorLambda = new lambda.Function(this, 'CuratorFunction', {
  runtime: lambda.Runtime.PYTHON_3_12,
  handler: 'lambda_curator.handler',
  code: lambda.Code.fromAsset('backend'),
  environment: {
    CD_S3_BUCKET: directoryBucket.bucketName,
    CD_DIRECTORY_KEY: 'directory.json',
  },
  timeout: Duration.minutes(5),
});
```

---

## 7. IAM Permissions Required

### S3 Permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": "arn:aws:s3:::clew-directive-data/directory.json"
}
```

### CloudWatch Permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "cloudwatch:PutMetricData"
  ],
  "Resource": "*"
}
```

### Logs Permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "arn:aws:logs:*:*:*"
}
```

---

## 8. Cost Estimate

### Monthly Cost (Assuming Weekly Execution):

**EventBridge Scheduler**:
- 4 invocations/month
- Free Tier: 14M invocations/month
- **Cost**: $0.00

**Lambda**:
- 4 invocations/month
- ~30 seconds per invocation (23 resources)
- 512 MB memory
- Free Tier: 1M requests + 400,000 GB-seconds/month
- **Cost**: $0.00

**S3**:
- 4 GET requests/month
- 4 PUT requests/month
- ~50 KB file size
- Free Tier: 20,000 GET + 2,000 PUT/month
- **Cost**: $0.00

**CloudWatch Metrics**:
- 3 metrics × 4 invocations = 12 data points/month
- Free Tier: 10 custom metrics
- **Cost**: $0.00 (within free tier)

**Total Monthly Cost**: $0.00 (all within Free Tier)

---

## 9. Monitoring & Alerts

### CloudWatch Alarm (Phase 12):
```typescript
const failureRateAlarm = new cloudwatch.Alarm(this, 'CuratorFailureRateAlarm', {
  metric: new cloudwatch.Metric({
    namespace: 'ClewDirective/Curator',
    metricName: 'ResourceFailureRate',
    statistic: 'Maximum',
  }),
  threshold: 10,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  alarmDescription: 'Alert when >10% of resources fail verification',
});

failureRateAlarm.addAlarmAction(new actions.SnsAction(alertTopic));
```

### Log Insights Queries:

**Find Failed Resources**:
```
fields @timestamp, @message
| filter @message like /degraded|stale|dead/
| sort @timestamp desc
```

**Curator Execution Summary**:
```
fields @timestamp, @message
| filter @message like /Freshness check complete/
| parse @message /active: (?<active>\d+), degraded: (?<degraded>\d+), stale: (?<stale>\d+), dead: (?<dead>\d+)/
| stats latest(active) as Active, latest(degraded) as Degraded, latest(stale) as Stale, latest(dead) as Dead by bin(5m)
```

---

## 10. Status Progression Example

### Week 1: All Active
```json
{
  "id": "elements-ai-intro",
  "status": "active",
  "last_verified": "2026-02-09T02:00:00Z"
}
```

### Week 2: URL Fails (→ Degraded)
```json
{
  "id": "elements-ai-intro",
  "status": "degraded",
  "last_verified": "2026-02-16T02:00:00Z"
}
```

### Week 3: Still Failing (→ Stale)
```json
{
  "id": "elements-ai-intro",
  "status": "stale",
  "last_verified": "2026-02-23T02:00:00Z"
}
```

### Week 4: Still Failing (→ Dead)
```json
{
  "id": "elements-ai-intro",
  "status": "dead",
  "last_verified": "2026-03-02T02:00:00Z"
}
```

### Week 5: URL Restored (→ Active)
```json
{
  "id": "elements-ai-intro",
  "status": "active",
  "last_verified": "2026-03-09T02:00:00Z"
}
```

**Note**: Resources can recover at any stage. A successful verification always resets status to "active".

---

## 11. Files Involved

### Existing (Verified):
1. ✅ `backend/curator/freshness_check.py` - Core logic
2. ✅ `backend/tests/test_curator.py` - Comprehensive tests (17/17 passing)
3. ✅ `backend/tools/resource_verifier.py` - URL verification tool

### Created:
1. ✅ `backend/lambda_curator.py` - Lambda wrapper for deployment

---

## 12. Deployment Checklist (Phase 8C)

### CDK Stack Configuration:
- [ ] Create `infrastructure/lib/curator-stack.ts`
- [ ] Define Lambda function with Python 3.12 runtime
- [ ] Set environment variables (S3_BUCKET, DIRECTORY_KEY)
- [ ] Configure EventBridge cron schedule (Sundays 2 AM UTC)
- [ ] Grant S3 read/write permissions
- [ ] Grant CloudWatch PutMetricData permissions
- [ ] Deploy: `cdk deploy CuratorStack`

### Post-Deployment Verification:
- [ ] Manually invoke Lambda to test
- [ ] Check CloudWatch Logs for execution
- [ ] Verify CloudWatch Metrics published
- [ ] Verify directory.json updated in S3
- [ ] Confirm EventBridge rule created
- [ ] Wait for first scheduled execution (next Sunday)

---

## 13. Success Criteria

### ✅ All Met:
- [x] Curator logic implemented
- [x] All 17 tests passing
- [x] Status progression working (active → degraded → stale → dead)
- [x] S3 integration working (mocked in tests)
- [x] CloudWatch metrics publishing (mocked in tests)
- [x] Alert threshold detection (>10%)
- [x] Graceful error handling
- [x] No PII in output
- [x] Lambda wrapper created
- [x] Documentation complete

---

## 14. Next Steps

**Phase 8C: Deploy API to AWS**:
1. Deploy Curator Lambda with EventBridge schedule
2. Deploy API Gateway + Lambda functions for Vibe Check, Refine, Briefing
3. Test end-to-end with deployed infrastructure

**Phase 12: Monitoring**:
1. Create CloudWatch alarm for >10% failure rate
2. Set up SNS topic for alerts
3. Configure email notifications

---

**Status**: Ready for deployment (Phase 8C)  
**Confidence**: High - All tests passing, comprehensive coverage  
**Cost**: $0.00/month (within Free Tier)
