# ReAct Agent Workbench — AWS architecture

[Editable source](aws-architecture.drawio) · [SVG export](aws-architecture.svg)

1. Amplify serves React. Cognito authenticates the user through SDK sign-in.
2. The browser sends an access JWT to API Gateway. Its JWT authorizer protects run routes.
3. API Lambda validates the task, writes QUEUED metadata to DynamoDB, sends a run ID to SQS, and returns HTTP 202.
4. SQS invokes worker Lambda with batch size one. A conditional write claims only QUEUED records.
5. The worker runs the bounded controller, invokes Bedrock Converse, and validates tool calls before executing calculator or curated search.
6. Each action and terminal result is persisted. The browser polls until terminal; CloudWatch receives operational logs and monitors worker errors and DLQ depth.

The table is retained on destroy; Amplify has its own lifecycle. SQS retries are at least once, and crashes after claiming can leave a RUNNING record. Default five, maximum eight steps; worker timeout 180 seconds; visibility timeout 1,080 seconds. There are no VPC/NAT, vector storage, browsing tools, or extra agents.

Diagram icons use draw.io's AWS stencil library. Regenerate with `.venv/bin/python scripts/update_diagram.py`, then export with `drawio -x -f svg -o architecture/aws-architecture.svg architecture/aws-architecture.drawio`. Export a PNG and inspect it after changes. This diagram reflects the backend deployed in Ohio and its connected Amplify frontend. Executed model and browser results are recorded separately in [verification](../docs/verification.md).


## Draw.io pages and source correspondence

The original three views remain available. The editable master now contains nine views; see the functional atlas below. The original views are:

1. **AWS Architecture:** deployed service topology, including Cognito, the two Lambdas, SQS/DLQ, DynamoDB, in-region Nova Lite and CloudWatch.
2. **Run lifecycle:** sign-in, JWT authorization, HTTP 202 submission, conditional claim, bounded tool loop, final validation and concurrent polling. [SVG export](aws-run-lifecycle.svg).
3. **Execution modes:** the static GitHub Pages playground, local FastAPI MOCK runtime, and live AWS application. [SVG export](execution-modes.svg).

The diagram was checked against `infra/lib/workbench-stack.ts`, `backend/app/api.py`, `worker.py`, `agent.py`, `dynamo.py`, `bedrock_client.py`, and the frontend authentication/polling hooks. API ownership comes from the verified JWT subject. DynamoDB uses `RUN#id` / `META` and ordered `STEP#000n` keys. The worker serializes native tool batches, counts each action against the budget, and validates final citation IDs. Queue delivery is at least once; failed infrastructure records can retry, while a claimed worker crash can strand a RUNNING run.

The portfolio and scripted playground are separate static files served by GitHub Pages. They never authenticate to Cognito or call the live run API. The local application uses the real Python tools and controller with FakeModel, whereas the static playground reproduces the interface with JavaScript fixtures. The live application remains on Amplify.

Draw.io v27 and later use **1-based** CLI page indexes. Regenerate and export all three pages:

```sh
.venv/bin/python scripts/update_diagram.py
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f svg -p 1 -o architecture/aws-architecture.svg architecture/aws-architecture.drawio
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f svg -p 2 -o architecture/aws-run-lifecycle.svg architecture/aws-architecture.drawio
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f svg -p 3 -o architecture/execution-modes.svg architecture/aws-architecture.drawio
```

Export PNGs and visually inspect all pages when changing layout. Earlier draw.io versions used 0-based indexes; check the installed CLI before exporting.


## Functional atlas (nine source-derived views)

| View | Source implementation | Drawing |
| --- | --- | --- |
| Deployed topology | CDK constructs, IAM and integrations | [SVG](aws-architecture.svg) / [master draw.io](aws-architecture.drawio) |
| Request lifecycle | API, worker and polling hooks | [SVG](aws-run-lifecycle.svg) / [draw.io](aws-run-lifecycle.drawio) |
| Execution modes | Static fixtures, local dispatcher, AWS worker | [SVG](execution-modes.svg) / [draw.io](execution-modes.drawio) |
| Authentication / owner isolation | auth.py and API owned() checks | [SVG](auth-isolation.svg) / [draw.io](auth-isolation.drawio) |
| Submission / queue | API create() and worker handler() | [SVG](submission-queue.svg) / [draw.io](submission-queue.drawio) |
| Agent control | agent.py and bedrock_client.py | [SVG](agent-control.svg) / [draw.io](agent-control.drawio) |
| Data / evidence persistence | dynamo.py and models.py | [SVG](data-persistence.svg) / [draw.io](data-persistence.drawio) |
| Failure / recovery | Worker partial batch failures and conditional claims | [SVG](failure-recovery.svg) / [draw.io](failure-recovery.drawio) |
| Build / deploy | GitHub Actions, Amplify build, manual CDK | [SVG](delivery-pipeline.svg) / [draw.io](delivery-pipeline.drawio) |

Regenerate the master, standalone sources and catalog, then export every view:

```sh
.venv/bin/python scripts/update_diagram.py
.venv/bin/python scripts/export_diagrams.py --png
```

`export_diagrams.py` exports the standalone sources at page one to avoid carrying multipage viewport state into later exports. PNG review files stay under ignored `.build/`; SVGs and editable sources are committed. The CLI binary can be overridden with `--binary`. `catalog.json` supplies the website's visible gallery and source labels.

Authentication is a sequence view; persistence is a record layout; failure/recovery distinguishes application outcomes from SQS delivery behavior. They are separate explanations of real functionality, rather than copies of the same topology. The portfolio's hero is a simplified hand-authored SVG drawing; the detailed draw.io atlas is authoritative for integration semantics.
