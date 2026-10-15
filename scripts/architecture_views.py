"""Additional editable views, grounded in the application and CDK source."""

import xml.etree.ElementTree as ET

CATALOG = [
    (
        "AWS Architecture",
        "aws-architecture",
        "System topology",
        "Deployed AWS services and their integration boundaries.",
        "infra/lib/workbench-stack.ts",
    ),
    (
        "Run lifecycle",
        "aws-run-lifecycle",
        "Request lifecycle",
        "From SRP sign-in to HTTP 202, concurrent polling and a cited answer.",
        "backend/app/api.py · frontend/src/hooks/useRunPolling.ts",
    ),
    (
        "Execution modes",
        "execution-modes",
        "Three execution modes",
        "Static JavaScript fixtures, local Python MOCK, and real AWS execution.",
        "docs/demo.js · scripts/dev.py · backend/app/worker.py",
    ),
    (
        "Authentication and isolation",
        "auth-isolation",
        "Authentication & isolation",
        "Token validation, trusted subject extraction and ownership checks on every read.",
        "backend/app/auth.py · backend/app/api.py",
    ),
    (
        "Submission and queue",
        "submission-queue",
        "Submission & asynchronous work",
        "The fast submission path, SQS handoff and conditional worker claim.",
        "backend/app/api.py · backend/app/worker.py",
    ),
    (
        "Agent control",
        "agent-control",
        "Bounded agent controller",
        "Typed tools, sequential native batches, real observations and validated completion.",
        "backend/app/agent.py · backend/app/bedrock_client.py",
    ),
    (
        "Persistence",
        "data-persistence",
        "Persistence & evidence model",
        "META ownership, ordered STEP records, strongly consistent reads and TTL.",
        "backend/app/dynamo.py · backend/app/models.py",
    ),
    (
        "Failures and delivery",
        "failure-recovery",
        "Failures, duplicates & recovery",
        "Handled agent failures versus delivery retries, and the explicit recovery gap.",
        "backend/app/agent.py · backend/app/worker.py",
    ),
    (
        "Build and deployment",
        "delivery-pipeline",
        "Build, deploy & offboard",
        "CI, GitHub Pages and Amplify automation; manual CDK backend deployment.",
        ".github/workflows · amplify.yml · infra/bin/app.ts",
    ),
]


def append_functional_views(mx):
    def create(name, title, subtitle):
        page = ET.SubElement(
            mx, "diagram", id=name.lower().replace(" ", "-"), name=name
        )
        graph = ET.SubElement(
            page,
            "mxGraphModel",
            dx="2800",
            dy="1600",
            grid="1",
            gridSize="10",
            page="1",
            pageWidth="2400",
            pageHeight="1400",
        )
        root = ET.SubElement(graph, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")

        def box(id, text, x, y, w=420, h=170, kind="card"):
            styles = {
                "card": "rounded=1;fillColor=#FFFFFF;strokeColor=#CAD3E0;fontColor=#142135;spacing=22;fontSize=25;",
                "dark": "rounded=1;fillColor=#142135;strokeColor=#142135;fontColor=#FFFFFF;spacing=22;fontSize=25;",
                "note": "rounded=1;fillColor=#E9F4F4;strokeColor=#8ABDBA;fontColor=#164B4B;spacing=22;fontSize=23;align=left;",
                "error": "rounded=1;fillColor=#FFF1EB;strokeColor=#DF967E;fontColor=#803B2C;spacing=22;fontSize=23;align=left;",
                "label": "fillColor=none;strokeColor=none;fontColor=#41536B;align=left;fontSize=25;",
                "bg": "fillColor=#F4F7FB;strokeColor=none;",
            }
            cell = ET.SubElement(
                root,
                "mxCell",
                id=id,
                value=text,
                style="html=1;whiteSpace=wrap;" + styles[kind],
                vertex="1",
                parent="1",
            )
            ET.SubElement(
                cell,
                "mxGeometry",
                x=str(x),
                y=str(y),
                width=str(w),
                height=str(h),
                attrib={"as": "geometry"},
            )
            return id

        def edge(id, a, b, label="", dashed=False, error=False, points=None, pins=""):
            attrs = dict(
                id=id,
                edge="1",
                parent="1",
                source=a,
                target=b,
                style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=3;endArrow=block;endFill=1;fontSize=22;html=1;labelBackgroundColor=#F4F7FB;verticalAlign=bottom;strokeColor="
                + ("#C66545;" if error else "#416A89;")
                + ("dashed=1;" if dashed else "")
                + pins,
            )
            if label:
                attrs["value"] = label
            cell = ET.SubElement(root, "mxCell", **attrs)
            geo = ET.SubElement(
                cell, "mxGeometry", relative="1", attrib={"as": "geometry"}
            )
            if points:
                arr = ET.SubElement(geo, "Array", attrib={"as": "points"})
                for x, y in points:
                    ET.SubElement(arr, "mxPoint", x=str(x), y=str(y))

        def icon(id, name, x, y, color):
            cell = ET.SubElement(
                root,
                "mxCell",
                id=id,
                value="",
                style=f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{name};strokeColor=#ffffff;fillColor={color};sketch=0;",
                vertex="1",
                parent="1",
            )
            ET.SubElement(
                cell,
                "mxGeometry",
                x=str(x),
                y=str(y),
                width="78",
                height="78",
                attrib={"as": "geometry"},
            )

        box("background", "", 0, 0, 2400, 1400, "bg")
        box("title", f"<b>{title}</b>", 70, 40, 2250, 80, "dark")
        box("subtitle", subtitle, 80, 140, 2220, 70, "label")
        box(
            "footer",
            "ReAct Workbench · Source-derived functional view · Manisha · 2026-10-15 · us-east-2",
            80,
            1320,
            2220,
            45,
            "label",
        )
        return box, edge, icon, root

    box, edge, icon, root = create(
        "Authentication and isolation",
        "Identity is validated before data is returned",
        "Cognito authenticates. API Gateway validates tokens. The application enforces run ownership.",
    )
    participants = [
        ("browser", "Browser / Amplify", 140),
        ("cognito", "Cognito / SRP", 600),
        ("gateway", "HTTP API / JWT", 1060),
        ("api", "FastAPI Lambda", 1520),
        ("db", "DynamoDB", 1980),
    ]
    for id, label, x in participants:
        box(id, label, x, 270, 310, 100, "dark")
        cell = ET.SubElement(
            root,
            "mxCell",
            id=id + "-life",
            value="",
            style="endArrow=none;strokeColor=#A9B8CA;dashed=1;strokeWidth=2;",
            edge="1",
            parent="1",
        )
        geo = ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as": "geometry"})
        ET.SubElement(
            geo, "mxPoint", x=str(x + 155), y="390", attrib={"as": "sourcePoint"}
        )
        ET.SubElement(
            geo, "mxPoint", x=str(x + 155), y="1070", attrib={"as": "targetPoint"}
        )

    def message(id, a, b, y, text, error=False):
        cell = ET.SubElement(
            root,
            "mxCell",
            id=id,
            value=text,
            edge="1",
            parent="1",
            style="endArrow=block;endFill=1;strokeWidth=3;fontSize=23;labelBackgroundColor=#F4F7FB;verticalAlign=bottom;strokeColor="
            + ("#C66545;" if error else "#416A89;"),
        )
        geo = ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as": "geometry"})
        for x, tag in [(a, "sourcePoint"), (b, "targetPoint")]:
            ET.SubElement(geo, "mxPoint", x=str(x), y=str(y), attrib={"as": tag})

    for args in [
        ("m1", 295, 755, 430, "1 · SRP sign-in / password challenge"),
        ("m2", 755, 295, 530, "2 · Access JWT"),
        ("m3", 295, 1215, 640, "3 · Bearer access token"),
        ("m4", 1215, 1675, 750, "4 · Validated JWT claims"),
        ("m5", 1675, 2135, 860, "5 · Get META; compare owner_id to sub"),
        ("m6", 2135, 1675, 960, "6 · Metadata / ordered steps"),
    ]:
        message(*args)
    box(
        "claim-check",
        "<b>Trusted ownership</b><br>Owner = authorizer.jwt.claims.sub.<br>Never trust a client-supplied owner or HTTP header.",
        100,
        1130,
        1020,
        145,
        "note",
    )
    box(
        "denials",
        "<b>Denied reads</b><br>Missing JWT: 401 at the gateway.<br>Another user's run or missing ID: 404 from the API.",
        1220,
        1130,
        1060,
        145,
        "error",
    )

    box, edge, icon, _ = create(
        "Submission and queue",
        "Submission returns quickly; execution happens asynchronously",
        "POST /runs → metadata → queue → HTTP 202. Browser polling runs concurrently with the worker.",
    )
    nodes = [
        (
            "browser",
            "Browser<br><br>Task ≤ 2,000 characters<br>Steps 3–8; default 5",
            100,
            300,
        ),
        (
            "api",
            "FastAPI Lambda<br><br>Validate Pydantic request<br>Create owned QUEUED run",
            670,
            300,
        ),
        (
            "table",
            "DynamoDB META<br><br>Condition: PK not exists<br>Store task, owner and budget",
            1240,
            300,
        ),
        (
            "queue",
            "SQS queue<br><br>Message contains run_id<br>Visibility: 1,080 seconds",
            1810,
            300,
        ),
        (
            "worker",
            "Worker Lambda<br><br>Batch size 1 / timeout 180s<br>Controller deadline ≤150s",
            1810,
            790,
        ),
        (
            "claim",
            "Conditional claim<br><br>QUEUED → RUNNING<br>Duplicate claim exits",
            1240,
            790,
        ),
        (
            "controller",
            "Shared Python controller<br><br>Bedrock + validated tools<br>Persist ordered step events",
            670,
            790,
        ),
        (
            "poll",
            "Browser polling<br><br>GET run, then GET steps<br>2 seconds until terminal",
            100,
            790,
        ),
    ]
    for id, text, x, y in nodes:
        box(id, text, x, y, 460, 235)
    for i, (a, b) in enumerate(
        [
            ("browser", "api"),
            ("api", "table"),
            ("api", "queue"),
            ("queue", "worker"),
            ("worker", "claim"),
            ("claim", "controller"),
        ]
    ):
        if a == "api" and b == "queue":
            edge(
                "flow" + str(i),
                a,
                b,
                "Enqueue after META",
                points=[(900, 235), (2040, 235)],
                pins="exitX=0.5;exitY=0;entryX=0.5;entryY=0;",
            )
        else:
            edge("flow" + str(i), a, b, dashed=i == 3)
    edge(
        "polling",
        "poll",
        "api",
        "JWT on reads",
        True,
        points=[(330, 740), (610, 740), (610, 417)],
        pins="exitX=0.5;exitY=0;entryX=0;entryY=0.5;",
    )
    box(
        "response",
        "<b>HTTP 202 immediately after enqueue</b><br>Return run_id + QUEUED. No waiting for Bedrock inside the HTTP request.",
        100,
        1130,
        1030,
        135,
        "note",
    )
    box(
        "failure",
        "<b>Enqueue failure is explicit</b><br>Save FAILED / MODEL_ERROR with a safe message; return HTTP 503 and run_id.",
        1240,
        1130,
        1030,
        135,
        "error",
    )

    box, edge, icon, _ = create(
        "Agent control",
        "The agent is a bounded controller, not an unbounded conversation",
        "Each executed tool action and final answer consumes one of 3–8 available steps.",
    )
    for id, text, x, y in [
        (
            "budget",
            "1 · Budget check<br><br>Check runtime deadline<br>and remaining steps",
            100,
            290,
        ),
        (
            "model",
            "2 · Obtain model action<br><br>Converse or queued native request<br>maxTokens 1,000; temperature 0",
            900,
            290,
        ),
        (
            "validate",
            "3 · Validate<br><br>Allowlisted name + typed args<br>No arbitrary code or shell",
            1700,
            290,
        ),
        (
            "record",
            "6 · Record / repeat<br><br>Persist sanitized STEP<br>Update usage and mode",
            100,
            730,
        ),
        (
            "observe",
            "5 · Observe<br><br>Actual tool output + source IDs<br>Untrusted evidence, not instructions",
            900,
            730,
        ),
        (
            "tools",
            "4 · Execute one action<br><br>Restricted AST calculator<br>or curated knowledge search",
            1700,
            730,
        ),
    ]:
        box(id, text, x, y, 560, 235)
    for i, (a, b) in enumerate(
        [
            ("budget", "model"),
            ("model", "validate"),
            ("validate", "tools"),
            ("tools", "observe"),
            ("observe", "record"),
        ]
    ):
        edge("loop" + str(i), a, b)
    edge("repeat", "record", "budget", "Next step", True)
    box(
        "completion",
        "<b>Completion protocol</b><br>final_answer is a structured wire response, not an executable third tool.<br>Validate supported evidence, retrieved IDs and inline citations before success.",
        100,
        1080,
        1040,
        190,
        "note",
    )
    box(
        "limits",
        "<b>Safe termination</b><br>Budget → LIMIT_REACHED. Invalid tool / args, model error or deadline → FAILED.<br>Native batches serialize one request per step; raw reasoning is never persisted.",
        1220,
        1080,
        1040,
        190,
        "error",
    )

    edge(
        "final-response",
        "model",
        "completion",
        "Final answer",
        points=[(1180, 620), (785, 620), (785, 1020), (620, 1020)],
        pins="exitX=0.5;exitY=1;entryX=0.5;entryY=0;",
    )

    box, edge, icon, _ = create(
        "Persistence",
        "One table. Owned metadata. Ordered evidence.",
        "DynamoDB: partition key PK = RUN#id; sort key SK = META or STEP#000n. No scan or recent-run listing.",
    )
    box(
        "api",
        "API Lambda<br><br>PutItem / GetItem / Query<br>Owner check before metadata<br>and before reading steps",
        100,
        360,
        430,
        230,
    )
    box(
        "worker",
        "Worker Lambda<br><br>Conditional UpdateItem claim<br>GetItem / PutItem for runs<br>and ordered step events",
        100,
        820,
        430,
        230,
    )
    box(
        "table-header",
        "PK = RUN#&lt;id&gt;    |    SK     |    Record",
        770,
        280,
        1490,
        95,
        "dark",
    )
    rows = [
        (
            "META",
            "owner_id, task, max_steps, status, mode,<br>usage, final_answer, source_ids, timestamps",
        ),
        (
            "STEP#0001",
            "step_number=1, action_summary, tool_name,<br>validated tool_input, observation, source_ids",
        ),
        (
            "STEP#0002",
            "step_number=2, tool result or sanitized error<br>Events sorted by SK; at most eight steps",
        ),
        (
            "ttl",
            "Unix timestamp on each record<br>Seven-day expiration; asynchronous deletion",
        ),
    ]
    for n, (key, value) in enumerate(rows):
        box("key" + str(n), key, 770, 400 + n * 165, 350, 140, "dark")
        box("value" + str(n), value, 1140, 400 + n * 165, 1120, 140)
    edge("read", "api", "key0", "Check owner")
    edge(
        "claim",
        "worker",
        "key1",
        "Write steps",
        points=[(635, 935), (635, 635)],
        pins="exitX=1;exitY=0.5;entryX=0;entryY=0.5;",
    )
    box(
        "bounds",
        "Strongly consistent reads · Conditional create and STEP writes · RETAIN table on stack destruction · TTL does not remove a retained table",
        770,
        1110,
        1490,
        150,
        "note",
    )

    box, edge, icon, _ = create(
        "Failures and delivery",
        "Application outcomes and queue retries are different mechanisms",
        "Handled agent failures terminate the run. Infrastructure exceptions report an SQS batch item failure.",
    )
    for id, text, x, y in [
        ("queued", "QUEUED", 100, 300),
        ("running", "RUNNING", 850, 300),
        ("terminal", "SUCCEEDED / LIMIT_REACHED / FAILED", 1600, 300),
    ]:
        box(id, text, x, y, 630, 150, "dark")
    edge("claim", "queued", "running", "Atomic claim")
    edge("end", "running", "terminal", "Persist terminal result")
    box(
        "dedupe",
        "<b>Duplicate delivery</b><br>Already RUNNING or terminal → claim returns None.<br>Skip agent execution and acknowledge the record.",
        100,
        600,
        1000,
        185,
        "note",
    )
    box(
        "crash",
        "<b>Crash after claim — documented gap</b><br>Redelivery sees RUNNING and skips.<br>Record can remain stranded; no stale-run sweeper exists.",
        1230,
        600,
        1000,
        185,
        "error",
    )
    box(
        "sqs",
        "SQS delivery<br><br>1,080s visibility<br>maxReceiveCount = 5",
        100,
        950,
        460,
        230,
    )
    box(
        "exception",
        "Infrastructure exception<br><br>Worker returns messageId<br>in batchItemFailures",
        680,
        950,
        460,
        230,
    )
    box(
        "retry",
        "Retry after visibility<br><br>Re-deliver message<br>Claim still controls execution",
        1260,
        950,
        460,
        230,
    )
    box(
        "dlq",
        "SQS dead-letter queue<br><br>14-day retention<br>Depth alarm; manual investigation",
        1840,
        950,
        460,
        230,
    )
    edge("delivery", "sqs", "exception", dashed=True)
    edge("retryflow", "exception", "retry", dashed=True)
    edge("redrive", "retry", "dlq", "Exhausted", True, True)

    box, edge, icon, _ = create(
        "Build and deployment",
        "Three delivery paths, with explicit operational ownership",
        "GitHub Actions verifies changes and publishes docs. Amplify builds the live UI. CDK backend deployment is manual.",
    )
    lanes = [
        (
            "CI",
            280,
            "Git push / pull request",
            "CI: pytest + Vitest + CDK<br>lint / types / synth / packaging<br>12 evals + browser acceptance",
            "Verification artifacts<br>Executed reports / screenshots",
        ),
        (
            "Hosting",
            650,
            "main branch / website changes",
            "Pages: build docs/dist<br>Amplify: frontend npm build<br>Public build variables only",
            "GitHub Pages: static portfolio + demo<br>Amplify: authenticated live UI",
        ),
        (
            "Infrastructure",
            1020,
            "Manual review / target verification",
            "cdk diff → approved deployment<br>Packaged API + worker Lambdas<br>Cognito / DynamoDB / SQS / API",
            "Scoped IAM / restricted CORS<br>CloudWatch logs + alarms",
        ),
    ]
    for index, (name, y, a, b, c) in enumerate(lanes):
        box("lane" + str(index), name, 70, y - 70, 2220, 55, "label")
        for col, text in enumerate([a, b, c]):
            box(f"n{index}-{col}", text, 100 + col * 770, y, 650, 210)
        edge("e" + str(index), f"n{index}-0", f"n{index}-1")
        edge("f" + str(index), f"n{index}-1", f"n{index}-2")
