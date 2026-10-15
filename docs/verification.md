# Verification record

Executed on October 15, 2026, locally and against the deployed AWS application in Ohio. The implementation is on `main` at [manisa504/react-agent-aws](https://github.com/manisa504/react-agent-aws). Cognito authentication, real Bedrock inference, persisted steps, and cross-user isolation were verified. See the live evidence below.

| Check | Executed result |
| --- | --- |
| `make setup` | PASS: virtual environment and both npm lockfiles installed |
| `make verify` | PASS: complete automated local gate |
| Python pytest | 50 passed |
| Frontend Vitest | 14 passed, including terminal polling, reconnection and abort behavior |
| CDK assertions | 1 passed, covering resource counts, authentication, CORS, retention and worker bounds |
| Deterministic evaluations | 12/12 passed; generated report under backend/evals/report.json |
| Python lint / frontend lint / TypeScript | PASS |
| Frontend production build | PASS |
| Lambda package | PASS: Linux x86_64 CPython 3.12 wheels and application assets |
| Linux container imports | PASS: FastAPI, Pydantic, Mangum, boto3 and application initialization |
| CDK synth, strict/no-lookups | PASS; target account 263429641790 in us-east-2 |
| Ohio CDK diff, no change set | PASS; actual Nova Lite ARN and Amplify origin reviewed; subsequent code-only updates deployed successfully |
| Documentation build | PASS: local links validated, draw.io and SVG XML |
| Development API smoke | PASS: five scenarios, routes, proxy and validation |
| Development Chrome E2E | 2 passed; success/citations, bounds/errors, refresh and 320px layout |
| Standalone showcase in Chrome | PASS: screenshot/diagram load, no missing local assets, 320px layout |

Production preview API smoke and both Chrome E2E tests passed after the final build. An earlier production browser attempt failed because a concurrent verification build replaced the served assets with cloud-mode configuration. The final check is run sequentially after rebuilding local preview. Do not rebuild `frontend/dist` in another process while testing `make preview`.

`workbench-local.png` and `workbench-mobile.png` show actual local MOCK execution. `workbench-cloud.png` shows the actual Amplify application with a successful Bedrock run using a temporary test identity. Mock evaluations do not measure Bedrock accuracy or establish general prompt-injection immunity.

The twelve fixtures cover four successful two-tool runs, three unsupported cases, two bounded loops, two invalid/tool-error runs, and one injected-observation case. Unit tests additionally cover input/tool schemas, numeric bounds, redaction, owner isolation, duplicate claims, deadlines and malformed model responses. SDK tests use mocked Bedrock and Moto DynamoDB, not AWS services.

Nonblocking dependency deprecation notices were emitted by Starlette/AnyIO and botocore under Python 3.12. Application tests pass. No test result or screenshot is fabricated.

## GitHub verification

The supplied repository is public. The implementation was pushed without changing its visibility. GitHub Actions runs the committed CI workflow; see [workflow runs](https://github.com/manisa504/react-agent-aws/actions/workflows/ci.yml) for the authoritative remote status. The local commit author uses the authenticated GitHub account and its noreply email.

## AWS Projects home Region correction

The owner identified the project home Region as `us-east-2` (Ohio). Read-only checks in Ohio succeeded for Lambda, DynamoDB, SQS, API Gateway, Cognito, Amplify, and CloudFormation. Earlier `us-east-1` denials did not establish a general service restriction. No advanced-feature activation, SCP edit, or plan upgrade is required by the successful read checks, and none was performed. AWS CLI defaults and project code/documentation now use Ohio.

## Executed live AWS verification

- Target account `263429641790`, profile `research`, Region `us-east-2`; identity verified before deployment. CDKToolkit bootstrap and ReActWorkbenchStack creation succeeded; latest application update reached UPDATE_COMPLETE.
- Amplify app `ds93i2ygk81q9`, branch `main`, connected to the supplied repository. Public introduction and direct `/app` navigation work at [the hosted site](https://main.ds93i2ygk81q9.amplifyapp.com).
- Public health returned 200; unauthenticated submission returned 401. CORS preflight returned 204 with exactly the Amplify origin.
- Two temporary Cognito users authenticated using SRP and access tokens. User B received 404 for user A's metadata and step endpoints. Test account creation suppressed email delivery; both temporary users were removed afterward.
- Two actual Bedrock runs succeeded: one authenticated API submission and one through the hosted React UI. Both used calculator and curated knowledge search, calculated 7,200, and cited IDs returned by real tool observations.
- Strongly consistent DynamoDB reads verified META plus every ordered STEP record for both runs, with terminal status matching the public API.
- Chrome verified hosted sign-in, submission, API CORS, successful final display, route refresh, and preserved sign-in without runtime errors. The cloud screenshot was captured from that successful browser session.
- Worker configuration reads confirmed 180-second timeout, SQS visibility 1,080 seconds, redrive count five, enabled event mapping and batch size one. Both CloudWatch alarms reported OK. No notification subscriptions or AWS Budget alert were created.

### Observed successful run usage

| Submission | Steps | Input tokens | Output tokens | Result |
| --- | --- | --- | --- | --- |
| Authenticated API | 3 | 3239 | 384 | SUCCEEDED / FINAL_ANSWER |
| Amplify browser | 5 | 4970 | 547 | SUCCEEDED / FINAL_ANSWER |

These are Bedrock-reported tokens for these two successful runs only. They exclude earlier diagnostic requests and are not a billing total. Live smoke verification is not a general model-quality benchmark. The twelve deterministic evaluations remain separate MOCK tests.

### Failures found and corrected during deployment

The first live run executed both tools but failed strict final JSON parsing. The adapter now uses Nova's structured completion schema while retaining Pydantic and citation validation. A subsequent hosted sample requested two native tools in one response and was safely rejected by the original single-request adapter. Native batches now execute sequentially, one action per controller step. Added tests prove batches cannot bypass step limits and completion cannot be mixed with pending tool requests. Both successful live runs above were executed after those corrections.

A full local verification attempt collided with a concurrently running CDK deployment's output-directory lock. It was rerun sequentially after deployment and passed. The current local resource snapshot is `.build/aws-resource-inventory.json`; stack outputs and diagnostic logs stay ignored by Git. Teardown remains a separate destructive action requiring explicit owner approval; none was performed.

After the final hosting rebuild, a fresh HTTP check exposed a 301-to-404 response from the original 404 fallback on `/app`. Hosting was corrected to use the documented extension-excluding 200 SPA rewrite, saved in `amplify-rewrites.json`. Direct navigation, static assets and browser refresh were checked again after the correction.

## Portfolio and static playground verification

On October 15, 2026, the portfolio was rebuilt as a two-page static site. A fresh screenshot was captured from the live public Amplify introduction, and another from a real local MOCK run stopping at five steps. Manisha's clean signed-in screenshot is included with provenance. Existing live Bedrock evidence remains labeled separately from the static demonstration.

The initial portfolio revision included three draw.io pages (AWS topology, cloud run lifecycle, execution modes). The subsequent visual case-study revision expands the master to nine functional views with independently editable sources and visible gallery panels. The guides distinguish concurrent polling from worker processing and document the retained table and deferred crashed-run recovery.

Executed browser checks passed at both the local site root and the `/react-agent-aws/` project subpath:

- Portfolio screenshots/diagram loaded; dialog open/close worked; no missing assets or browser errors.
- Both pages fit a 320px viewport; desktop screenshots were also captured.
- Six scripted scenarios produced the expected statuses, reasons and event counts.
- Repeated searches stopped at both three-step and eight-step limits.
- Numeric inputs produced the expected 360-image result and rejected out-of-range values.
- Task markup remained inert, empty tasks could not start, and resetting a RUNNING run prevented later events from appearing.
- After the demo's initial asset load, all network requests were blocked and every scenario still worked; no attempted runtime requests were recorded.
- `make docs-build` validated local links and parsed all three SVG exports and the multipage draw.io XML. JavaScript syntax and Python lint checks passed.

The new credential supplied for Higgsfield authenticated successfully; one conceptual illustration was generated through Recraft V4.1 and downloaded. Earlier incomplete-credential attempts returned 401. No credentials are saved in the source or bundled for visitors. Artwork is explicitly distinguished from app screenshots and architecture diagrams; see [asset provenance](assets/README.md).

GitHub Pages is enabled with HTTPS and the custom publishing workflow. See [publishing instructions](portfolio-publishing.md) and the [Pages workflow runs](https://github.com/manisa504/react-agent-aws/actions/workflows/pages.yml) for deployment status. This static publication is independent of the live Amplify application.


## Visual case-study revision

The original portfolio placed only one diagram inline and linked the additional views. The redesigned portfolio makes nine distinct source-derived drawings visible: topology, request lifecycle, execution modes, authentication/isolation, submission/queue, agent control, persistence, failures/recovery, and delivery. Every view has an SVG and editable draw.io source; the master retains all nine pages. An inline SVG drawing introduces the logical system before scrolling.

All twelve evaluation rows and both recorded live-run usage rows are rendered from the executed reports. The sanitized live snapshot is [available as JSON](assets/live-verification.json). The renderer validates fixture/result consistency, step bounds and actual retrieved citation IDs. Recorded live results remain observations from October 15; the site redesign does not create new paid model calls or claim continuous service monitoring.

Browser acceptance checks the nine-panel gallery, runtime/operations filters, full-size diagram and screenshot viewers, keyboard-operable trace tabs, result row counts, mobile layout, and all six static demo scenarios. These replace the earlier single-diagram-only portfolio checks. The complete CI and Pages workflow histories remain authoritative for the published revision.
