import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

interface ApiStackProps extends cdk.StackProps {
  dataBucket: s3.IBucket;
}

/**
 * API Stack — API Gateway + Lambda handlers for Clew Directive.
 *
 * Three Lambda functions:
 *   1. VibeCheckHandler: Process Vibe Check responses → profile summary
 *   2. RefineProfileHandler: Refine profile based on user correction
 *   3. GenerateBriefingHandler: Generate learning path + PDF
 *
 * Cost controls:
 *   - API Gateway: 10 req/sec rate limit
 *   - Lambda: scaling unreserved — API Gateway rate limiting (10 req/sec) is the primary cost guardrail
 *   - Timeout: 30 seconds (90 seconds for briefing generation)
 *   - Memory: 512 MB
 */
export class ApiStack extends cdk.Stack {
  public readonly apiUrl: string;
  public readonly vibeCheckFunctionName: string;
  public readonly refineProfileFunctionName: string;
  public readonly generateBriefingFunctionName: string;
  public readonly apiGatewayName: string;

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    // Lambda functions using Docker container images (supports up to 10GB vs 250MB for ZIP)
    
    // Lambda 1: Vibe Check Handler
    const vibeCheckFn = new lambda.DockerImageFunction(this, 'VibeCheckFunction', {
      code: lambda.DockerImageCode.fromImageAsset('../backend', {
        file: 'Dockerfile.lambda',
        cmd: ['lambda_vibe_check.lambda_handler'],
      }),
      memorySize: 512,
      timeout: cdk.Duration.seconds(30),
      description: 'Process Vibe Check responses and return profile summary',
      // 7-day retention: logs may contain session content (profiles, Vibe Check answers). Auto-expire to support privacy-by-design claim.
      logRetention: logs.RetentionDays.ONE_WEEK,
      environment: {
        CD_ENVIRONMENT: 'prod',
        CD_S3_BUCKET: props.dataBucket.bucketName,
        CD_DIRECTORY_KEY: 'data/directory.json',
      },
    });

    // Lambda 2: Refine Profile Handler
    const refineProfileFn = new lambda.DockerImageFunction(this, 'RefineProfileFunction', {
      code: lambda.DockerImageCode.fromImageAsset('../backend', {
        file: 'Dockerfile.lambda',
        cmd: ['lambda_refine_profile.lambda_handler'],
      }),
      memorySize: 512,
      timeout: cdk.Duration.seconds(30),
      description: 'Refine profile based on user correction',
      // 7-day retention: logs may contain session content (profiles, Vibe Check answers). Auto-expire to support privacy-by-design claim.
      logRetention: logs.RetentionDays.ONE_WEEK,
      environment: {
        CD_ENVIRONMENT: 'prod',
        CD_S3_BUCKET: props.dataBucket.bucketName,
        CD_DIRECTORY_KEY: 'data/directory.json',
      },
    });

    // Lambda 3: Generate Briefing Handler
    const generateBriefingFn = new lambda.DockerImageFunction(this, 'GenerateBriefingFunction', {
      code: lambda.DockerImageCode.fromImageAsset('../backend', {
        file: 'Dockerfile.lambda',
        cmd: ['lambda_generate_briefing.lambda_handler'],
      }),
      memorySize: 512,
      timeout: cdk.Duration.seconds(90), // Longer timeout for Scout + Navigator + PDF
      description: 'Generate learning path and Command Briefing PDF',
      // 7-day retention: logs may contain session content (profiles, Vibe Check answers). Auto-expire to support privacy-by-design claim.
      logRetention: logs.RetentionDays.ONE_WEEK,
      environment: {
        CD_ENVIRONMENT: 'prod',
        CD_S3_BUCKET: props.dataBucket.bucketName,
        CD_DIRECTORY_KEY: 'data/directory.json',
      },
    });

    // IAM Permissions: All functions need Bedrock access
    // Permissive policy for Nova models across all regions (Strands SDK may use different regions)
    const bedrockPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: [
        // Nova models - all regions, both foundation model and inference profile ARNs
        `arn:aws:bedrock:*:${this.account}:inference-profile/*nova*`,
        `arn:aws:bedrock:*::foundation-model/amazon.nova-*`,
      ],
    });

    vibeCheckFn.addToRolePolicy(bedrockPolicy);
    refineProfileFn.addToRolePolicy(bedrockPolicy);
    generateBriefingFn.addToRolePolicy(bedrockPolicy);

    // S3 Permissions: Read directory.json, write PDFs
    props.dataBucket.grantRead(vibeCheckFn);
    props.dataBucket.grantRead(refineProfileFn);
    props.dataBucket.grantRead(generateBriefingFn);
    props.dataBucket.grantWrite(generateBriefingFn, 'tmp/briefings/*');

    // Allowed CORS origins — restrict to custom domain and local dev
    // NOTE: clewdirective.com was manually configured in Amplify Console (not in CDK)
    const allowedOrigins = [
      'https://clewdirective.com',           // Custom domain (manual Amplify config)
      'https://www.clewdirective.com',       // www subdomain (manual Amplify config)
      'https://main.d1rbee1a32avsq.amplifyapp.com', // Amplify default (backup)
      'http://localhost:3000',                       // Local development
    ];

    // CloudWatch log group for API Gateway access logs
    // Captures every request: method, path, status code, IP, latency.
    // Useful for diagnosing 4xx spikes (bot scanners, CORS errors, bad paths).
    // 7-day retention matches Lambda log retention — no PII in access logs.
    const accessLogGroup = new logs.LogGroup(this, 'ApiAccessLogs', {
      logGroupName: '/aws/apigateway/ClewDirective-Access',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // IAM role granting API Gateway permission to write to CloudWatch Logs.
    // This is a one-time account-level requirement but scoped here per-API.
    const apiGatewayLoggingRole = new iam.Role(this, 'ApiGatewayLoggingRole', {
      assumedBy: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AmazonAPIGatewayPushToCloudWatchLogs'
        ),
      ],
    });

    // Register the logging role with the API Gateway account settings
    const cfnAccount = new apigateway.CfnAccount(this, 'ApiGatewayAccount', {
      cloudWatchRoleArn: apiGatewayLoggingRole.roleArn,
    });

    // API Gateway with rate limiting, CORS, and access logging
    const api = new apigateway.RestApi(this, 'ClewDirectiveApi', {
      restApiName: 'Clew Directive API',
      description: 'REST API for Clew Directive AI learning navigator',
      deployOptions: {
        throttlingRateLimit: 10,    // 10 req/sec
        throttlingBurstLimit: 20,   // Burst to 20
        stageName: 'prod',
        // Access logging: one JSON line per request with status, path, IP, latency
        accessLogDestination: new apigateway.LogGroupLogDestination(accessLogGroup),
        accessLogFormat: apigateway.AccessLogFormat.custom(
          JSON.stringify({
            requestId:      '$context.requestId',
            ip:             '$context.identity.sourceIp',
            method:         '$context.httpMethod',
            path:           '$context.path',
            status:         '$context.status',
            responseLength: '$context.responseLength',
            latencyMs:      '$context.responseLatency',
            userAgent:      '$context.identity.userAgent',
            errorMessage:   '$context.error.message',
          })
        ),
      },
      defaultCorsPreflightOptions: {
        allowOrigins: allowedOrigins,
        allowMethods: ['POST', 'OPTIONS'],
        allowHeaders: ['Content-Type'],
      },
    });

    // Ensure the account CfnAccount resource is created before the API stage
    api.node.addDependency(cfnAccount);

    // POST /vibe-check — Process Vibe Check responses
    const vibeCheckResource = api.root.addResource('vibe-check');
    vibeCheckResource.addMethod('POST', new apigateway.LambdaIntegration(vibeCheckFn));

    // POST /refine-profile — Refine profile based on user correction
    const refineProfileResource = api.root.addResource('refine-profile');
    refineProfileResource.addMethod('POST', new apigateway.LambdaIntegration(refineProfileFn));

    // POST /generate-briefing — Generate learning path and PDF
    const generateBriefingResource = api.root.addResource('generate-briefing');
    generateBriefingResource.addMethod('POST', new apigateway.LambdaIntegration(generateBriefingFn));

    // Store API URL and resource names for use by other stacks
    // Remove trailing slash from API Gateway URL to prevent double-slash in requests
    this.apiUrl = api.url.replace(/\/$/, '');
    this.vibeCheckFunctionName = vibeCheckFn.functionName;
    this.refineProfileFunctionName = refineProfileFn.functionName;
    this.generateBriefingFunctionName = generateBriefingFn.functionName;
    this.apiGatewayName = api.restApiId;

    // Output API URL for frontend configuration
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.apiUrl,
      description: 'Clew Directive API Gateway URL',
      exportName: 'ClewDirectiveApiUrl',
    });
  }
}
