#!/usr/bin/env python3
"""
scan_dir.py — Directory Scanner helper for the directory-scanner skill.

Usage:
    python scan_dir.py <target_directory> [--depth N] [--output json|text]

Outputs a structured JSON (default) or human-readable text summary of each
immediate subdirectory in <target_directory>, including:
  - file count
  - file type breakdown (extension frequencies)
  - notable files (READMEs, manifests, configs)
  - top-level listing
  - README content (first 40 lines if found)

The JSON output is designed to be piped directly into an LLM prompt so it
can write an accurate report without needing to shell out repeatedly.
"""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime

# Extensions that strongly signal project type / purpose
NOTABLE_NAMES = {
    "README.md", "README.txt", "README", "README.rst",
    "package.json", "package-lock.json", "yarn.lock",
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "Makefile", "CMakeLists.txt",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", ".env",
    "index.html", "index.js", "index.ts", "main.py", "main.go", "main.rs",
    "app.py", "app.js", "app.ts",
    "SKILL.md", "AGENTS.md", "CLAUDE.md",
}

MAX_README_LINES = 40
MAX_NOTABLE_FILES = 20
FILE_SCAN_DEPTH = 3  # how deep to recurse when counting files / types


def scan_subdir(path: Path, max_depth: int = FILE_SCAN_DEPTH) -> dict:
    """Collect metadata about a single subdirectory."""
    result = {
        "name": path.name,
        "path": str(path),
        "file_count": 0,
        "dir_count": 0,
        "file_types": {},
        "notable_files": [],
        "top_level": [],
        "readme": None,
        "is_empty": False,
        "error": None,
    }

    try:
        # Top-level listing (names only, sorted)
        top_items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        result["top_level"] = [
            ("📁 " if p.is_dir() else "📄 ") + p.name for p in top_items
        ]

        ext_counter: Counter = Counter()
        notable: list[str] = []
        readme_path: Path | None = None

        # Walk up to max_depth levels
        for root, dirs, files in os.walk(path):
            # Compute current depth relative to path
            rel = Path(root).relative_to(path)
            depth = len(rel.parts)
            if depth >= max_depth:
                dirs.clear()  # don't go deeper
                continue

            # Skip hidden subdirectories (e.g. .git) to keep output clean
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            result["dir_count"] += len(dirs)
            result["file_count"] += len(files)

            for fname in files:
                fpath = Path(root) / fname
                # Extension
                suffix = fpath.suffix.lower().lstrip(".")
                if suffix:
                    ext_counter[suffix] += 1
                else:
                    ext_counter["(no ext)"] += 1

                # Notable files
                if fname in NOTABLE_NAMES and len(notable) < MAX_NOTABLE_FILES:
                    rel_path = str(fpath.relative_to(path))
                    notable.append(rel_path)

                # README detection (prefer root-level)
                if readme_path is None and fname.upper().startswith("README"):
                    readme_path = fpath

        # Sort extensions by frequency, keep top 10
        result["file_types"] = dict(ext_counter.most_common(10))
        result["notable_files"] = sorted(notable)
        result["is_empty"] = result["file_count"] == 0 and result["dir_count"] == 0

        # Read README excerpt
        if readme_path and readme_path.exists():
            try:
                lines = readme_path.read_text(errors="replace").splitlines()
                result["readme"] = "\n".join(lines[:MAX_README_LINES])
                if len(lines) > MAX_README_LINES:
                    result["readme"] += f"\n… ({len(lines) - MAX_README_LINES} more lines)"
            except Exception as e:
                result["readme"] = f"(could not read: {e})"

    except PermissionError as e:
        result["error"] = f"Permission denied: {e}"
    except Exception as e:
        result["error"] = str(e)

    return result


def scan_directory(target: str, max_depth: int = FILE_SCAN_DEPTH) -> dict:
    """Scan all immediate subdirectories of target and return structured data."""
    root = Path(target).expanduser().resolve()

    if not root.exists():
        return {"error": f"Path does not exist: {target}"}
    if not root.is_dir():
        return {"error": f"Not a directory: {target}"}

    # Immediate subdirectories only, sorted
    try:
        subdirs = sorted(
            [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")],
            key=lambda p: p.name.lower(),
        )
    except PermissionError as e:
        return {"error": f"Cannot list directory: {e}"}

    # Also note top-level files (not dirs)
    try:
        top_files = sorted(
            [p.name for p in root.iterdir() if p.is_file()],
            key=str.lower,
        )
    except Exception:
        top_files = []

    results = {
        "target": str(root),
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "subdir_count": len(subdirs),
        "top_level_files": top_files,
        "subdirectories": [scan_subdir(d, max_depth) for d in subdirs],
    }
    return results


def print_text(data: dict) -> None:
    """Human-readable text summary (for quick manual inspection)."""
    if "error" in data:
        print(f"ERROR: {data['error']}", file=sys.stderr)
        return

    print(f"\n📂  {data['target']}")
    print(f"    Generated : {data['generated']}")
    print(f"    Subdirs   : {data['subdir_count']}")
    if data["top_level_files"]:
        print(f"    Root files: {', '.join(data['top_level_files'][:10])}")
    print()

    for sd in data["subdirectories"]:
        status = " [EMPTY]" if sd["is_empty"] else ""
        err = f" [ERROR: {sd['error']}]" if sd["error"] else ""
        print(f"  ┌─ {sd['name']}/{status}{err}")
        print(f"  │  Files  : {sd['file_count']}  |  Subdirs: {sd['dir_count']}")
        if sd["file_types"]:
            types_str = ", ".join(
                f".{k}×{v}" if k != "(no ext)" else f"no-ext×{v}"
                for k, v in sd["file_types"].items()
            )
            print(f"  │  Types  : {types_str}")
        if sd["notable_files"]:
            print(f"  │  Notable: {', '.join(sd['notable_files'][:8])}")
        if sd["readme"]:
            first_line = sd["readme"].splitlines()[0].strip(" #").strip()
            print(f"  │  README : {first_line[:80]}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Scan immediate subdirectories and output structured metadata."
    )
    parser.add_argument("target", help="Directory to scan")
    parser.add_argument(
        "--depth",
        type=int,
        default=FILE_SCAN_DEPTH,
        help=f"How many levels deep to recurse when counting files (default: {FILE_SCAN_DEPTH})",
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    args = parser.parse_args()

    data = scan_directory(args.target, max_depth=args.depth)

    if args.output == "text":
        print_text(data)
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
