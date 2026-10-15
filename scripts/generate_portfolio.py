"""Render the visual portfolio from committed, executed evidence and diagram sources."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render():
    catalog = json.loads((ROOT / "architecture/catalog.json").read_text())
    report = json.loads((ROOT / "backend/evals/report.json").read_text())
    live = json.loads((ROOT / "docs/assets/live-verification.json").read_text())
    cases = json.loads((ROOT / "backend/evals/cases.json").read_text())
    expected = {case["id"]: case for case in cases}
    assert report["total"] == len(report["results"]) == len(cases)
    assert report["passed"] == sum(item["passed"] for item in report["results"])
    assert {item["id"] for item in report["results"]} == set(expected)
    for result in report["results"]:
        case = expected[result["id"]]
        assert result["steps_used"] <= case.get("max_steps", 5)
        if result["passed"]:
            assert result["termination_reason"] == case["expected_reason"]
    for run in live["runs"]:
        assert run["execution_mode"] == "BEDROCK" and run["status"] == "SUCCEEDED"
        assert run["token_usage"]["input"] > 0 and run["token_usage"]["output"] > 0
        actual_ids = {
            source
            for event in run["events"]
            if event["tool"]
            for source in event["source_ids"]
        }
        assert set(run["source_ids"]).issubset(actual_ids)
        assert len(run["events"]) == run["steps_used"] <= run["max_steps"]
        assert [event["number"] for event in run["events"]] == list(
            range(1, run["steps_used"] + 1)
        )
    escape = html.escape
    cards = []
    for item in catalog:
        cards.append(f'''<article class="atlas-card" id="view-{item["slug"]}">
<div class="atlas-image"><img src="../architecture/{item["slug"]}.svg" loading="lazy" alt="{escape(item["title"])}: {escape(item["description"])}"></div>
<div class="atlas-copy"><span class="mono">VIEW {item["index"]:02d}</span><h3>{escape(item["title"])}</h3><p>{escape(item["description"])}</p>
<div class="atlas-links"><button type="button" data-diagram="{item["slug"]}" data-title="{escape(item["title"])}">Explore diagram ↗</button><a href="../architecture/{item["slug"]}.svg">SVG</a><a href="../architecture/{item["slug"]}.drawio" download>draw.io</a></div><small>Source: {escape(item["source"])}</small></div></article>''')
    rows = "".join(
        f"<tr><td>{escape(x['id'])}</td><td><span class='pass'>{'PASS' if x['passed'] else 'FAIL'}</span></td><td>{escape(x['status'])}</td><td>{escape(x['termination_reason'])}</td><td>{x['steps_used']}</td></tr>"
        for x in report["results"]
    )
    live_rows = "".join(
        f"<tr><td>{label}</td><td>{x['steps_used']} / {x['max_steps']}</td><td>{x['token_usage']['input']:,}</td><td>{x['token_usage']['output']:,}</td><td><span class='pass'>{x['status']}</span></td></tr>"
        for label, x in zip(["Authenticated API", "Amplify browser"], live["runs"])
    )
    checks = "".join(
        f"<li><span aria-hidden='true'>✓</span>{escape(x['check'])}</li>"
        for x in live["checks"]
    )
    template = (ROOT / "docs/portfolio.template.html").read_text()
    for key, value in {
        "ATLAS": "".join(cards),
        "EVAL_ROWS": rows,
        "LIVE_ROWS": live_rows,
        "LIVE_CHECKS": checks,
        "EVAL_PASSED": str(report["passed"]),
        "EVAL_TOTAL": str(report["total"]),
        "EVAL_DATE": escape(report["generated_at"]),
        "DIAGRAM_COUNT": str(len(catalog)),
    }.items():
        template = template.replace("{{" + key + "}}", value)
    (ROOT / "docs/index.html").write_text(template)


if __name__ == "__main__":
    render()
