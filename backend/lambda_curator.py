"""
Lambda Handler: Curator Freshness Check

Endpoint: Triggered by EventBridge Scheduler (weekly cron)
Purpose: Verify all resources in directory.json are still live

This is a wrapper around curator/freshness_check.py for AWS Lambda deployment.
For local testing, you can invoke this directly or use the test suite.
"""

from backend.curator.freshness_check import lambda_handler

# Export the handler for Lambda
handler = lambda_handler

if __name__ == "__main__":
    # For local testing
    import json
    import os
    
    # Set test environment variables
    os.environ["CD_S3_BUCKET"] = "clew-directive-data-dev"
    os.environ["CD_DIRECTORY_KEY"] = "directory.json"
    
    print("Running Curator freshness check locally...")
    print("Note: This requires AWS credentials and S3 access")
    print()
    
    try:
        result = lambda_handler({}, None)
        print("Result:")
        print(json.dumps(json.loads(result["body"]), indent=2))
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("For local testing without AWS, run the test suite:")
        print("  pytest tests/test_curator.py -v")
