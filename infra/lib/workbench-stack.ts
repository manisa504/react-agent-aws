import * as path from "node:path";
import {
  Stack,
  StackProps,
  Duration,
  RemovalPolicy,
  CfnOutput,
  Tags,
} from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-lambda-event-sources";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as logs from "aws-cdk-lib/aws-logs";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as iam from "aws-cdk-lib/aws-iam";
import * as api from "aws-cdk-lib/aws-apigatewayv2";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import { HttpJwtAuthorizer } from "aws-cdk-lib/aws-apigatewayv2-authorizers";
export interface WorkbenchProps extends StackProps {
  readonly modelId: string;
  readonly modelResourceArns: readonly string[];
  readonly frontendOrigin: string;
}
export class WorkbenchStack extends Stack {
  constructor(scope: Construct, id: string, props: WorkbenchProps) {
    super(scope, id, props);
    Tags.of(this).add("Project", "ReActWorkbench");
    if (!/^https:\/\/[a-zA-Z0-9.-]+(?::\d+)?$/.test(props.frontendOrigin))
      throw new Error(
        "FRONTEND_ORIGIN must be one HTTPS origin without a path",
      );
    const table = new dynamodb.Table(this, "Runs", {
      partitionKey: { name: "PK", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "SK", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "ttl",
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: RemovalPolicy.RETAIN,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: false },
    });
    const dlq = new sqs.Queue(this, "DLQ", {
      retentionPeriod: Duration.days(14),
      encryption: sqs.QueueEncryption.SQS_MANAGED,
    });
    const queue = new sqs.Queue(this, "Queue", {
      visibilityTimeout: Duration.minutes(18),
      retentionPeriod: Duration.days(1),
      deadLetterQueue: { queue: dlq, maxReceiveCount: 5 },
      encryption: sqs.QueueEncryption.SQS_MANAGED,
    });
    const pool = new cognito.UserPool(this, "Users", {
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      autoVerify: { email: true },
      passwordPolicy: {
        minLength: 12,
        requireDigits: true,
        requireLowercase: true,
        requireUppercase: true,
        requireSymbols: true,
      },
      removalPolicy: RemovalPolicy.DESTROY,
    });
    const client = pool.addClient("WebClient", {
      generateSecret: false,
      authFlows: { userSrp: true },
      preventUserExistenceErrors: true,
      accessTokenValidity: Duration.hours(1),
      idTokenValidity: Duration.hours(1),
    });
    const code = lambda.Code.fromAsset(
      path.resolve(__dirname, "../../.build/lambda"),
    );
    const apiLogs = new logs.LogGroup(this, "ApiLogs", {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY,
    });
    const workerLogs = new logs.LogGroup(this, "WorkerLogs", {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY,
    });
    const apiFn = new lambda.Function(this, "Api", {
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.X86_64,
      handler: "app.api.handler",
      code,
      timeout: Duration.seconds(15),
      memorySize: 256,
      logGroup: apiLogs,
      environment: {
        DEMO_MODE: "false",
        TABLE_NAME: table.tableName,
        QUEUE_URL: queue.queueUrl,
      },
    });
    const worker = new lambda.Function(this, "Worker", {
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.X86_64,
      handler: "app.worker.handler",
      code,
      timeout: Duration.seconds(180),
      memorySize: 512,
      logGroup: workerLogs,
      environment: {
        TABLE_NAME: table.tableName,
        BEDROCK_MODEL_ID: props.modelId,
      },
    });
    apiFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"],
        resources: [table.tableArn],
      }),
    );
    worker.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
        ],
        resources: [table.tableArn],
      }),
    );
    queue.grantSendMessages(apiFn);
    if (props.modelResourceArns.length)
      worker.addToRolePolicy(
        new iam.PolicyStatement({
          actions: ["bedrock:InvokeModel"],
          resources: [...props.modelResourceArns],
        }),
      );
    worker.addEventSource(
      new events.SqsEventSource(queue, {
        batchSize: 1,
        reportBatchItemFailures: true,
        maxConcurrency: 2,
      }),
    );
    const http = new api.HttpApi(this, "HttpApi", {
      corsPreflight: {
        allowOrigins: [props.frontendOrigin],
        allowHeaders: ["Authorization", "Content-Type"],
        allowMethods: [
          api.CorsHttpMethod.GET,
          api.CorsHttpMethod.POST,
          api.CorsHttpMethod.OPTIONS,
        ],
        maxAge: Duration.hours(1),
      },
    });
    const authorizer = new HttpJwtAuthorizer(
      "CognitoJwt",
      pool.userPoolProviderUrl,
      { jwtAudience: [client.userPoolClientId] },
    );
    const integration = new HttpLambdaIntegration("ApiIntegration", apiFn);
    http.addRoutes({
      path: "/health",
      methods: [api.HttpMethod.GET],
      integration,
    });
    http.addRoutes({
      path: "/runs",
      methods: [api.HttpMethod.POST],
      integration,
      authorizer,
      authorizationScopes: ["aws.cognito.signin.user.admin"],
    });
    for (const route of ["/runs/{run_id}", "/runs/{run_id}/steps"])
      http.addRoutes({
        path: route,
        methods: [api.HttpMethod.GET],
        integration,
        authorizer,
        authorizationScopes: ["aws.cognito.signin.user.admin"],
      });
    worker
      .metricErrors({ period: Duration.minutes(5) })
      .createAlarm(this, "WorkerErrors", {
        threshold: 1,
        evaluationPeriods: 1,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      });
    dlq
      .metricApproximateNumberOfMessagesVisible({ period: Duration.minutes(5) })
      .createAlarm(this, "DLQMessages", {
        threshold: 1,
        evaluationPeriods: 1,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      });
    const output: Record<string, string> = {
      Region: this.region,
      ApiUrl: http.apiEndpoint,
      UserPoolId: pool.userPoolId,
      UserPoolClientId: client.userPoolClientId,
      TableName: table.tableName,
      QueueUrl: queue.queueUrl,
      QueueArn: queue.queueArn,
      DLQUrl: dlq.queueUrl,
      ApiFunction: apiFn.functionName,
      WorkerFunction: worker.functionName,
      ApiLogGroup: apiLogs.logGroupName,
      WorkerLogGroup: workerLogs.logGroupName,
    };
    for (const [name, value] of Object.entries(output))
      new CfnOutput(this, name, { value });
  }
}
