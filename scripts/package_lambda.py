"""Build Linux x86_64 CPython 3.12 assets even on an Apple Silicon workstation."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / ".build/lambda"
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--quiet",
            "--platform",
            "manylinux2014_x86_64",
            "--implementation",
            "cp",
            "--python-version",
            "3.12",
            "--only-binary=:all:",
            "--target",
            str(target),
            "-r",
            str(ROOT / "backend/requirements.lock"),
        ],
        check=True,
    )
    shutil.copytree(
        ROOT / "backend/app",
        target / "app",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    required = [
        "app/api.py",
        "app/worker.py",
        "app/knowledge.json",
        "fastapi/__init__.py",
        "mangum/__init__.py",
        "pydantic/__init__.py",
    ]
    for name in required:
        if not (target / name).is_file():
            raise RuntimeError(f"Missing package asset: {name}")
    if not list((target / "pydantic_core").glob("*cpython-312-x86_64-linux-gnu.so")):
        raise RuntimeError("Missing Linux pydantic-core binary")
    print(
        "Lambda asset ready: Linux x86_64 CPython 3.12, dependencies and knowledge included"
    )


if __name__ == "__main__":
    main()
