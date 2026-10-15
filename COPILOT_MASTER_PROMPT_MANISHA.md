# GitHub Copilot master build prompt — ReAct Planning Agent Workbench

You are an experienced full-stack AI engineer working inside this repository. Build a **complete working portfolio project for Manisha**, who is demonstrating practical AI engineering and AWS deployment. **Read `REQUIREMENTS_MANISHA.md` fully before changing files.** It is the source of truth whenever an implementation choice is ambiguous.

## Mission
Create a React/TypeScript workbench and Python bounded ReAct agent backed by Amazon Bedrock, deployed on AWS using Amplify Hosting, API Gateway HTTP API + Cognito JWT authentication, two Lambda functions (API and worker), SQS with DLQ, a single DynamoDB table, and CloudWatch. Use AWS CDK in TypeScript for backend infrastructure. Deliver a useful, polished application—not pseudocode, mock screenshots, or scaffolding with unfinished `TODO`s.

## Hard scope boundaries
- Do not add LangGraph, CrewAI, AutoGen, multiple agents, RAG/vector DB, external web browsing, real-time sockets, Step Functions, ECS, Kubernetes, EventBridge, Redis, self-reflection subagents, long-term memory, canary releases, detailed financial cost analytics, VPC/NAT, or arbitrary code execution.
- Preserve engineering fundamentals: 5 default/8 max steps, strict allowed tools, typed schemas, deterministic stopping, short action/observation trace, authentication, ownership, unit tests, deployment and cleanup.
- Use **ReAct** for agent behavior and **React** for UI. Explain difference in README.
- Provide two working tools: safe calculator (restricted arithmetic AST/parser with bounded input/operators, no Python eval) and local curated knowledge_search with source IDs. Avoid claiming curated facts are real-time AWS documentation.
- Never display chain-of-thought. Expose concise action decisions, inputs after redaction, tool outcomes and final citation IDs only.

## Build sequence (implement and verify at each gate)

### Phase 1: Repository and local execution
1. Create the exact folder structure in the requirements, adjusting only where necessary for running code. Bootstrap Vite React + TS; FastAPI + Pydantic v2; install tests and formatting.
2. Define types: `Run`, `StepEvent`, `RunStatus`, `TerminationReason`, tool request/response models. Implement `POST /runs`, `GET /runs/{id}`, `GET /runs/{id}/steps` with dependency-injected storage so tests run without AWS.
3. Build a deterministic fake model adapter used in development/evals. Its modes include success, repeated-tool loop, invalid tool, unsupported evidence, and simulated tool exception. Clearly label mock mode throughout UI.
4. Implement `calculator` and `knowledge_search`, seeded `knowledge.json` with ~10 small curated entries and IDs.
5. Implement `run_agent` state loop as plain Python. The model returns either final response or typed tool call. Every iteration counts towards limit. Reject malformed arguments, unauthorized tool calls, and attempts to follow instructions embedded in source content. Persist each action summary, tool result, and terminal outcome. Use a bounded error result instead of infinite retries.
6. React page: sign-in state, user task entry with sample prompts, start button, status badge, ordered timeline, final answer, source refs, metrics strip and error messages. Poll with TanStack Query or a simple React hook and stop on terminal status. Responsive layout. Use a local no-auth demo ONLY when explicit local `DEMO_MODE` is enabled; cloud uses Cognito authorization.
7. Tests: pytest for controller/tool/API; Vitest for React UI; 12 deterministic fixture evaluations with a runnable script. Run them locally and fix errors before proceeding.

### Phase 2: AWS infrastructure and cloud integration
8. Implement DynamoDB repository using one table with `PK=RUN#id` and `SK=META` or `STEP#000n`; additional owner/time GSI only if implementing user run list. All API reads check owner from validated JWT. No table scans of all runs.
9. API Lambda: FastAPI through Mangum. `POST /runs` writes `QUEUED`, sends SQS message `{run_id}`, and returns HTTP 202. GET reads status/steps from DynamoDB. Handle enqueue failures explicitly to avoid silently stuck runs.
10. Worker Lambda: SQS batch size 1; atomically transition `QUEUED` to `RUNNING` with DynamoDB condition, skip already-claimed/terminal duplicates. Invoke Bedrock Converse tool use through boto3 with region/model configured by environment; validate response shape for the chosen model. Persist step events and terminal status, catch bounded errors. Explain that durable recovery of a crashed RUNNING worker is deferred, rather than claiming exactly-once execution.
11. AWS CDK v2 TypeScript stack: API Gateway HTTP API + Cognito JWT authorizer, Lambda API/worker, SQS/DLQ, one DynamoDB table, CloudWatch log groups and basic worker/DLQ alerts, least-privilege IAM, CORS restricted to frontend origin configurable, outputs for region, API URL, user pool ID/client ID and queue/table identifiers needed by ops. Choose worker timeout and SQS visibility according to AWS guidance, with batch size 1. Avoid NAT gateways/VPC. Make Lambda Python dependencies deploy correctly (bundling/layer or asset) and ensure fastapi+mangum+pydantic are packaged.
12. Cognito sign-in in React using AWS Amplify Auth library or equivalent supported approach. Configure frontend vars through build-time environment settings, no API secrets. Record how to create a test user and configure callback/allowed origins without leaking passwords.
13. Configure Amplify Hosting for Git-based frontend deployment: `frontend` app root, build commands, SPA rewrite rules, environment variables, and the manual AWS Console Git authorization step (unless an actually implemented automated provisioning path is verified). Do NOT claim CDK automatically completed GitHub/Amplify connection.
14. Provide `docs/aws-deploy.md`: prerequisites (AWS account, CLI auth, CDK bootstrap, region, Bedrock model access including Converse tools), CDK commands, frontend Amplify steps, test signup/auth, first request, logs, expected costs, AWS Budgets recommendation and clean teardown. Show secure GitHub Actions CI running tests/lint/CDK synth; leave automated AWS deploy optional rather than requiring advanced OIDC setup for MVP.

### Phase 3: Verify and polish
15. Add unit/integration assertions for 5-step termination, unknown-tool rejection, injection text treated as data, tool errors, sequential trace, fake model citations, simulated duplicate claim, and owner isolation. Produce `evals/report.json` only by running actual fixtures; never fill with invented metrics.
16. Run `pytest`, frontend tests/build, type checks and `cdk synth`. Fix actual defects. If AWS credentials/Bedrock permissions unavailable, stop before cloud deployment and explain missing prerequisites. Never claim a live AWS URL or live model invocation unless verified.
17. Create README starting with business problem, screenshot placeholder clearly labeled until screenshot exists, architecture Mermaid, setup commands, functionality, recorded eval results, constraints and trade-offs; plus `docs/demo-script.md` for a 2–3-minute showcase: success -> bounded loop -> AWS architecture -> next steps.

## Detailed behavioral contracts
- Input limit 2,000 characters. Max steps 8 (default 5). Do not support arbitrary web URLs as tools.
- Run statuses `QUEUED`, `RUNNING`, `SUCCEEDED`, `LIMIT_REACHED`, `FAILED`. Termination reasons `FINAL_ANSWER`, `STEP_LIMIT`, `UNSUPPORTED`, `MODEL_ERROR`, `TOOL_ERROR`, `TIMEOUT`, `INVALID_TOOL`.
- Bedrock ID/inference profile must be configurable and chosen after confirming model/tool support in the intended region. Do not hard-code a false access assumption or fabricating token/cost values.
- Restrict model action structure to final text with evidence IDs, or validated tool request. Evidence references in final response must be present in actual returned knowledge_search observations; label missing evidence as unsupported.
- For fake/mock mode, expose `execution_mode=MOCK` and display it clearly; `execution_mode=BEDROCK` only after actual invocation.
- Every step event contains safe timestamp, step number, action summary, tool name (if any), result/error and source IDs; no raw private reasoning or secrets.
- Prefer the simplest reliable implementation; avoid extra abstractions unless essential for tests or AWS runtime. Use typed Python and TypeScript where practical.

## Definition of done checklist
- [ ] `make setup`, `make dev`, `make test`, `make eval`, `make synth` are documented and work.
- [ ] React app connects to real API in AWS and displays queued/running/final status after Cognito login.
- [ ] A Bedrock run invokes both allowlisted tools and produces cited output (verify only if cloud access available).
- [ ] Loop stops at step limit; invalid tool rejected; cross-user read fails.
- [ ] DynamoDB steps persist; SQS worker handles claim/idempotency basics; CloudWatch logs and DLQ configured.
- [ ] CDK deploy and destroy steps are accurate, including Amplify git setup.
- [ ] 12 eval cases run with real outcomes; README explains limitations accurately.

## Operating instructions
Start by summarizing the proposed file tree and exact delivery gates (in no more than 12 lines), then **implement Phase 1 immediately**. After each phase, run and report executed commands with pass/fail status. If blocked, explain precisely what is missing and continue on work that does not require the missing input. Do not stop after creating plans. Ask the user only for truly required AWS-account-specific information or confirmation before spending money/deploying.


## Mandatory v1.2 addendum: UI, draw.io, presentation site and full teardown

Before coding, also read `docs/UI_COMPONENT_SPEC.md`, `docs/aws-deploy-teardown.md`, `README.md`, and `architecture/aws-architecture.drawio`.

1. Implement the React UI **component by component** from `docs/UI_COMPONENT_SPEC.md`, covering authentication, composer, sample prompts, status badge, execution timeline, evidence/citations and terminal/error states. Add accessibility and responsive behavior; no mock data masquerading as production results.
2. The architecture diagram must remain a true editable `architecture/aws-architecture.drawio` file. When you modify AWS architecture, update that file **and** `architecture/aws-architecture.svg` then ensure the README and `docs/index.html` show the same system diagram. If the environment has an installed draw.io skill/CLI, inspect its instructions and use it; otherwise edit valid draw.io XML and generate a synchronized export. Diagram must include both Lambdas, Amplify, Cognito, API Gateway, DynamoDB, SQS/DLQ, Bedrock, tools and CloudWatch.
3. Maintain `docs/index.html` as a high-quality static showcase (problem, feature cards, diagram, example run, AWS stack, deployment/cleanup and links to docs). It must remain usable **without any external website design API**. Add a `docs:build` command producing a publishable site in `docs/dist` (or other documented output) by copying/rebasing architecture assets; automatically check asset links. Do not quietly ship broken relative paths to GitHub Pages.
4. The sponsor may later supply an 'Expial API' for website design. **Do not assume the API contract, disclose credentials, or put an API key in the browser or Git repository.** Await official docs and implement any secrets-bearing requests on a server-side integration only after approval.
5. Deployment must include an explicit teardown checkpoint. Write commands and checks for the **actual** CDK stack, separately created Amplify Hosting app/branches, retained DynamoDB data, SQS/DLQ, Lambdas, CloudWatch groups/alarms, API Gateway and Cognito. Require confirmed `AWS_PROFILE`, `AWS_REGION` and `aws sts get-caller-identity` before any deletion. Do not automatically tear down unrelated/shared resources such as CDK bootstrap. Budget alerts are not cost caps.
6. Run `pytest`, `vitest`, `cdk synth`, HTML asset validation, draw.io XML parse, and link validation as applicable. Report executed tests and unresolved cloud permissions explicitly. Do not claim you provisioned or tore down AWS resources without executed commands and successful verification.

**Priority:** preserve a compact end-to-end build for one developer. Do not convert this into an enterprise management suite just to accommodate documentation or teardown requirements.
