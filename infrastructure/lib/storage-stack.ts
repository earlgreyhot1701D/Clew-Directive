import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

/**
 * Storage Stack — S3 bucket for directory.json and temporary PDFs.
 *
 * Lifecycle rules:
 *   - tmp/briefings/ objects expire after 1 hour (PDF cleanup)
 *   - directory.json is versioned (rollback on bad Curator update)
 */
export class StorageStack extends cdk.Stack {
  public readonly dataBucket: s3.IBucket;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.dataBucket = new s3.Bucket(this, 'DataBucket', {
      bucketName: `clew-directive-data-${this.account}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [
        {
          prefix: 'tmp/briefings/',
          expiration: cdk.Duration.days(1), // Changed from hours to days
        },
      ],
    });
  }
}
