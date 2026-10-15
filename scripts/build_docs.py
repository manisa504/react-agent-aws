"""Create a self-contained static bundle and validate local HTML/Markdown links."""

import re
import shutil
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("src", "href"):
            if key in attrs:
                self.links.append(attrs[key])


def main():
    output = ROOT / "docs/dist"
    shutil.rmtree(output, ignore_errors=True)
    output.mkdir(parents=True)
    shutil.copytree(ROOT / "architecture", output / "architecture")
    shutil.copy2(ROOT / "amplify-rewrites.json", output / "amplify-rewrites.json")
    for source in list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md")):
        dest = output / source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    for folder in ["assets"]:
        if (ROOT / "docs" / folder).exists():
            shutil.copytree(ROOT / "docs" / folder, output / "docs" / folder)
    (output / "backend/evals").mkdir(parents=True)
    shutil.copy2(
        ROOT / "backend/evals/report.json", output / "backend/evals/report.json"
    )
    (output / "scripts").mkdir()
    shutil.copy2(
        ROOT / "scripts/check-aws-resources.sh",
        output / "scripts/check-aws-resources.sh",
    )
    original = (ROOT / "docs/index.html").read_text()
    index = (
        original.replace("../architecture/", "architecture/")
        .replace("../README.md", "README.md")
        .replace("../REQUIREMENTS_MANISHA.md", "REQUIREMENTS_MANISHA.md")
        .replace(
            "../COPILOT_MASTER_PROMPT_MANISHA.md", "COPILOT_MASTER_PROMPT_MANISHA.md"
        )
    )
    index = re.sub(
        r'(href=")(?!https?:)([\w-]+\.md)(")',
        lambda m: m[1]
        + ("docs/" if (ROOT / "docs" / m[2]).is_file() else "")
        + m[2]
        + m[3],
        index,
    )
    index = index.replace('src="assets/', 'src="docs/assets/')
    (output / "index.html").write_text(index)
    (output / "docs/index.html").write_text(original)
    checked = 0
    for source in output.rglob("*"):
        if source.suffix == ".html":
            parsed = Links()
            parsed.feed(source.read_text())
            links = parsed.links
        elif source.suffix == ".md":
            links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", source.read_text())
        else:
            continue
        for link in links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                if (
                    not url.path
                    and url.fragment
                    and source.suffix == ".html"
                    and url.fragment not in parsed.ids
                ):
                    raise RuntimeError(f"Broken fragment: {source.name}: {link}")
                continue
            target = (source.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(output.resolve()) or not target.exists():
                raise RuntimeError(
                    f"Broken local link: {source.relative_to(output)} -> {link}"
                )
            checked += 1
    tree = ET.parse(ROOT / "architecture/aws-architecture.drawio")
    cells = tree.findall(".//mxCell")
    ids = [cell.attrib["id"] for cell in cells]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate draw.io IDs")
    ET.parse(ROOT / "architecture/aws-architecture.svg")
    print(
        f"Docs ready: docs/dist; {checked} local links validated; draw.io and SVG XML parsed"
    )


if __name__ == "__main__":
    main()
