"""Regenerate the editable diagram. Export SVG/PNG with draw.io CLI afterward."""

import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        "<b>ReAct Agent Workbench — AWS architecture</b><br>Manisha | 2026-10-15 | Implemented infrastructure, deployment unverified",
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
        "AWS account · us-east-1 · no VPC / NAT",
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
            "Amazon Bedrock<br>Converse tool use",
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
    edge("worker-logs", "worker", "logs", "Logs", vertical=True)
    node(
        "limits",
        "Default 5 / maximum 8 decisions · Batch size 1 · Worker 180s / SQS visibility 1080s<br>Curated knowledge, not live docs · Conditional claim is not crashed-run recovery<br>Amplify managed separately · DynamoDB retained on stack destroy",
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
    ET.ElementTree(mx).write(
        ROOT / "architecture/aws-architecture.drawio",
        encoding="UTF-8",
        xml_declaration=True,
    )
    print("Updated editable draw.io architecture")


if __name__ == "__main__":
    main()
