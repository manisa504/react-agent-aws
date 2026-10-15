# AWS deployment

## Preconditions

The chosen target is account `263429641790` (provided account ARN: `arn:aws:account::263429641790:account`), `AWS_PROFILE=research`, `AWS_REGION=us-east-1`. The account ARN identifies the destination; it does not provide credentials or an assumable role. Before any resource creation, authenticate with `aws login --profile research --region us-east-1`, then verify identity. Never commit credentials, passwords, or tokens. The root README records whether live deployment has actually been verified.

```sh
export AWS_PROFILE=research AWS_REGION=us-east-1
aws sts get-caller-identity
export DEPLOY_ACCOUNT=263429641790
test "$(aws sts get-caller-identity --query Account --output text)" = "$DEPLOY_ACCOUNT" || exit 1
aws bedrock list-foundation-models --region "$AWS_REGION"
aws bedrock list-inference-profiles --region "$AWS_REGION"
```

Select a model supporting Converse client-side tool use in this region and account. Verify access, subscription requirements, current input/output prices, and any profile's destination regions. Do not assume a listed model is invocable. Set `BEDROCK_MODEL_ID` to the verified model/profile ID. Set `BEDROCK_RESOURCE_ARNS` to a JSON array of its exact invocation resource ARNs. For an inference profile include the profile ARN and the destination foundation-model ARNs required by its IAM guidance; do not substitute `*`.

[Converse tool use](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html) · [Supported models](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html) · [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)

Create an AWS Budget alert in the console and choose the notification recipient. Alerts are not a spending cap. Review Bedrock per-token usage, Amplify build/hosting/data transfer, API Gateway requests, Lambda duration, DynamoDB requests/storage, SQS, and CloudWatch pricing for the selected region. This project does not invent a fixed monthly estimate before model and usage are chosen.

## Current account readiness

Authentication to account `263429641790` succeeded, and Bedrock model/profile discovery worked in `us-east-1`. An organization service control policy explicitly denied `amplify:ListApps` and `cloudformation:DescribeStacks` for both `ReActWorkbenchStack` and `CDKToolkit`. Deployment is blocked by these account controls; no resources were provisioned. Have the account administrator review these specific denials and approve an environment for the documented architecture before continuing. Do not bypass the controls by changing roles or regions without authorization. Model listing alone does not establish invocation access.

## Git and Amplify preparation

Use the supplied repository `https://github.com/manisa504/react-agent-aws`. It was empty and publicly readable when checked. The local checkout is connected to this repository as `origin`; push the implementation after GitHub authentication. Preserve its current visibility unless the owner requests a change; do not include the surrounding source zip, `.env`, `.venv`, `node_modules`, `.build`, or AWS outputs. If using GitHub CLI, install and authenticate it first with browser authorization. Otherwise create the repository through GitHub's UI and use standard Git authentication.

In Amplify Hosting, connect this repository manually and select the main branch. Configure the monorepo root as `frontend` (`AMPLIFY_MONOREPO_APP_ROOT=frontend`); the committed `amplify.yml` defines npm installation, build, artifacts, and caching. Record the assigned Amplify origin and App ID before deploying the backend. An initial build may show the unconfigured sign-in state until outputs are supplied.

Set `FRONTEND_ORIGIN` to the exact Amplify HTTPS origin without a trailing slash. No wildcard CORS is allowed. The implemented SDK sign-in uses Cognito SRP rather than hosted OAuth redirects, so callback URLs are not needed. If adding hosted sign-in later, explicitly configure allowed callback/logout origins and PKCE.

## Backend deployment checkpoint

```sh
make setup
make verify
# Export verified BEDROCK_MODEL_ID, BEDROCK_RESOURCE_ARNS and FRONTEND_ORIGIN first.
cd infra
npx cdk bootstrap "aws://$DEPLOY_ACCOUNT/$AWS_REGION" --profile "$AWS_PROFILE"
npx cdk synth --strict --no-lookups
npx cdk diff ReActWorkbenchStack --profile "$AWS_PROFILE"
```

Bootstrap creates shared account infrastructure; do it only when needed. Inspect the synthesized template and IAM diff. Present the actual account, region, model, pricing estimate for the planned demo usage, and changes for owner approval before spending/deployment, as required by the project prompt.

After approval:

```sh
npx cdk deploy ReActWorkbenchStack --profile "$AWS_PROFILE" --outputs-file ../.build/aws-outputs.json
```

The packaging gate creates Linux x86_64 CPython 3.12 assets with FastAPI, Mangum, Pydantic, boto3, and local knowledge. Both Lambdas are outside a VPC. Queue visibility is 1,080 seconds for the 180-second worker; batch size is one, redrive count five. [AWS queue configuration guidance](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html).

## Frontend and users

Populate Amplify's build variables from the stack outputs:

```text
VITE_DEMO_MODE=false
VITE_API_URL=<ApiUrl>
VITE_REGION=us-east-1
VITE_USER_POOL_ID=<UserPoolId>
VITE_USER_POOL_CLIENT_ID=<UserPoolClientId>
```

These are public configuration, not secrets. Rebuild Amplify. Add an HTTP 200 SPA rewrite using Amplify's documented extension-excluding regex to `/index.html`; preserve real static assets. See [SPA redirects](https://docs.aws.amazon.com/amplify/latest/userguide/redirect-rewrite-examples.html).

In Cognito, create a demo user using a real controlled email and let Cognito deliver a temporary password. Do not put passwords in shell history, repo files, screenshots, or documentation. Sign in through the UI and complete the new-password challenge. Provision a second controlled user for ownership verification. Public self-signup is disabled.

## Smoke test and diagnosis

1. Verify unauthenticated `/health` works and `/runs` rejects missing JWTs.
2. Sign in, submit the photo-processing sample, and inspect QUEUED/RUNNING/terminal status, both tool observations, the 7,200 calculation, cited source IDs, and BEDROCK mode after actual invocation.
3. In a temporary authenticated test session, verify user B receives 404 for user A's run and steps. Do not save tokens in artifacts.
4. Inspect DynamoDB META/STEP items and TTL, worker logs, queue and DLQ metrics, and CloudWatch alarm states. Stack outputs identify functions and groups.
5. Capture actual screenshots and update verification status only after the above succeeds.

Mock marker prompts demonstrate deterministic failure locally; they are not guaranteed to control a live language model. Live agent step limits and tool validation remain enforced by the controller.

Enqueue failures return 503 and persist a terminal failure. Model/tool errors produce sanitized terminal states. Infrastructure failures can retry to DLQ. A crash after claim may strand a RUNNING record; automatic stale-run recovery is deliberately deferred. CloudWatch alarms have no outbound notification subscription in this compact version.

## Shutdown

Use [the complete teardown playbook](aws-deploy-teardown.md). Remove separately created Amplify hosting, destroy this backend stack, explicitly handle retained DynamoDB data, then run read-only inventory. Never remove shared CDK bootstrap resources.
