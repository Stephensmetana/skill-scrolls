---
name: skills-index
description: >
  Scan a skills folder (or any folder containing SKILL.md files) and generate a
  structured index, report, or README that lists every skill with its name,
  description, category, and bundled resources. Use this skill whenever the user
  wants to: document their skill collection, generate or update a README for a
  skills repo, get an overview of what skills are available, audit a skills
  directory, produce a shareable index of all skills, or prepare a skills folder
  for publishing as a GitHub repo. Trigger on phrases like "list my skills",
  "generate a skills README", "what skills do I have", "index my skills folder",
  "document my skills", "make a readme for my skills", or any request to
  summarize, catalog, or publish a collection of SKILL.md files. Always use this
  skill — do NOT manually walk skill directories without it.
---

# Skills Index

Scan a directory tree for SKILL.md files and produce a structured index,
report, or README. Useful for documenting, auditing, and sharing a collection
of Claude skills.

---

## What This Skill Produces

Choose one or more outputs based on what the user needs:

| Output | Use when |
|---|---|
| **JSON index** | You need structured data for further processing |
| **Text report** | Quick human-readable overview in the terminal |
| **README.md** | User wants to publish the skills folder as a GitHub repo |

---

## Workflow

### Step 1 — Resolve the target directory

If the user didn't specify a path, ask for one (or confirm cwd). Expand `~`
and relative paths before proceeding.

### Step 2 — Run the scan script

This skill includes `scripts/scan_skills.py`. Run it first — it recursively
finds every SKILL.md, extracts frontmatter (name, description, compatibility),
and groups skills by category:

```bash
# JSON index (default — use for further processing or reporting)
python <skill-path>/scripts/scan_skills.py <target_directory>

# Human-readable text report
python <skill-path>/scripts/scan_skills.py <target_directory> --output text

# Write README.md directly to <target_directory> and exit
python <skill-path>/scripts/scan_skills.py <target_directory> --readme
```

### Step 3 — Produce the requested output

**If the user wants a README** (e.g., "make a readme for my skills repo"):
- Run with `--readme` to write it directly, then open the file to verify it
  looks right. Offer to adjust the intro text, category labels, or ordering.

**If the user wants a report / overview**:
- Run with `--output text` and present it in the conversation.
- Add a one-paragraph summary: total skill count, categories present,
  any categories that look thin or overpopulated.

**If the user wants raw data**:
- Run with default JSON output and format/filter as needed.

### Step 4 — Offer follow-up actions

After producing the index, suggest relevant next steps:

- "Want me to update the README whenever you add a new skill?" → point them
  to running `--readme` again, or wiring it into a git hook / CI step.
- "Want to add a GitHub Actions workflow to auto-regenerate the README?" →
  offer to write `.github/workflows/update-readme.yml`.
- "Want to add a `.gitignore` for the workspace eval directories?" → offer
  to write one that excludes `*-workspace/` and `evals/` noise.

---

## Tips for Good READMEs

- **Category labels**: The script infers categories from top-level folder names.
  If the folder names are cryptic, you can rename them for clarity before
  generating the README, or edit the `category_labels` dict in the script.
- **Short descriptions**: The README truncates descriptions to the first
  sentence. Write first sentences that stand alone as one-liners.
- **Order**: Skills within a category are listed alphabetically by folder name.
  Rename folders to control ordering (e.g., prefix with `01-`, `02-`).
- **Badges**: After generating the README, consider adding GitHub badges for
  the skill count, license, or last-updated date above the intro paragraph.

---

## GitHub Repo Setup

When the user wants to turn their skills folder into a GitHub repo, walk them
through this checklist in order:

1. Generate README.md (`--readme` flag)
2. Create `.gitignore` (see template below)
3. `git init` in the skills root (if not already a repo)
4. `git add .` and initial commit
5. Create the repo on GitHub and push

### .gitignore template for a skills repo

```gitignore
# Eval workspaces (generated during skill development)
*-workspace/

# Python
__pycache__/
*.pyc
*.pyo
.venv/
env/

# Editor
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Temp files
/tmp/
*.tmp
```
