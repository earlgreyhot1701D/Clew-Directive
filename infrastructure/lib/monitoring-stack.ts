import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatch_actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as sns_subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import { Construct } from 'constructs';

interface MonitoringStackProps extends cdk.StackProps {
  vibeCheckFunctionName: string;
  refineProfileFunctionName: string;
  generateBriefingFunctionName: string;
  curatorFunctionName: string;
  apiGatewayName: string;
}

/**
 * Monitoring Stack — CloudWatch alarms and dashboard for Clew Directive.
 *
 * Monitors:
 *   - High traffic (>200 briefings/day)
 *   - Error rates (>5 errors in 5 minutes)
 *   - API Gateway performance
 *   - Lambda invocations and errors
 *
 * Notifications:
 *   - SNS topic with email subscription
 *   - All alarms send to email
 */
export class MonitoringStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    // SNS Topic for alarm notifications
    const alarmTopic = new sns.Topic(this, 'AlarmTopic', {
      displayName: 'Clew Directive Alarms',
      topicName: 'ClewDirective-Alarms',
    });

    // Email subscription
    alarmTopic.addSubscription(
      new sns_subscriptions.EmailSubscription('cordero.lsj@gmail.com')
    );

    // Import Lambda functions by name
    const vibeCheckFn = lambda.Function.fromFunctionName(
      this,
      'VibeCheckFunction',
      props.vibeCheckFunctionName
    );

    const refineProfileFn = lambda.Function.fromFunctionName(
      this,
      'RefineProfileFunction',
      props.refineProfileFunctionName
    );

    const generateBriefingFn = lambda.Function.fromFunctionName(
      this,
      'GenerateBriefingFunction',
      props.generateBriefingFunctionName
    );

    const curatorFn = lambda.Function.fromFunctionName(
      this,
      'CuratorFunction',
      props.curatorFunctionName
    );

    // Import API Gateway by name
    const api = apigateway.RestApi.fromRestApiAttributes(this, 'ClewDirectiveApi', {
      restApiId: props.apiGatewayName,
      rootResourceId: 'root', // Placeholder, not used for metrics
    });

    // ============================================
    // ALARM 1: High Traffic Alert
    // ============================================
    const highTrafficAlarm = new cloudwatch.Alarm(this, 'HighTrafficAlarm', {
      alarmName: 'ClewDirective-HighTraffic',
      alarmDescription: 'Alert when briefing generation exceeds 200 per day',
      metric: generateBriefingFn.metricInvocations({
        statistic: 'Sum',
        period: cdk.Duration.days(1),
      }),
      threshold: 200,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    highTrafficAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));

    // ============================================
    // ALARM 2: Lambda Error Rate (All Functions)
    // ============================================
    
    // Vibe Check errors
    const vibeCheckErrorAlarm = new cloudwatch.Alarm(this, 'VibeCheckErrorAlarm', {
      alarmName: 'ClewDirective-VibeCheckErrors',
      alarmDescription: 'Alert when Vibe Check function has >5 errors in 5 minutes',
      metric: vibeCheckFn.metricErrors({
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    vibeCheckErrorAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));

    // Refine Profile errors
    const refineProfileErrorAlarm = new cloudwatch.Alarm(this, 'RefineProfileErrorAlarm', {
      alarmName: 'ClewDirective-RefineProfileErrors',
      alarmDescription: 'Alert when Refine Profile function has >5 errors in 5 minutes',
      metric: refineProfileFn.metricErrors({
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    refineProfileErrorAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));

    // Generate Briefing errors
    const generateBriefingErrorAlarm = new cloudwatch.Alarm(this, 'GenerateBriefingErrorAlarm', {
      alarmName: 'ClewDirective-GenerateBriefingErrors',
      alarmDescription: 'Alert when Generate Briefing function has >5 errors in 5 minutes',
      metric: generateBriefingFn.metricErrors({
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    generateBriefingErrorAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));

    // Curator errors
    const curatorErrorAlarm = new cloudwatch.Alarm(this, 'CuratorErrorAlarm', {
      alarmName: 'ClewDirective-CuratorErrors',
      alarmDescription: 'Alert when weekly Curator run has any errors',
      metric: curatorFn.metricErrors({
        statistic: 'Sum',
        period: cdk.Duration.days(1),
      }),
      threshold: 0,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    curatorErrorAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));

    // Curator resource failure rate
    const curatorFailureRateAlarm = new cloudwatch.Alarm(this, 'CuratorResourceFailureRateAlarm', {
      alarmName: 'ClewDirective-CuratorResourceFailureRate',
      alarmDescription: 'Alert when >10% of curated resources fail freshness check',
      metric: new cloudwatch.Metric({
        namespace: 'ClewDirective/Curator',
        metricName: 'ResourceFailureRate',
        statistic: 'Maximum',
        period: cdk.Duration.days(7),
      }),
      threshold: 10,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    curatorFailureRateAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));

    // ============================================
    // ALARM 3: API Gateway 5xx Errors
    // ============================================
    const apiErrorAlarm = new cloudwatch.Alarm(this, 'ApiGateway5xxAlarm', {
      alarmName: 'ClewDirective-ApiGateway5xx',
      alarmDescription: 'Alert when API Gateway has >5 5xx errors in 5 minutes',
      metric: new cloudwatch.Metric({
        namespace: 'AWS/ApiGateway',
        metricName: '5XXError',
        dimensionsMap: {
          ApiName: 'Clew Directive API',
        },
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    apiErrorAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));

    // ============================================
    // ALARM 4: API Gateway 4xx Errors
    // ============================================
    const apiGateway4xxAlarm = new cloudwatch.Alarm(this, 'ApiGateway4xxAlarm', {
      alarmName: 'ClewDirective-ApiGateway4xx',
      alarmDescription: 'Alert when API Gateway has >20 4xx errors in 5 minutes',
      metric: new cloudwatch.Metric({
        namespace: 'AWS/ApiGateway',
        metricName: '4XXError',
        dimensionsMap: {
          ApiName: 'Clew Directive API',
        },
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 20,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    apiGateway4xxAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));

    // ============================================
    // CloudWatch Dashboard
    // ============================================
    const dashboard = new cloudwatch.Dashboard(this, 'ClewDirectiveDashboard', {
      dashboardName: 'ClewDirective-Monitoring',
    });

    // Row 1: API Gateway Metrics
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'API Gateway - Requests',
        left: [
          new cloudwatch.Metric({
            namespace: 'AWS/ApiGateway',
            metricName: 'Count',
            dimensionsMap: {
              ApiName: 'Clew Directive API',
            },
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Total Requests',
          }),
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'API Gateway - Errors',
        left: [
          new cloudwatch.Metric({
            namespace: 'AWS/ApiGateway',
            metricName: '4XXError',
            dimensionsMap: {
              ApiName: 'Clew Directive API',
            },
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: '4xx Errors',
            color: cloudwatch.Color.ORANGE,
          }),
          new cloudwatch.Metric({
            namespace: 'AWS/ApiGateway',
            metricName: '5XXError',
            dimensionsMap: {
              ApiName: 'Clew Directive API',
            },
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: '5xx Errors',
            color: cloudwatch.Color.RED,
          }),
        ],
        width: 12,
      })
    );

    // Row 2: Lambda Invocations
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda - Invocations',
        left: [
          vibeCheckFn.metricInvocations({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Vibe Check',
            color: cloudwatch.Color.BLUE,
          }),
          refineProfileFn.metricInvocations({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Refine Profile',
            color: cloudwatch.Color.GREEN,
          }),
          generateBriefingFn.metricInvocations({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Generate Briefing',
            color: cloudwatch.Color.PURPLE,
          }),
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda - Errors',
        left: [
          vibeCheckFn.metricErrors({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Vibe Check Errors',
            color: cloudwatch.Color.RED,
          }),
          refineProfileFn.metricErrors({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Refine Profile Errors',
            color: cloudwatch.Color.ORANGE,
          }),
          generateBriefingFn.metricErrors({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Generate Briefing Errors',
            color: cloudwatch.Color.RED,
          }),
        ],
        width: 12,
      })
    );

    // Row 3: Lambda Duration
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda - Duration (ms)',
        left: [
          vibeCheckFn.metricDuration({
            statistic: 'Average',
            period: cdk.Duration.minutes(5),
            label: 'Vibe Check (avg)',
            color: cloudwatch.Color.BLUE,
          }),
          refineProfileFn.metricDuration({
            statistic: 'Average',
            period: cdk.Duration.minutes(5),
            label: 'Refine Profile (avg)',
            color: cloudwatch.Color.GREEN,
          }),
          generateBriefingFn.metricDuration({
            statistic: 'Average',
            period: cdk.Duration.minutes(5),
            label: 'Generate Briefing (avg)',
            color: cloudwatch.Color.PURPLE,
          }),
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda - Throttles',
        left: [
          vibeCheckFn.metricThrottles({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Vibe Check',
            color: cloudwatch.Color.RED,
          }),
          refineProfileFn.metricThrottles({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Refine Profile',
            color: cloudwatch.Color.ORANGE,
          }),
          generateBriefingFn.metricThrottles({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
            label: 'Generate Briefing',
            color: cloudwatch.Color.RED,
          }),
        ],
        width: 12,
      })
    );

    // Row 4: Single Value Widgets (Current Stats)
    dashboard.addWidgets(
      new cloudwatch.SingleValueWidget({
        title: 'Briefings Today',
        metrics: [
          generateBriefingFn.metricInvocations({
            statistic: 'Sum',
            period: cdk.Duration.days(1),
          }),
        ],
        width: 6,
      }),
      new cloudwatch.SingleValueWidget({
        title: 'Total Errors (5 min)',
        metrics: [
          vibeCheckFn.metricErrors({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
          }),
          refineProfileFn.metricErrors({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
          }),
          generateBriefingFn.metricErrors({
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
          }),
        ],
        width: 6,
      }),
      new cloudwatch.SingleValueWidget({
        title: 'Avg Briefing Duration (ms)',
        metrics: [
          generateBriefingFn.metricDuration({
            statistic: 'Average',
            period: cdk.Duration.minutes(5),
          }),
        ],
        width: 6,
      }),
      new cloudwatch.SingleValueWidget({
        title: 'API Requests (5 min)',
        metrics: [
          new cloudwatch.Metric({
            namespace: 'AWS/ApiGateway',
            metricName: 'Count',
            dimensionsMap: {
              ApiName: 'Clew Directive API',
            },
            statistic: 'Sum',
            period: cdk.Duration.minutes(5),
          }),
        ],
        width: 6,
      })
    );

    // Outputs
    new cdk.CfnOutput(this, 'AlarmTopicArn', {
      value: alarmTopic.topicArn,
      description: 'SNS Topic ARN for alarm notifications',
      exportName: 'ClewDirectiveAlarmTopicArn',
    });

    new cdk.CfnOutput(this, 'DashboardUrl', {
      value: `https://console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=${dashboard.dashboardName}`,
      description: 'CloudWatch Dashboard URL',
    });

    new cdk.CfnOutput(this, 'EmailSubscription', {
      value: 'cordero.lsj@gmail.com',
      description: 'Email address for alarm notifications (check inbox for confirmation)',
    });
  }
}
