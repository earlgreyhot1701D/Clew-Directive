import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

interface CuratorStackProps extends cdk.StackProps {
  dataBucket: s3.IBucket;
}

/**
 * Curator Stack — Weekly resource freshness verification.
 *
 * EventBridge Scheduler triggers Lambda every Sunday at 2:00 AM UTC.
 * Lambda reads directory.json, verifies URLs, updates status fields.
 * Cost: ~$0.00/month (all Free Tier).
 */
export class CuratorStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: CuratorStackProps) {
    super(scope, id, props);

    const curatorFn = new lambda.Function(this, 'CuratorFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'lambda_curator.handler',
      code: lambda.Code.fromAsset('../backend'),
      timeout: cdk.Duration.minutes(5), // URL checks take time
      memorySize: 256,
      environment: {
        CD_ENVIRONMENT: 'prod',
        CD_S3_BUCKET: props.dataBucket.bucketName,
        CD_DIRECTORY_KEY: 'data/directory.json',
      },
    });

    // Curator needs read/write to S3 for directory.json
    props.dataBucket.grantReadWrite(curatorFn, 'data/directory.json');

    // Curator uses Nova Micro for content verification
    curatorFn.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel'],
      resources: ['*'], // TODO: Scope to Nova Micro ARN
    }));

    // Weekly schedule: every Sunday at 2:00 AM UTC
    new events.Rule(this, 'WeeklyCuratorRule', {
      schedule: events.Schedule.cron({
        minute: '0',
        hour: '2',
        weekDay: 'SUN',
      }),
      targets: [new targets.LambdaFunction(curatorFn)],
    });
  }
}
