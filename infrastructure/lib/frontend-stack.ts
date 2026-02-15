import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

/**
 * Frontend Stack — Amplify hosting for Next.js.
 *
 * Provides a live public URL for the voting period.
 * Free Tier: 1000 build min/mo, 15GB served/mo, 5GB storage.
 *
 * TODO: Implement Amplify CDK construct
 * Options:
 *   1. aws-cdk-lib/aws-amplify (L2 construct)
 *   2. Manual Amplify setup via console + connect to GitHub repo
 *
 * For hackathon speed, option 2 (console setup) may be faster.
 * CDK construct documented here for completeness.
 */
export class FrontendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // TODO: Implement Amplify hosting
    // import * as amplify from 'aws-cdk-lib/aws-amplify';
    //
    // const app = new amplify.App(this, 'ClewDirectiveFrontend', {
    //   sourceCodeProvider: new amplify.GitHubSourceCodeProvider({
    //     owner: 'team-docket-1701d',
    //     repository: 'clew-directive',
    //     oauthToken: cdk.SecretValue.secretsManager('github-token'),
    //   }),
    //   buildSpec: cdk.aws_codebuild.BuildSpec.fromObjectToYaml({
    //     version: '1.0',
    //     frontend: {
    //       phases: {
    //         preBuild: { commands: ['cd frontend', 'npm ci'] },
    //         build: { commands: ['npm run build'] },
    //       },
    //       artifacts: { baseDirectory: 'frontend/.next', files: ['**/*'] },
    //     },
    //   }),
    // });
    //
    // app.addBranch('main');
  }
}
