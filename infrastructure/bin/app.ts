#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { StorageStack } from '../lib/storage-stack';
import { ApiStack } from '../lib/api-stack';
import { CuratorStack } from '../lib/curator-stack';
import { FrontendStack } from '../lib/frontend-stack';
import { MonitoringStack } from '../lib/monitoring-stack';

/**
 * Clew Directive CDK App
 *
 * Deploys all infrastructure:
 *   - StorageStack: S3 bucket for directory.json + temp PDFs
 *   - ApiStack: API Gateway + Lambda for Scout/Navigator agents
 *   - CuratorStack: Lambda + EventBridge for weekly freshness checks
 *   - FrontendStack: Amplify hosting for Next.js frontend
 *   - MonitoringStack: CloudWatch alarms + dashboard + SNS notifications
 */

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

const storage = new StorageStack(app, 'ClewDirective-Storage', { env });

const apiStack = new ApiStack(app, 'ClewDirective-Api', {
  env,
  dataBucket: storage.dataBucket,
});

new CuratorStack(app, 'ClewDirective-Curator', {
  env,
  dataBucket: storage.dataBucket,
});

new FrontendStack(app, 'ClewDirective-Frontend', {
  env,
  apiUrl: apiStack.apiUrl,
});

new MonitoringStack(app, 'ClewDirective-Monitoring', {
  env,
  vibeCheckFunctionName: apiStack.vibeCheckFunctionName,
  refineProfileFunctionName: apiStack.refineProfileFunctionName,
  generateBriefingFunctionName: apiStack.generateBriefingFunctionName,
  apiGatewayName: apiStack.apiGatewayName,
});
