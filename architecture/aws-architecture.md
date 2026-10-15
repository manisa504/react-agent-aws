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
