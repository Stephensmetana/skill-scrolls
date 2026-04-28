---
name: directory-scanner
description: Scan a directory's immediate subdirectories and produce a structured report that describes what each one contains. Use this skill whenever the user wants to explore, document, audit, or get an overview of a folder's contents — including requests like "what's in this directory?", "give me a summary of these folders", "document my project structure", "make a report of my subdirectories", "what does each folder contain?", "audit my file layout", or any time they want a human-readable breakdown of a folder's children. Also trigger when the user pastes a path and asks what's in it, or says "scan", "index", "map", or "overview" in the context of local files or folders.
---

# Directory Scanner

Produce a clear, structured report of the immediate subdirectories inside a given directory, with a concise description of what each one contains.

## What this skill produces

A Markdown report with:
- A one-line **purpose summary** per subdirectory
- A **file inventory** (file count, types present, notable files)
- Optional **notes** when a directory looks unusual (empty, deeply nested, mixed concerns, etc.)

The goal is to give the reader a fast, accurate mental model of a folder's layout — something they could hand to a new team member and have them immediately understand what lives where.

## Workflow

### Step 0 — Run the scan script

This skill includes `scripts/scan_dir.py`. Run it first — it does all the filesystem work in one shot and returns structured JSON, so you don't need to shell out repeatedly:

```bash
python <skill-path>/scripts/scan_dir.py <target_directory>
```

Optional flags:
- `--depth N` — how many levels deep to recurse when counting files (default: 3)
- `--output text` — human-readable summary instead of JSON (useful for quick spot-checks)

The JSON output contains everything you need to write the report: `file_count`, `file_types`, `notable_files`, `top_level` listing, and `readme` excerpt (first 40 lines) for every immediate subdirectory. Parse it and proceed from Step 3 — you can skip Steps 1 and 2.

### Step 1 — Resolve the target directory

If the user didn't provide a path, ask for one (or confirm the current working directory if they implied it). Expand `~` and relative paths before proceeding.

### Step 2 — List immediate subdirectories

If the script isn't available, fall back to shell commands:

```bash
# List immediate subdirectories only
find <target> -maxdepth 1 -mindepth 1 -type d | sort
```

If there are no subdirectories, report that and offer to describe the top-level files instead.

### Step 3 — Sample each subdirectory

If you didn't use the script, gather just enough information to write an accurate description. Don't read every file — scan lightly:

```bash
# File count and types
find <subdir> -maxdepth 2 -type f | wc -l
find <subdir> -maxdepth 2 -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10

# Notable files (READMEs, configs, manifests)
find <subdir> -maxdepth 2 -name "README*" -o -name "*.json" -o -name "*.toml" \
     -o -name "*.yaml" -o -name "*.yml" -o -name "Makefile" -o -name "*.md" \
  | head -20

# Top-level file names (gives a quick gestalt)
ls <subdir>
```

Read the content of any README or obvious manifest file you find — these are gold for accurate descriptions.

### Step 4 — Write the report

Produce a Markdown report. Use this structure:

```markdown
# Directory Report: <path>
_Generated: <date>_

## Summary
<1–2 sentence overview of what this directory is / high-level purpose>

---

## Subdirectories

### `<subdir-name>/`
**Purpose:** <one-line description of what this folder is for>

| Metric | Value |
|--------|-------|
| Files | <count> |
| Types | <ext1>, <ext2>, … |
| Notable files | <README.md, package.json, …> |

> <1–3 sentence description of what's inside, inferred from file names, README, and structure>

---

### `<next-subdir>/`
…
```

Repeat the block for every subdirectory. Keep each description honest and specific — don't say "contains various files" when you can say "Python source files for the data ingestion pipeline".

### Step 5 — Flag anything unusual

After the per-directory blocks, add an optional **Notes** section for things worth calling out:
- Empty directories
- Directories with a single file
- Directories that seem to serve overlapping purposes
- Very large directories (>1,000 files)
- Directories with no recognizable file types

### Step 6 — Save the report as a Markdown file

Always write the report to a `.md` file — this is a required final step, not optional. The skill is not complete until the file exists on disk.

Choose the output path as follows:
- If the user specified a path or filename, use it exactly.
- Otherwise, default to `<target_directory>/directory-report.md`.

After writing the file, tell the user the full path so they can find it easily.

### Step 7 — Offer next steps

After saving the file, briefly offer to:
- Drill down into any specific subdirectory
- Recursively scan a chosen subdirectory
- Re-run the scan and update the report at any time

## Tips for accurate descriptions

- **READMEs beat guessing.** If a subdirectory has a README, read it — even a one-liner usually reveals the intent better than file name inference.
- **File extensions tell a story.** A directory full of `.py` files is probably source code; `.csv` and `.json` together suggest data; `.mp4` and `.png` together suggest media.
- **Config files reveal context.** A `package.json` means Node.js. A `pyproject.toml` means Python. A `Dockerfile` means containerized service. Use these as anchors for the description.
- **Don't over-infer.** If you genuinely can't tell what a directory is for, say so — "Contents unclear: mixed file types with no README" is more useful than a confident wrong answer.

## Report tone

Write descriptions as if explaining to a capable developer who is new to this codebase. Be direct and specific. Skip vague filler like "this folder contains files related to…" — just say what they are.
