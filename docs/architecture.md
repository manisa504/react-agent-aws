# Architecture and runtime contracts

See the [editable diagram](../architecture/aws-architecture.drawio), [SVG](../architecture/aws-architecture.svg), and [diagram guide](../architecture/aws-architecture.md).

Local mode uses a single FastAPI process with an in-memory repository and background dispatcher. Cloud mode uses an API Lambda to persist and enqueue; the SQS worker conditionally claims and calls the same bounded controller. The React client polls every two seconds and fetches steps after run status so the final observation is included before polling stops.

The public endpoint is GET `/health`. POST `/runs` accepts `{task,max_steps}` and returns HTTP 202 `{run_id,status}`. GET `/runs/{run_id}` returns status, mode, metrics and final result; GET `/runs/{run_id}/steps` returns ordered events. Run reads hide task and owner fields. Missing and other-user runs both return 404 to avoid enumeration. Owner is taken from API Gateway's trusted JWT context. Lambda has no function URL; API Gateway integration invocation is permission-scoped by CDK.

Run statuses: QUEUED, RUNNING, SUCCEEDED, LIMIT_REACHED, FAILED. Reasons: FINAL_ANSWER, STEP_LIMIT, UNSUPPORTED, MODEL_ERROR, TOOL_ERROR, TIMEOUT, INVALID_TOOL. Unsupported evidence is FAILED/UNSUPPORTED. Every decision, including final or rejected actions, consumes one step. Tool/model failures stop immediately instead of retrying indefinitely. Calculator rejects nonnumeric AST nodes and bounded-result violations. Only retrieved IDs can be cited.

Converse is client-side tool use: the model requests an action, application code validates and executes it. The final JSON is validated separately. No reasoning blocks are persisted. Model call timeouts/output and the worker's deadline bound execution. Usage is only displayed when returned by Bedrock. A queued cloud run has no claimed BEDROCK invocation; its mode becomes BEDROCK only after a completed actual model request. MOCK is the pre-invocation/default mode, not evidence of a cloud model call.

DynamoDB uses one partition per run, separate META/STEP records, and seven-day TTL. Strongly consistent reads keep the short poll trace coherent. Conditional claims prevent normal duplicate execution; they do not recover crashes after RUNNING. Tool outcomes and terminal failures acknowledge messages; infrastructure exceptions retry and can reach the DLQ. A worker Lambda error alarm covers runtime failures, not every domain-level failed run.
