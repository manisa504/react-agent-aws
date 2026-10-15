"""Export each independently editable draw.io view, avoiding multipage viewport state."""

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--binary", default="/Applications/draw.io.app/Contents/MacOS/draw.io"
    )
    parser.add_argument("--png", action="store_true")
    args = parser.parse_args()
    catalog = json.loads((ROOT / "architecture/catalog.json").read_text())
    for view in catalog:
        slug = view["slug"]
        source = ROOT / f"architecture/{slug}.drawio"
        # The topology uses page one of the master; all other sources are standalone.
        for extension in ["svg", "png"] if args.png else ["svg"]:
            destination = ROOT / (
                f".build/{slug}-atlas.png"
                if extension == "png"
                else f"architecture/{slug}.svg"
            )
            destination.parent.mkdir(exist_ok=True, parents=True)
            result = subprocess.run(
                [
                    args.binary,
                    "-x",
                    "-f",
                    extension,
                    "-p",
                    "1",
                    "-o",
                    str(destination),
                    str(source),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            if not destination.is_file() or "Invalid page" in result.stdout:
                raise RuntimeError(f"Export failed for {slug}: {result.stdout}")
        print("Exported", slug, flush=True)


if __name__ == "__main__":
    main()
