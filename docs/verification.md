# Verification record

Executed locally on October 15, 2026. These results concern the implemented local application and synthesized infrastructure. The implementation was uploaded to `manisa504/react-agent-aws` on `main` (initial implementation commit `8bfe71b`). GitHub authentication and the remote push are verified. No live AWS resources or Bedrock invocation have been verified.

| Check | Executed result |
| --- | --- |
| `make setup` | PASS: virtual environment and both npm lockfiles installed |
| `make verify` | PASS: complete automated local gate |
| Python pytest | 46 passed |
| Frontend Vitest | 14 passed, including terminal polling, reconnection and abort behavior |
| CDK assertions | 1 passed, covering resource counts, authentication, CORS, retention and worker bounds |
| Deterministic evaluations | 12/12 passed; generated report under backend/evals/report.json |
| Python lint / frontend lint / TypeScript | PASS |
| Frontend production build | PASS |
| Lambda package | PASS: Linux x86_64 CPython 3.12 wheels and application assets |
| Linux container imports | PASS: FastAPI, Pydantic, Mangum, boto3 and application initialization |
| CDK synth, strict/no-lookups | PASS; target account 263429641790 in us-east-2 |
| Ohio CDK diff, no change set | PASS; new stack compared against the authenticated account, using Nova Lite and a placeholder frontend origin pending Amplify connection |
| Documentation build | PASS: 58 local links, draw.io and SVG XML |
| Development API smoke | PASS: five scenarios, routes, proxy and validation |
| Development Chrome E2E | 2 passed; success/citations, bounds/errors, refresh and 320px layout |
| Standalone showcase in Chrome | PASS: screenshot/diagram load, no missing local assets, 320px layout |

Production preview API smoke and both Chrome E2E tests passed after the final build. An earlier production browser attempt failed because a concurrent verification build replaced the served assets with cloud-mode configuration. The final check is run sequentially after rebuilding local preview. Do not rebuild `frontend/dist` in another process while testing `make preview`.

The screenshots under `docs/assets` are generated from the actual local application. They show MOCK inference, not a hosted or live Bedrock result. Mock evaluations do not measure Bedrock accuracy or establish general prompt-injection immunity.

The twelve fixtures cover four successful two-tool runs, three unsupported cases, two bounded loops, two invalid/tool-error runs, and one injected-observation case. Unit tests additionally cover input/tool schemas, numeric bounds, redaction, owner isolation, duplicate claims, deadlines and malformed model responses. SDK tests use mocked Bedrock and Moto DynamoDB, not AWS services.

Nonblocking dependency deprecation notices were emitted by Starlette/AnyIO and botocore under Python 3.12. Application tests pass. No test result or screenshot is fabricated.

## GitHub verification

The supplied repository is public. The implementation was pushed without changing its visibility. GitHub Actions runs the committed CI workflow; see [workflow runs](https://github.com/manisa504/react-agent-aws/actions/workflows/ci.yml) for the authoritative remote status. The local commit author uses the authenticated GitHub account and its noreply email.

## AWS Projects home Region correction

The owner identified the project home Region as `us-east-2` (Ohio). Read-only checks in Ohio succeeded for Lambda, DynamoDB, SQS, API Gateway, Cognito, Amplify, and CloudFormation. Earlier `us-east-1` denials did not establish a general service restriction. No advanced-feature activation, SCP edit, or plan upgrade is required by the successful read checks, and none was performed. AWS CLI defaults and project code/documentation now use Ohio.

## Cloud prerequisites still outstanding

- AWS authentication succeeds for account `263429641790` using profile `research`. The Ohio CloudFormation stack list was empty, and the standard CDK bootstrap version parameter was absent; prepare bootstrap for Ohio after reviewing its resources.
- In Ohio, `amazon.nova-lite-v1:0` is ACTIVE, lists ON_DEMAND support, and reports AUTHORIZED/AVAILABLE. Configure its exact regional invocation ARN and verify an actual tool-using run before claiming live inference.
- Finish Amplify's Git authorization and supply its real origin.
- Review the actual CDK diff/account/model/costs at the required deployment approval checkpoint, then deploy and execute authenticated live smoke/ownership checks.

No AWS provisioning, deletion, or paid inference was executed. The [AWS deployment](aws-deploy.md) and [teardown](aws-deploy-teardown.md) guides describe those remaining operations accurately.
