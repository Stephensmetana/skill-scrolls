#!/usr/bin/env python3
"""
scan_skills.py — Skills Index helper for the skills-index skill.

Usage:
    python scan_skills.py <root_directory> [--output json|text] [--readme]

Recursively finds every SKILL.md under <root_directory>, extracts the YAML
frontmatter (name, description, compatibility), and emits a structured JSON
summary suitable for generating an index or README.

Flags:
    --output json|text   Output format (default: json)
    --readme             Write a README.md to <root_directory> and exit
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def extract_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter between --- delimiters (simple key/value parser)."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    raw = match.group(1)
    result: dict = {}
    current_key = None
    current_value_lines: list[str] = []

    for line in raw.splitlines():
        # Key: value  (simple single-line or start of multi-line)
        key_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)", line)
        if key_match:
            # Flush previous key
            if current_key:
                result[current_key] = " ".join(current_value_lines).strip()
            current_key = key_match.group(1)
            rest = key_match.group(2).strip()
            if rest in (">", "|", ""):
                current_value_lines = []
            else:
                current_value_lines = [rest]
        elif current_key and line.startswith("  "):
            # Continuation line (block scalar)
            current_value_lines.append(line.strip())

    if current_key:
        result[current_key] = " ".join(current_value_lines).strip()

    return result


def scan_skills(root: Path) -> list[dict]:
    """Walk root recursively and collect metadata for every SKILL.md found."""
    skills = []

    for skill_path in sorted(root.rglob("SKILL.md")):
        rel_path = skill_path.relative_to(root)
        skill_dir = skill_path.parent

        try:
            text = skill_path.read_text(encoding="utf-8")
        except OSError as e:
            skills.append({"path": str(rel_path), "error": str(e)})
            continue

        fm = extract_frontmatter(text)
        name = fm.get("name", skill_dir.name)
        description = fm.get("description", "")
        compatibility = fm.get("compatibility", "")

        # Infer category from the directory structure
        parts = rel_path.parts  # e.g. ("agent-tools", "context-optimizer", "SKILL.md")
        if len(parts) >= 3:
            category = parts[0]
        elif len(parts) == 2:
            category = parts[0]
        else:
            category = "."

        # Collect bundled resources
        def list_dir_files(subdir: str) -> list[str]:
            d = skill_dir / subdir
            if d.is_dir():
                return [p.name for p in d.iterdir() if p.is_file()]
            return []

        scripts = list_dir_files("scripts")
        references = list_dir_files("references")
        assets = list_dir_files("assets")

        skills.append({
            "name": name,
            "path": str(rel_path.parent),
            "category": category,
            "description": description,
            "compatibility": compatibility,
            "has_scripts": bool(scripts),
            "scripts": scripts,
            "has_references": bool(references),
            "references": references,
            "has_assets": bool(assets),
            "assets": assets,
        })

    return skills


def group_by_category(skills: list[dict]) -> dict[str, list[dict]]:
    categories: dict[str, list[dict]] = {}
    for skill in skills:
        cat = skill["category"]
        categories.setdefault(cat, []).append(skill)
    return categories


def render_text(skills: list[dict]) -> str:
    grouped = group_by_category(skills)
    lines = []
    for category, items in sorted(grouped.items()):
        lines.append(f"\n## {category}")
        for s in items:
            lines.append(f"\n### {s['name']}  ({s['path']})")
            if s.get("description"):
                # Wrap description at ~80 chars
                desc = s["description"]
                lines.append(f"  {desc}")
            if s.get("compatibility"):
                lines.append(f"  Requires: {s['compatibility']}")
    return "\n".join(lines)


def _first_sentence(text: str) -> str:
    """Return the first complete sentence from text, or the full text if short."""
    if not text:
        return ""
    text = text.strip()
    # Find end of first sentence: period/!/ followed by space+uppercase or end
    match = re.search(r"[.!?](?=\s+[A-Z]|\s*$)", text)
    if match:
        sentence = text[: match.end()].strip()
        # If the sentence is very long, truncate at word boundary
        if len(sentence) > 200:
            sentence = sentence[:197].rsplit(" ", 1)[0] + "..."
        return sentence
    # No sentence boundary found — just cap at 200 chars
    if len(text) > 200:
        return text[:197].rsplit(" ", 1)[0] + "..."
    return text


def render_readme(skills: list[dict], root: Path) -> str:
    grouped = group_by_category(skills)
    total = len(skills)

    lines = [
        "# Smetana Skills",
        "",
        f"A collection of **{total} Agent skills** for software development, game dev, and agentic tooling.",
        "",
        "Each skill is a `SKILL.md` file that gives an Agent structured guidance for a specific task —",
        "think of them as focused instruction modules that activate when you need them.",
        "",
        "---",
        "",
        "## Skills",
        "",
    ]

    for category, items in sorted(grouped.items()):
        label = category.replace("-", " ").title()
        lines.append(f"### {label}")
        lines.append("")
        for s in items:
            desc = s.get("description", "")
            short = _first_sentence(desc)
            link = f"[`{s['name']}`]({s['path']}/SKILL.md)"
            lines.append(f"- {link} — {short}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Structure",
        "",
        "```",
        "skills-root/",
        "├── <category>/",
        "│   └── <skill-name>/",
        "│       ├── SKILL.md          # skill instructions + YAML frontmatter",
        "│       ├── scripts/          # helper scripts bundled with the skill",
        "│       ├── references/       # reference docs loaded on demand",
        "│       └── assets/           # static files used in output",
        "```",
        "",
        "---",
        "",
        "_This README was generated by the `skills-index` skill._",
    ]

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Scan a skills directory and emit a structured index.")
    parser.add_argument("root", help="Root directory to scan")
    parser.add_argument("--output", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    parser.add_argument("--readme", action="store_true",
                        help="Write README.md to <root> and exit")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    skills = scan_skills(root)

    if args.readme:
        content = render_readme(skills, root)
        readme_path = root / "README.md"
        readme_path.write_text(content, encoding="utf-8")
        print(f"Wrote {readme_path}")
        return

    if args.output == "text":
        print(render_text(skills))
    else:
        print(json.dumps({"root": str(root), "total": len(skills), "skills": skills}, indent=2))


if __name__ == "__main__":
    main()
