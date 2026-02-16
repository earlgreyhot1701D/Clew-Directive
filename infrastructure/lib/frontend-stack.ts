import * as cdk from 'aws-cdk-lib';
import * as amplify from '@aws-cdk/aws-amplify-alpha';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import { Construct } from 'constructs';

interface FrontendStackProps extends cdk.StackProps {
  apiUrl: string;
}

/**
 * Frontend Stack — Amplify hosting for Next.js.
 *
 * Deploys the Next.js frontend to AWS Amplify with:
 * - GitHub integration for automatic deployments
 * - Environment variables for API Gateway URL
 * - Custom build configuration for Next.js
 * - Free Tier: 1000 build min/mo, 15GB served/mo, 5GB storage
 */
export class FrontendStack extends cdk.Stack {
  public readonly appUrl: string;

  constructor(scope: Construct, id: string, props: FrontendStackProps) {
    super(scope, id, props);

    // GitHub OAuth token from Secrets Manager
    const githubToken = cdk.SecretValue.secretsManager('github-token-amplify');

    // Amplify App
    const amplifyApp = new amplify.App(this, 'ClewDirectiveFrontend', {
      appName: 'Clew-Directive',
      description: 'AI learning navigator - personalized paths to free resources',
      sourceCodeProvider: new amplify.GitHubSourceCodeProvider({
        owner: 'earlgreyhot1701D',
        repository: 'Clew-Directive',
        oauthToken: githubToken,
      }),
      environmentVariables: {
        // API Gateway URL for backend
        'NEXT_PUBLIC_API_URL': props.apiUrl,
        // Next.js build optimization
        'NEXT_TELEMETRY_DISABLED': '1',
        '_LIVE_UPDATES': JSON.stringify([
          {
            pkg: 'next',
            type: 'internal',
            version: 'latest',
          },
        ]),
      },
      buildSpec: codebuild.BuildSpec.fromObjectToYaml({
        version: '1.0',
        frontend: {
          phases: {
            preBuild: {
              commands: [
                'cd frontend',
                'npm ci',
              ],
            },
            build: {
              commands: [
                'npm run build',
              ],
            },
          },
          artifacts: {
            baseDirectory: 'frontend/.next',
            files: ['**/*'],
          },
          cache: {
            paths: [
              'frontend/node_modules/**/*',
            ],
          },
        },
      }),
    });

    // Add main branch
    const mainBranch = amplifyApp.addBranch('main', {
      branchName: 'main',
      stage: 'PRODUCTION',
      autoBuild: true, // Auto-deploy on push to main
    });

    // Store the app URL for output
    this.appUrl = `https://main.${amplifyApp.defaultDomain}`;

    // Outputs
    new cdk.CfnOutput(this, 'AmplifyAppId', {
      value: amplifyApp.appId,
      description: 'Amplify App ID',
      exportName: 'ClewDirectiveAmplifyAppId',
    });

    new cdk.CfnOutput(this, 'AmplifyAppUrl', {
      value: this.appUrl,
      description: 'Clew Directive Frontend URL',
      exportName: 'ClewDirectiveFrontendUrl',
    });

    new cdk.CfnOutput(this, 'AmplifyConsoleUrl', {
      value: `https://console.aws.amazon.com/amplify/home?region=${this.region}#/${amplifyApp.appId}`,
      description: 'Amplify Console URL for monitoring builds',
    });
  }
}

