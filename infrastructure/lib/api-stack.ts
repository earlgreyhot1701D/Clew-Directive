import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
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
 *   - Lambda: reserved concurrency of 10 per function
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
    const allowedOrigins = [
      'https://clewdirective.com',           // Custom domain
      'https://www.clewdirective.com',       // www subdomain
      'https://main.d1rbee1a32avsq.amplifyapp.com', // Amplify default (backup)
      'http://localhost:3000',                       // Local development
    ];

    // API Gateway with rate limiting and CORS
    const api = new apigateway.RestApi(this, 'ClewDirectiveApi', {
      restApiName: 'Clew Directive API',
      description: 'REST API for Clew Directive AI learning navigator',
      deployOptions: {
        throttlingRateLimit: 10,    // 10 req/sec
        throttlingBurstLimit: 20,   // Burst to 20
        stageName: 'prod',
      },
      defaultCorsPreflightOptions: {
        allowOrigins: allowedOrigins,
        allowMethods: ['POST', 'OPTIONS'],
        allowHeaders: ['Content-Type'],
      },
    });

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
