import { test } from "node:test";
import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { WorkbenchStack } from "../lib/workbench-stack";
test("bounded async stack, protected routes and retained storage", () => {
  const stack = new WorkbenchStack(new App(), "Test", {
    env: { account: "111111111111", region: "us-east-1" },
    modelId: "test-model",
    modelResourceArns: [
      "arn:aws:bedrock:us-east-1::foundation-model/test-model",
    ],
    frontendOrigin: "https://example.com",
  });
  const template = Template.fromStack(stack);
  template.resourceCountIs("AWS::Lambda::Function", 2);
  template.resourceCountIs("AWS::DynamoDB::Table", 1);
  template.resourceCountIs("AWS::SQS::Queue", 2);
  template.resourceCountIs("AWS::CloudWatch::Alarm", 2);
  template.hasResourceProperties("AWS::Lambda::Function", {
    Timeout: 180,
    Runtime: "python3.12",
  });
  template.hasResourceProperties("AWS::SQS::Queue", {
    VisibilityTimeout: 1080,
  });
  template.hasResourceProperties("AWS::Lambda::EventSourceMapping", {
    BatchSize: 1,
    FunctionResponseTypes: ["ReportBatchItemFailures"],
  });
  template.hasResourceProperties("AWS::ApiGatewayV2::Route", {
    RouteKey: "POST /runs",
    AuthorizationType: "JWT",
    AuthorizationScopes: ["aws.cognito.signin.user.admin"],
  });
  template.hasResourceProperties("AWS::ApiGatewayV2::Api", {
    CorsConfiguration: { AllowOrigins: ["https://example.com"] },
  });
  template.hasResource("AWS::DynamoDB::Table", { DeletionPolicy: "Retain" });
  template.hasResourceProperties("AWS::IAM::Policy", {
    PolicyDocument: {
      Statement: Match.arrayWith([
        Match.objectLike({
          Action: "bedrock:InvokeModel",
          Resource: "arn:aws:bedrock:us-east-1::foundation-model/test-model",
        }),
      ]),
    },
  });
});
