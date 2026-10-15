# AWS deployment

## Preconditions

The chosen target is account `263429641790` (provided account ARN: `arn:aws:account::263429641790:account`), `AWS_PROFILE=research`, `AWS_REGION=us-east-2`. The account ARN identifies the destination; it does not provide credentials or an assumable role. Before any resource creation, authenticate with `aws login --profile research --region us-east-2`, then verify identity. Never commit credentials, passwords, or tokens. The root README records whether live deployment has actually been verified.

```sh
export AWS_PROFILE=research AWS_REGION=us-east-2
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

This account is the AWS Projects “Hold My Coffee” project. Its home Region is **US East (Ohio), `us-east-2`**, as supplied by the owner and corroborated by successful regional service checks. AWS manages organization guardrails in this experience. Earlier service denials were observed in `us-east-1`; they did not establish a general service restriction or a need to activate advanced features. See [AWS Projects Regions](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html) and [managed project policies](https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html).

Read checks succeeded in Ohio for Lambda, DynamoDB, SQS, API Gateway, Cognito, Amplify and CloudFormation. The first inventory found no project resources or CDK bootstrap stack in Ohio. CDKToolkit has since been bootstrapped and ReActWorkbenchStack deployed successfully. Nova Lite is ACTIVE, supports ON_DEMAND in this Region, and reports AUTHORIZED/AVAILABLE. This catalogue check alone verifies control-plane availability; see the verification record for executed live requests. Prefer the in-region model `amazon.nova-lite-v1:0` with invocation resource `arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-lite-v1:0`; live tool behavior and ownership checks have now passed; see [verification](verification.md).

The owner reported a Free plan and credits. Do not activate advanced features, modify managed SCPs, or upgrade the plan automatically. If a concrete operation is restricted in the home Region, report that exact failure and consult the corresponding Projects documentation before proposing an account change. No separate human organization administrator is assumed.

## Model selection and inference estimate

The read-only Ohio model catalogue reports in-region ON_DEMAND support for Nova Lite. Use `BEDROCK_MODEL_ID=amazon.nova-lite-v1:0` and `BEDROCK_RESOURCE_ARNS='["arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-lite-v1:0"]'`. The adapter sends the Nova-supported tool-schema subset while retaining full Pydantic validation in the application. The adapter uses the `final_answer` wire schema as a structured completion signal; it adds no executable capability. Only calculator and knowledge search can execute. Native batched tool requests execute sequentially, one controller step each; they cannot exceed the run budget. Completion mixed with tool requests and malformed completion data fail closed. See [Nova structured outputs](https://docs.aws.amazon.com/nova/latest/userguide/concept-chapter-servicename.html).

The AWS Price List API returned Ohio on-demand rates of **$0.00006 per 1,000 input tokens** and **$0.00024 per 1,000 output tokens** for Nova Lite. An illustrative ten-run demo with five calls per run, 4,000 input tokens and 1,000 output tokens per call costs **$0.024 for model inference**, calculated programmatically. This is an assumption-based example, not an observed usage total or a cap. Hosting/builds, Lambda, API requests, storage, queues, logs and alarms are additional. Review the owner-reported Free-plan balance in AWS Settings; it has not been independently verified. The Pricing API uses a separate supported global endpoint; this does not change the deployment home Region. [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/).

## Git and Amplify preparation

Use the supplied repository `https://github.com/manisa504/react-agent-aws`. It was empty and publicly readable when checked. The local checkout is connected to this repository as `origin`; push the implementation after GitHub authentication. Preserve its current visibility unless the owner requests a change; do not include the surrounding source zip, `.env`, `.venv`, `node_modules`, `.build`, or AWS outputs. If using GitHub CLI, install and authenticate it first with browser authorization. Otherwise create the repository through GitHub's UI and use standard Git authentication.

The owner connected Amplify app `ds93i2ygk81q9` to this repository and `main` in Ohio. Its origin is `https://main.ds93i2ygk81q9.amplifyapp.com`. For a fresh deployment, connect the repository manually and select the main branch. Configure the monorepo root as `frontend` (`AMPLIFY_MONOREPO_APP_ROOT=frontend`); the committed `amplify.yml` defines npm installation, build, artifacts, and caching. Record the assigned Amplify origin and App ID before deploying the backend. An initial build may show the unconfigured sign-in state until outputs are supplied.

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
VITE_REGION=us-east-2
VITE_USER_POOL_ID=<UserPoolId>
VITE_USER_POOL_CLIENT_ID=<UserPoolClientId>
```

These are public configuration, not secrets. Rebuild Amplify. The deployed app preserves Amplify's `/<*>` → `/index.html` fallback with status `404-200`; existing assets are served normally. For a fresh app, configure a documented SPA fallback and verify direct `/app` navigation and refresh. See [SPA redirects](https://docs.aws.amazon.com/amplify/latest/userguide/redirect-rewrite-examples.html).

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

## Verified deployment record

On October 15, 2026, the stack deployed in Ohio and the connected Amplify build succeeded. The hosted URL is https://main.ds93i2ygk81q9.amplifyapp.com/app. Cognito access-token authentication, both Bedrock tools, cited answers, persistent ordered steps, and cross-user denial passed actual checks. See [executed verification](verification.md) for reported token usage and the genuine screenshot. Local output and resource inventory files remain under ignored `.build/`; refresh inventory before any separately approved teardown. No Free-plan, advanced-feature, or managed-SCP setting was changed.
