# Verification record

Executed locally on October 15, 2026. These results concern the implemented local application and synthesized infrastructure. No live AWS resources, Bedrock invocation, or GitHub upload have been verified.

| Check | Executed result |
| --- | --- |
| `make setup` | PASS: virtual environment and both npm lockfiles installed |
| `make verify` | PASS: complete automated local gate |
| Python pytest | 45 passed |
| Frontend Vitest | 14 passed, including terminal polling, reconnection and abort behavior |
| CDK assertions | 1 passed, covering resource counts, authentication, CORS, retention and worker bounds |
| Deterministic evaluations | 12/12 passed; generated report under backend/evals/report.json |
| Python lint / frontend lint / TypeScript | PASS |
| Frontend production build | PASS |
| Lambda package | PASS: Linux x86_64 CPython 3.12 wheels and application assets |
| Linux container imports | PASS: FastAPI, Pydantic, Mangum, boto3 and application initialization |
| CDK synth, strict/no-lookups | PASS; target account 263429641790, placeholder model/origin for local synthesis |
| Documentation build | PASS: 58 local links, draw.io and SVG XML |
| Development API smoke | PASS: five scenarios, routes, proxy and validation |
| Development Chrome E2E | 2 passed; success/citations, bounds/errors, refresh and 320px layout |
| Standalone showcase in Chrome | PASS: screenshot/diagram load, no missing local assets, 320px layout |

Production preview API smoke and both Chrome E2E tests passed after the final build. An earlier production browser attempt failed because a concurrent verification build replaced the served assets with cloud-mode configuration. The final check is run sequentially after rebuilding local preview. Do not rebuild `frontend/dist` in another process while testing `make preview`.

The screenshots under `docs/assets` are generated from the actual local application. They show MOCK inference, not a hosted or live Bedrock result. Mock evaluations do not measure Bedrock accuracy or establish general prompt-injection immunity.

The twelve fixtures cover four successful two-tool runs, three unsupported cases, two bounded loops, two invalid/tool-error runs, and one injected-observation case. Unit tests additionally cover input/tool schemas, numeric bounds, redaction, owner isolation, duplicate claims, deadlines and malformed model responses. SDK tests use mocked Bedrock and Moto DynamoDB, not AWS services.

Nonblocking dependency deprecation notices were emitted by Starlette/AnyIO and botocore under Python 3.12. Application tests pass. No test result or screenshot is fabricated.

## Cloud prerequisites still outstanding

- The AWS browser authorization timed out without completing. Restart `aws login --profile research --region us-east-1`, finish browser authorization, then verify that Account is `263429641790` and inspect the authenticated Arn.
- Complete GitHub CLI browser authorization, configure commit author metadata from the authenticated account, then push to the supplied `manisa504/react-agent-aws` repository. Its empty remote was verified and `origin` is configured; no upload has occurred.
- Verify regional Bedrock model/tool access and actual pricing; configure exact invocation ARNs.
- Finish Amplify's Git authorization and supply its real origin.
- Review the actual CDK diff/account/model/costs at the required deployment approval checkpoint, then deploy and execute authenticated live smoke/ownership checks.

No AWS provisioning, deletion, or paid inference was executed. The [AWS deployment](aws-deploy.md) and [teardown](aws-deploy-teardown.md) guides describe those remaining operations accurately.
