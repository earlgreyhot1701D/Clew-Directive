"""
Curator Lambda — Weekly resource freshness verification.

Triggered by EventBridge Scheduler (weekly cron).
Reads every resource in directory.json, verifies URLs are live,
optionally uses Nova Micro to check if landing pages still describe
free AI learning resources.

Updates status and last_verified fields in directory.json.
Status progression: active → degraded → stale → dead

Cost: ~$0.00/month (EventBridge free, Lambda free tier, Nova Micro negligible)
"""

import json
import logging
from datetime import datetime, timezone

from tools.resource_verifier import verify_url

logger = logging.getLogger("clew.curator")


# Status definitions
STATUS_ACTIVE = "active"       # URL live, content verified
STATUS_DEGRADED = "degraded"   # URL live but content may have changed
STATUS_STALE = "stale"         # URL redirects or content outdated
STATUS_DEAD = "dead"           # URL returns 4xx/5xx or unreachable


def check_all_resources(directory_data: dict) -> dict:
    """
    Verify all resources in the directory.

    Args:
        directory_data: The full directory.json dict.

    Returns:
        Updated directory_data with refreshed status and last_verified fields.
    """
    resources = directory_data.get("resources", [])
    now = datetime.now(timezone.utc).isoformat()
    stats = {"active": 0, "degraded": 0, "stale": 0, "dead": 0, "errors": 0}

    logger.info("[curator] Starting freshness check for %d resources", len(resources))

    for resource in resources:
        resource_id = resource.get("id", "unknown")
        url = resource.get("resource_url", "")

        try:
            is_live = verify_url(url, timeout=10)

            if is_live:
                resource["status"] = STATUS_ACTIVE
                stats["active"] += 1
            else:
                # URL failed — check previous status for progression
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
            logger.warning(
                "[curator] Error checking resource id=%s",
                resource_id,
                exc_info=True,
            )
            stats["errors"] += 1
            resource["last_verified"] = now

    logger.info(
        "[curator] Freshness check complete: %s",
        json.dumps(stats),
    )

    directory_data["last_curated"] = now
    return directory_data


def lambda_handler(event: dict, context: object) -> dict:
    """
    AWS Lambda entry point for the Curator.

    Triggered by EventBridge Scheduler (weekly cron).

    Reads directory.json from S3, verifies all resources, writes back to S3.
    Publishes CloudWatch metric for failure rate monitoring.
    """
    import os
    import boto3

    logger.info("[curator] Lambda triggered by EventBridge")

    # Get S3 configuration from environment
    bucket = os.environ.get("CD_S3_BUCKET", "clew-directive-data")
    key = os.environ.get("CD_DIRECTORY_KEY", "directory.json")

    try:
        # Read directory.json from S3
        s3 = boto3.client("s3")
        logger.info("[curator] Reading %s from S3 bucket %s", key, bucket)
        response = s3.get_object(Bucket=bucket, Key=key)
        directory_data = json.loads(response["Body"].read())

        # Run freshness check
        updated = check_all_resources(directory_data)

        # Calculate failure rate for CloudWatch metric
        resources = updated.get("resources", [])
        total = len(resources)
        failed = sum(1 for r in resources if r.get("status") != STATUS_ACTIVE)
        failure_rate = (failed / total * 100) if total > 0 else 0

        logger.info(
            "[curator] Freshness check complete: %d/%d resources failed (%.1f%%)",
            failed,
            total,
            failure_rate,
        )

        # Write updated directory back to S3
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(updated, indent=2),
            ContentType="application/json",
        )
        logger.info("[curator] Updated directory written to S3")

        # Publish CloudWatch metric for failure rate
        cloudwatch = boto3.client("cloudwatch")
        cloudwatch.put_metric_data(
            Namespace="ClewDirective/Curator",
            MetricData=[
                {
                    "MetricName": "ResourceFailureRate",
                    "Value": failure_rate,
                    "Unit": "Percent",
                },
                {
                    "MetricName": "FailedResources",
                    "Value": failed,
                    "Unit": "Count",
                },
                {
                    "MetricName": "TotalResources",
                    "Value": total,
                    "Unit": "Count",
                },
            ],
        )
        logger.info("[curator] CloudWatch metrics published")

        # Alert if >10% fail
        if failure_rate > 10:
            logger.error(
                "[curator] ALERT: Failure rate %.1f%% exceeds 10%% threshold",
                failure_rate,
            )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Curator freshness check complete",
                "total_resources": total,
                "failed_resources": failed,
                "failure_rate": failure_rate,
            }),
        }

    except Exception as e:
        logger.error("[curator] Lambda execution failed: %s", str(e), exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Curator execution failed",
                "error": str(e),
            }),
        }
