"""Regenerate the editable diagram. Export SVG/PNG with draw.io CLI afterward."""

import xml.etree.ElementTree as ET
import copy
import json

from architecture_views import (
    CATALOG,
    add_icons,
    append_functional_views,
    aws_icon_style,
)
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

        def box(id, text, x, y, w, h, style="", icons=None):
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
            cell.set("style", cell.get("style") + add_icons(root, id, w, h, icons))

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
    entry_icons = {
        "signin": ["cognito"],
        "jwt": ["api_gateway"],
        "submit": ["lambda", "dynamodb"],
        "enqueue": ["sqs"],
        "claim": ["lambda", "dynamodb"],
        "loop": ["bedrock"],
        "finish": ["dynamodb"],
        "poll": ["amplify"],
    }
    for id, text, x, y in entries:
        box(id, text, x, y, 490, 240, icons=entry_icons[id])
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
        icons = {
            "static": [["client"], ["source_code"], ["source_code"]],
            "local": [["client"], ["server"], ["source_code"]],
            "cloud": [
                ["cognito", "api_gateway"],
                ["sqs", "lambda", "bedrock"],
                ["dynamodb"],
            ],
        }[id]
        box(id + "-start", start, 650, y, 470, 180, icons=icons[0])
        box(id + "-middle", middle, 1240, y, 470, 180, icons=icons[1])
        box(id + "-end", end, 1830, y, 470, 180, icons=icons[2])
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
        "Official AWS icons · Solid: request / data flow · Dashed: asynchronous processing · Red: exhausted retries",
        60,
        125,
        1200,
        45,
        "text;html=1;align=left;fontSize=14;fontColor=#526078;",
    )
    group = "points=[];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=19;fontStyle=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;verticalAlign=top;align=left;spacingLeft=40;spacingTop=6;fillColor=none;"
    node(
        "cloud",
        "AWS Cloud · single account",
        360,
        200,
        1990,
        1160,
        group
        + "grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fontColor=#232F3E;dashed=0;",
    )
    node(
        "region",
        "US East (Ohio) · us-east-2 · serverless, no VPC / NAT",
        400,
        255,
        1910,
        1075,
        group
        + "grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fontColor=#147EBA;dashed=1;",
    )
    nodes = [
        ("browser", "Users<br>Browser · React SPA", 150, 580, "users"),
        ("auth", "Amazon Cognito<br>User pool · SRP + JWT", 530, 340, "cognito"),
        (
            "api",
            "Amazon API Gateway<br>HTTP API · JWT authorizer",
            530,
            580,
            "api_gateway",
        ),
        ("hosting", "AWS Amplify Hosting<br>Static React build", 530, 880, "amplify"),
        ("lambda", "AWS Lambda · API<br>FastAPI + Mangum", 890, 580, "lambda"),
        ("table", "Amazon DynamoDB<br>Run META + STEP · TTL", 1250, 340, "dynamodb"),
        ("queue", "Amazon SQS<br>Async run queue", 1250, 580, "sqs"),
        ("dlq", "Amazon SQS DLQ<br>Exhausted retries", 1250, 880, "sqs"),
        ("worker", "AWS Lambda · Worker<br>Bounded ReAct loop", 1610, 580, "lambda"),
        ("bedrock", "Amazon Bedrock<br>Nova Lite · Converse", 1970, 580, "bedrock"),
        (
            "tools",
            "In-process tools<br>Calculator + curated search",
            1970,
            880,
            "source_code",
        ),
        ("iam", "AWS IAM<br>Least-privilege roles", 890, 1120, "iam"),
        (
            "logs",
            "Amazon CloudWatch<br>Logs + worker / DLQ alarms",
            1610,
            1120,
            "cloudwatch",
        ),
    ]
    for id, label, x, y, icon in nodes:
        node(id, "", x, y, 78, 78, aws_icon_style(icon))
        node(
            id + "-label",
            label,
            x - 76,
            y + 86,
            230,
            70,
            "text;html=1;align=center;verticalAlign=top;whiteSpace=wrap;fontSize=16;fontColor=#172033;",
        )

    def edge(
        id,
        source,
        target,
        label="",
        pins="",
        async_path=False,
        error=False,
        points=None,
    ):
        style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;endArrow=block;endFill=1;fontSize=14;labelBackgroundColor=#F5F5F5;verticalAlign=bottom;"
        style += "strokeColor=#DD344C;dashed=1;" if error else "strokeColor=#525D70;"
        if async_path:
            style += "dashed=1;"
        style += pins or "exitX=1;exitY=0.5;entryX=0;entryY=0.5;"
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

    edge(
        "signin",
        "browser",
        "auth",
        "Sign in",
        "exitX=1;exitY=0.15;entryX=0;entryY=0.5;",
        points=[(290, 592), (290, 379)],
    )
    edge("https", "browser", "api", "HTTPS + JWT")
    edge(
        "load",
        "browser",
        "hosting",
        "Load UI",
        "exitX=1;exitY=0.85;entryX=0;entryY=0.5;",
        points=[(320, 646), (320, 919)],
    )
    edge("invoke", "api", "lambda")
    edge("enqueue", "lambda", "queue", "Enqueue")
    edge("trigger", "queue", "worker", "Trigger", async_path=True)
    edge("model", "worker", "bedrock", "Model calls")
    edge(
        "api-data",
        "lambda",
        "table",
        "Persist",
        "exitX=0.5;exitY=0;entryX=0;entryY=0.5;",
        points=[(929, 379)],
    )
    edge(
        "worker-data",
        "worker",
        "table",
        "Claim / save",
        "exitX=0.5;exitY=0;entryX=1;entryY=0.5;",
        points=[(1649, 379)],
    )
    edge(
        "deadletter",
        "queue",
        "dlq",
        "Retries exhausted",
        "exitX=1;exitY=0.85;entryX=0.5;entryY=0;",
        error=True,
        points=[(1430, 646), (1430, 830), (1289, 830)],
    )
    edge(
        "safe-tools",
        "worker",
        "tools",
        "Validated call",
        "exitX=1;exitY=0.75;entryX=0;entryY=0.5;",
        points=[(1860, 638), (1860, 919)],
    )
    edge(
        "api-logs",
        "lambda",
        "logs",
        "Logs",
        "exitX=1;exitY=0.85;entryX=0;entryY=0.5;",
        points=[(1070, 646), (1070, 1159)],
    )
    edge(
        "worker-logs",
        "worker",
        "logs",
        "",
        "exitX=1;exitY=0.95;entryX=0.75;entryY=0;",
        points=[(1800, 654), (1800, 1070), (1668, 1070)],
    )
    node(
        "limits",
        "<b>Bounds</b><br>Default 5 / max 8 steps<br>SQS batch size 1<br>Worker 180s · visibility 1,080s<br>Curated knowledge, not live docs<br>Claim is not crashed-run recovery<br>DynamoDB retained on destroy",
        40,
        820,
        300,
        300,
        "text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;fontSize=15;fontColor=#526078;",
    )
    append_detail_pages(mx)
    append_functional_views(mx)
    ET.ElementTree(mx).write(
        ROOT / "architecture/aws-architecture.drawio",
        encoding="UTF-8",
        xml_declaration=True,
    )
    catalog = []
    for index, (name, slug, title, description, source) in enumerate(CATALOG):
        page = mx.findall("diagram")[index]
        standalone = ET.Element("mxfile", host="app.diagrams.net")
        standalone.append(copy.deepcopy(page))
        if slug != "aws-architecture":
            ET.ElementTree(standalone).write(
                ROOT / f"architecture/{slug}.drawio",
                encoding="UTF-8",
                xml_declaration=True,
            )
        catalog.append(
            {
                "index": index + 1,
                "slug": slug,
                "title": title,
                "description": description,
                "source": source,
            }
        )
    (ROOT / "architecture/catalog.json").write_text(
        json.dumps(catalog, indent=2) + "\n"
    )
    print(f"Updated master draw.io and {len(catalog)} independently editable views")


if __name__ == "__main__":
    main()
