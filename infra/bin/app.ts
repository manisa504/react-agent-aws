import { App } from "aws-cdk-lib";
import { WorkbenchStack } from "../lib/workbench-stack";
const app = new App();
new WorkbenchStack(app, "ReActWorkbenchStack", {
  env: {
    account: process.env.DEPLOY_ACCOUNT || "263429641790",
    region: process.env.AWS_REGION || "us-east-1",
  },
  modelId: process.env.BEDROCK_MODEL_ID || "configure-before-deployment",
  modelResourceArns: process.env.BEDROCK_RESOURCE_ARNS
    ? (JSON.parse(process.env.BEDROCK_RESOURCE_ARNS) as string[])
    : [],
  frontendOrigin: process.env.FRONTEND_ORIGIN || "https://frontend.invalid",
});
