"""Regenerate the editable diagram. Export SVG/PNG with draw.io CLI afterward."""

import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def append_detail_pages(mx):
    def page(name, title, subtitle):
        diagram = ET.SubElement(
            mx, "diagram", id=name.lower().replace(" ", "-"), name=name
        )
        graph = ET.SubElement(
            diagram,
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

        def box(id, text, x, y, w, h, style=""):
            cell = ET.SubElement(
                root,
                "mxCell",
                id=id,
                value=text,
                vertex="1",
                parent="1",
                style="rounded=1;whiteSpace=wrap;html=1;fontSize=23;spacing=24;fillColor=#FFFFFF;strokeColor=#D6D1E5;fontColor=#252134;"
                + style,
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

        def link(id, source, target, dashed=False):
            cell = ET.SubElement(
                root,
                "mxCell",
                id=id,
                edge="1",
                parent="1",
                source=source,
                target=target,
                style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#6955A4;strokeWidth=3;endArrow=block;endFill=1;"
                + ("dashed=1;" if dashed else ""),
            )
            ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as": "geometry"})

        box(
            "background",
            "",
            0,
            0,
            2400,
            1400,
            "rounded=0;fillColor=#F5F5F5;strokeColor=none;",
        )
        box(
            "title",
            f"<b>{title}</b><br>Manisha | 2026-10-15 | {subtitle}",
            60,
            40,
            2200,
            120,
            "fillColor=none;strokeColor=none;align=left;fontSize=31;",
        )
        return box, link

    box, link = page(
        "Run lifecycle",
        "From sign-in to a cited answer",
        "Actual cloud request and worker lifecycle · us-east-2",
    )
    entries = [
        (
            "signin",
            "<b>1 · Sign in</b><br><br>Amplify Auth uses Cognito SRP.<br>Access token is held by the client.",
            80,
            260,
        ),
        (
            "jwt",
            "<b>2 · Authorize</b><br><br>HTTP API validates JWT issuer,<br>audience and required scope.",
            650,
            260,
        ),
        (
            "submit",
            "<b>3 · Submit</b><br><br>POST /runs validates ≤ 2,000 chars<br>and 3–8 steps. Persist QUEUED META.",
            1220,
            260,
        ),
        (
            "enqueue",
            "<b>4 · Enqueue</b><br><br>Send run_id to SQS.<br>Return 202 + run_id immediately.",
            1790,
            260,
        ),
        (
            "claim",
            "<b>5 · Claim</b><br><br>Worker conditionally claims<br>QUEUED → RUNNING. Skip duplicates.",
            1790,
            660,
        ),
        (
            "loop",
            "<b>6 · Decide / validate / act</b><br><br>Bedrock Converse → validate →<br>safe tool → ordered STEP. Repeat.",
            1220,
            660,
        ),
        (
            "finish",
            "<b>7 · Finish</b><br><br>Validate citation IDs. Persist final<br>status, reason and actual usage.",
            650,
            660,
        ),
        (
            "poll",
            "<b>8 · Poll / display</b><br><br>GET metadata + steps every 2s.<br>Owner check on each read; stop at terminal.",
            80,
            660,
        ),
    ]
    for id, text, x, y in entries:
        box(id, text, x, y, 490, 240)
    for index, (a, b) in enumerate(zip(entries, entries[1:])):
        link(f"flow-{index}", a[0], b[0], index in {3, 6})
    box(
        "polling-note",
        "After HTTP 202, the browser polls concurrently with worker steps 5–7; it does not wait for completion to begin polling.",
        300,
        535,
        1800,
        70,
        "fillColor=none;strokeColor=none;fontSize=23;fontColor=#6955A4;",
    )
    box(
        "states",
        "<b>Terminal states</b><br>SUCCEEDED / FINAL_ANSWER<br>LIMIT_REACHED / STEP_LIMIT<br>FAILED / UNSUPPORTED, MODEL_ERROR, TOOL_ERROR, TIMEOUT, INVALID_TOOL",
        80,
        1040,
        1060,
        250,
        "align=left;fontSize=22;",
    )
    box(
        "bounds",
        "<b>Operational bounds</b><br>Worker: 180s; controller: ≤150s; maxTokens: 1,000 per model request.<br>Native tool batches execute sequentially, one step each.<br>Enqueue failure: 503 + saved failure. Infrastructure retries: DLQ after five receives.<br>A worker crash after claim can strand RUNNING; automatic recovery is deferred.",
        1220,
        1040,
        1060,
        250,
        "align=left;fontSize=22;",
    )
    box, link = page(
        "Execution modes",
        "Three experiences. Explicit boundaries.",
        "The portfolio demo is independent of the authenticated AWS application",
    )
    modes = [
        (
            "static",
            "<b>STATIC PLAYGROUND</b><br>GitHub Pages · docs/demo.html",
            "Browser loads HTML / CSS / JS",
            "Six scripted scenarios<br>Browser-local arithmetic and events",
            "No login, API, model or database<br>Reset clears the displayed run",
            260,
        ),
        (
            "local",
            "<b>LOCAL APPLICATION</b><br>make dev / make preview",
            "Vite 127.0.0.1:5173<br>/api proxy → FastAPI :8000",
            "Fixed demo identity → memory repo<br>Background task → same controller",
            "FakeModel + real safe tools<br>API restart clears runs",
            620,
        ),
        (
            "cloud",
            "<b>LIVE AWS APPLICATION</b><br>Amplify · us-east-2",
            "Cognito → HTTP API JWT<br>API Lambda → DynamoDB / SQS",
            "SQS → claimed worker →<br>Bedrock + real safe tools",
            "Owned META + ordered STEP<br>7-day TTL; table retained on destroy",
            980,
        ),
    ]
    for id, title, start, middle, end, y in modes:
        box(
            id + "-label",
            title,
            70,
            y - 25,
            520,
            230,
            "fillColor=#EAE5F5;strokeColor=none;align=left;",
        )
        box(id + "-start", start, 650, y, 470, 180)
        box(id + "-middle", middle, 1240, y, 470, 180)
        box(id + "-end", end, 1830, y, 470, 180)
        link(id + "-flow-a", id + "-start", id + "-middle")
        link(id + "-flow-b", id + "-middle", id + "-end")


def main():
    mx = ET.Element("mxfile", host="app.diagrams.net", version="24.7.17")
    page = ET.SubElement(mx, "diagram", id="architecture", name="AWS Architecture")
    model = ET.SubElement(
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
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    def node(id, label, x, y, w, h, style):
        cell = ET.SubElement(
            root, "mxCell", id=id, value=label, style=style, vertex="1", parent="1"
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

    node(
        "background",
        "",
        0,
        0,
        2400,
        1400,
        "rounded=0;fillColor=#F5F5F5;strokeColor=none;",
    )
    node(
        "title",
        "<b>ReAct Agent Workbench — AWS architecture</b><br>Manisha | 2026-10-15 | Deployed in US East (Ohio), us-east-2",
        60,
        35,
        1200,
        75,
        "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=24;fontColor=#172033;",
    )
    node(
        "legend",
        "Solid: authenticated request / data flow     Dashed: asynchronous processing     Red: exhausted retries",
        60,
        125,
        1200,
        45,
        "text;html=1;align=left;fontSize=14;fontColor=#526078;",
    )
    node(
        "cloud",
        "AWS account · us-east-2 · no VPC / NAT",
        410,
        210,
        1810,
        1120,
        "rounded=1;fillColor=none;strokeColor=#A8B3C5;dashed=1;verticalAlign=top;align=left;spacing=18;fontSize=17;fontColor=#526078;",
    )
    nodes = [
        (
            "browser",
            "React UI<br>AWS Amplify Hosting",
            150,
            510,
            "client",
            "#5A4DC6",
            False,
        ),
        (
            "auth",
            "Amazon Cognito<br>User pool + JWT",
            530,
            255,
            "cognito",
            "#DD344C",
            True,
        ),
        (
            "api",
            "API Gateway<br>HTTP API + JWT",
            530,
            510,
            "api_gateway",
            "#E7157B",
            True,
        ),
        (
            "lambda",
            "API Lambda<br>FastAPI + Mangum",
            890,
            510,
            "lambda",
            "#ED7100",
            True,
        ),
        ("queue", "Amazon SQS<br>Async run queue", 1250, 510, "sqs", "#E7157B", True),
        (
            "worker",
            "Worker Lambda<br>Bounded ReAct loop",
            1610,
            510,
            "lambda",
            "#ED7100",
            True,
        ),
        (
            "bedrock",
            "Amazon Bedrock<br>Nova Lite · Converse",
            1970,
            510,
            "bedrock",
            "#01A88D",
            True,
        ),
        (
            "table",
            "DynamoDB<br>Run META + STEP",
            1250,
            255,
            "dynamodb",
            "#C925D1",
            True,
        ),
        ("dlq", "SQS DLQ<br>Exhausted retries", 1250, 870, "sqs", "#DD344C", True),
        (
            "tools",
            "Local tools<br>Calculator + curated search",
            1970,
            870,
            "source_code",
            "#5A6C86",
            False,
        ),
        (
            "logs",
            "CloudWatch<br>Logs + worker / DLQ alarms",
            1610,
            1170,
            "cloudwatch_2",
            "#E7157B",
            True,
        ),
    ]
    for id, label, x, y, icon, color, service in nodes:
        shape = (
            f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{icon};strokeColor=#ffffff;"
            if service
            else f"shape=mxgraph.aws4.{icon};strokeColor=none;"
        )
        node(id, "", x, y, 78, 78, f"{shape}fillColor={color};sketch=0;")
        node(
            id + "-label",
            label,
            x - 100,
            y + 88,
            278,
            65,
            "text;html=1;align=center;verticalAlign=top;whiteSpace=wrap;fontSize=17;fontColor=#172033;",
        )

    def edge(
        id,
        source,
        target,
        label="",
        vertical=False,
        up=False,
        async_path=False,
        error=False,
        points=None,
    ):
        style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;endArrow=block;endFill=1;fontSize=14;labelBackgroundColor=#F5F5F5;"
        style += "strokeColor=#DD344C;dashed=1;" if error else "strokeColor=#525D70;"
        if async_path:
            style += "dashed=1;"
        if vertical:
            style += f"exitX=0.5;exitY={0 if up else 1};entryX=0.5;entryY={1 if up else 0};align=right;"
        else:
            style += "exitX=1;exitY=0.5;entryX=0;entryY=0.5;verticalAlign=bottom;"
        attrs = {
            "id": id,
            "style": style,
            "edge": "1",
            "parent": "1",
            "source": source,
            "target": target,
        }
        if label:
            attrs["value"] = label
        cell = ET.SubElement(root, "mxCell", **attrs)
        geo = ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as": "geometry"})
        if points:
            arr = ET.SubElement(geo, "Array", attrib={"as": "points"})
            for x, y in points:
                ET.SubElement(arr, "mxPoint", x=str(x), y=str(y))

    edge("signin", "browser", "auth", "Sign in", points=[(330, 549), (330, 294)])
    edge("https", "browser", "api", "HTTPS + JWT")
    edge("invoke", "api", "lambda")
    edge("enqueue", "lambda", "queue", "Enqueue")
    edge("trigger", "queue", "worker", "Trigger", async_path=True)
    edge("model", "worker", "bedrock", "Model calls")
    edge("api-data", "lambda", "table", "Persist", points=[(1100, 549), (1100, 294)])
    edge(
        "worker-data",
        "worker",
        "table",
        "Claim / save",
        vertical=True,
        up=True,
        points=[(1649, 190), (1289, 190)],
    )
    edge("deadletter", "queue", "dlq", "Retries exhausted", vertical=True, error=True)
    edge(
        "safe-tools",
        "worker",
        "tools",
        "Validated call",
        points=[(1800, 549), (1800, 909)],
    )
    edge(
        "api-logs",
        "lambda",
        "logs",
        "Logs",
        vertical=True,
        points=[(929, 1150), (1649, 1150)],
    )
    edge("worker-logs", "worker", "logs", vertical=True)
    node(
        "limits",
        "Default 5 / maximum 8 steps · Batch size 1 · Worker 180s / SQS visibility 1080s<br>Curated knowledge, not live docs · Conditional claim is not crashed-run recovery<br>Amplify managed separately · DynamoDB retained on stack destroy",
        60,
        1050,
        800,
        160,
        "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=17;fontColor=#526078;",
    )
    routes = {
        "api-logs": (
            "exitX=1;exitY=0.75;entryX=0.5;entryY=0;",
            [(1060, 568), (1060, 1130), (1649, 1130)],
        ),
        "worker-logs": (
            "exitX=1;exitY=0.75;entryX=0.5;entryY=0;",
            [(1770, 568), (1770, 1110), (1649, 1110)],
        ),
        "deadletter": (
            "exitX=1;exitY=0.75;entryX=0.5;entryY=0;",
            [(1430, 568), (1430, 800), (1289, 800)],
        ),
        "worker-data": (
            "exitX=0.5;exitY=0;entryX=0.5;entryY=0;",
            [(1649, 190), (1289, 190)],
        ),
    }
    for cell in root.findall("mxCell"):
        if cell.get("id") in routes:
            pins, points = routes[cell.get("id")]
            style = cell.get("style")
            for key in ["exitX", "exitY", "entryX", "entryY"]:
                import re

                style = re.sub(key + r"=[^;]+;", "", style)
            cell.set("style", style + pins)
            geo = cell.find("mxGeometry")
            for child in list(geo):
                geo.remove(child)
            arr = ET.SubElement(geo, "Array", attrib={"as": "points"})
            for x, y in points:
                ET.SubElement(arr, "mxPoint", x=str(x), y=str(y))
    append_detail_pages(mx)
    ET.ElementTree(mx).write(
        ROOT / "architecture/aws-architecture.drawio",
        encoding="UTF-8",
        xml_declaration=True,
    )
    print("Updated editable draw.io architecture")


if __name__ == "__main__":
    main()
