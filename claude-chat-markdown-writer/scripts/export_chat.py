#!/usr/bin/env python3
"""
export_chat.py — Markdown Writer Skill helper script
=====================================================
Formats raw chat JSON (e.g. exported from Claude.ai or a custom client)
into a clean Markdown chatlog file.

Usage
-----
  python export_chat.py --input chat.json [--topic "my topic"] [--output ./out]
  python export_chat.py --stdin [--topic "my topic"] [--output ./out]
  cat chat.json | python export_chat.py --stdin --topic "design review"

Input JSON format (either array or object with a "messages" key)
-----------------------------------------------------------------
[
  {"role": "user",      "content": "Hello!", "timestamp": "2026-05-02T14:00:00"},
  {"role": "assistant", "content": "Hi there!", "timestamp": "2026-05-02T14:00:05"}
]

OR

{
  "messages": [ ... same list ... ]
}

Output
------
  claude-chatlog--{topic}--{YYYY-MM-DD_HH-MM}.md
  written to --output directory (default: current directory)
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

ROLE_ICONS = {
    "user":      "👤 User",
    "human":     "👤 User",
    "assistant": "🤖 Claude",
    "claude":    "🤖 Claude",
    "system":    "⚙️  System",
}


def slugify(text: str) -> str:
    """Convert a topic string to kebab-case."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60]


def infer_topic(messages: list[dict]) -> str:
    """Infer a short topic from the first user message."""
    for msg in messages:
        if msg.get("role") in ("user", "human"):
            text = msg.get("content", "")
            if isinstance(text, list):          # handle content-block format
                text = " ".join(
                    b.get("text", "") for b in text if isinstance(b, dict)
                )
            words = text.split()[:6]
            return slugify(" ".join(words)) or "conversation"
    return "conversation"


def format_content(content) -> str:
    """Normalise content — string or list of content blocks."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                btype = block.get("type", "text")
                if btype == "text":
                    parts.append(block.get("text", "").strip())
                elif btype == "code":
                    lang = block.get("language", "")
                    parts.append(f"```{lang}\n{block.get('code','').strip()}\n```")
                elif btype == "image":
                    parts.append("*[image]*")
                else:
                    parts.append(str(block))
        return "\n\n".join(p for p in parts if p)
    return str(content).strip()


def build_markdown(messages: list[dict], topic: str, now: datetime) -> str:
    """Render the full chatlog Markdown string."""
    ts = now.strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Chat Log: {topic.replace('-', ' ').title()}",
        "",
        f"**Exported:** {ts}  ",
        f"**Messages:** {len(messages)}",
        "",
        "---",
        "",
        "## Conversation",
        "",
    ]

    for i, msg in enumerate(messages, start=1):
        role_raw = msg.get("role", "user").lower()
        icon = ROLE_ICONS.get(role_raw, f"❓ {role_raw.capitalize()}")

        # Timestamp label
        raw_ts = msg.get("timestamp") or msg.get("created_at") or msg.get("time")
        if raw_ts:
            try:
                dt = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
                label = dt.strftime("%H:%M:%S")
            except ValueError:
                label = str(raw_ts)
        else:
            label = f"Msg {i}"

        body = format_content(msg.get("content", ""))

        lines += [
            f"### {icon} · {label}",
            "",
            body,
            "",
            "---",
            "",
        ]

    iso_date = now.strftime("%Y-%m-%d")
    lines += [f"*Exported from Claude.ai · {iso_date}*", ""]
    return "\n".join(lines)


def filename_for(topic: str, now: datetime) -> str:
    dt_str = now.strftime("%Y-%m-%d_%H-%M")
    return f"claude-chatlog--{topic}--{dt_str}.md"


# ── main ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Export a Claude chat to a Markdown chatlog file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--input",  metavar="FILE", help="Path to input JSON file")
    source.add_argument("--stdin",  action="store_true", help="Read JSON from stdin")

    p.add_argument("--topic",  metavar="TEXT",
                   help="Short topic label (auto-inferred if omitted)")
    p.add_argument("--output", metavar="DIR",  default=".",
                   help="Output directory (default: current directory)")
    p.add_argument("--stdout", action="store_true",
                   help="Print Markdown to stdout instead of writing a file")
    return p.parse_args()


def load_messages(args) -> list[dict]:
    if args.stdin:
        raw = sys.stdin.read()
    else:
        raw = Path(args.input).read_text(encoding="utf-8")

    data = json.loads(raw)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("messages", "conversation", "turns", "chat"):
            if key in data and isinstance(data[key], list):
                return data[key]
    raise ValueError(
        "Could not find a messages list in the JSON. "
        "Expected a top-level array or an object with a 'messages' key."
    )


def main():
    args = parse_args()
    now  = datetime.now()

    try:
        messages = load_messages(args)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    if not messages:
        print("[error] No messages found in input.", file=sys.stderr)
        sys.exit(1)

    topic = slugify(args.topic) if args.topic else infer_topic(messages)
    md    = build_markdown(messages, topic, now)

    if args.stdout:
        print(md)
        return

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / filename_for(topic, now)
    out_file.write_text(md, encoding="utf-8")
    print(f"✅  Saved: {out_file}")


if __name__ == "__main__":
    main()
