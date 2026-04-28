# Pattern Library: Context-Efficient Design

Load the section relevant to what you're designing. Don't read everything —
navigate to the pattern that matches the artifact type.

## Contents
1. [Skill (SKILL.md) Patterns](#1-skill-skillmd-patterns)
2. [Pointer-Based Tool Patterns](#2-pointer-based-tool-patterns)
3. [File Pointer Patterns (CLAUDE.md / AGENTS.md)](#3-file-pointer-patterns)
4. [Session / Pipeline Patterns](#4-session--pipeline-patterns)
5. [Fallbacks: No API Access](#5-fallbacks-no-api-access)

---

## 1. Skill (SKILL.md) Patterns

### Pattern: Lean routing description

The description is the only content that loads on *every* skill selection cycle.
It must route, not explain. Compress to trigger phrases + domains.

```
# BLOATED (educational, ~80 tokens)
description: >
  This skill assists with Python development tasks including writing new code,
  debugging errors, refactoring existing code, running tests, and creating 
  documentation. Use it whenever you need help with Python programming work.

# LEAN (routing signal, ~30 tokens)  
description: >
  Python code: write, debug, refactor, test. Triggers on .py files, import
  errors, pytest output, type annotations, virtual environments.
```

### Pattern: Progressive disclosure body

Split body into: (1) always-needed core, (2) conditional reference files.
The model reads core unconditionally; reference files only when the task needs them.

```markdown
## Core workflow
[The 5-10 steps that apply to EVERY invocation — keep this tight]

## Reference files (load on demand)
- `./references/postgres.md` — Load if task involves PostgreSQL queries or schema
- `./references/mysql.md` — Load if task involves MySQL
- `./references/error-codes.md` — Load only when debugging a specific error code
- `./references/examples/` — Load the file matching the endpoint the user mentions
```

The phrasing "load if" / "load only when" tells the model these are conditional.
The model will not load them unless the task warrants it.

### Pattern: Script execution (zero-token code)

Scripts in `scripts/` run via bash. The source code never enters context — only
the output does. This is the highest compression ratio possible: 300-line script = 0 context tokens.

```markdown
## Validation
Before submitting any form, run:
`python ./scripts/validate.py <json_payload>`

The script prints "VALID" or a list of field errors. Act on the output only.
Do not read the script source.
```

```markdown
## Schema check
To get the current database schema, run:
`python ./scripts/get_schema.py --tables <table_names>`

The script returns a compact schema summary. Do not use the raw DB schema file.
```

### Pattern: Domain-variant organization

When a skill covers multiple frameworks/environments, split by variant instead
of loading all variants always.

```
my-skill/
├── SKILL.md         ← Core workflow + routing to variant
└── references/
    ├── aws.md       ← loaded only for AWS tasks
    ├── gcp.md       ← loaded only for GCP tasks  
    └── azure.md     ← loaded only for Azure tasks
```

SKILL.md body:
```markdown
## Environment setup
Determine which cloud environment the user is targeting, then:
- AWS: load `./references/aws.md`
- GCP: load `./references/gcp.md`
- Azure: load `./references/azure.md`

Do not load all three.
```

---

## 2. Pointer-Based Tool Patterns

The core idea: tools return a navigable summary + a stable reference ID.
The agent uses the summary to reason, and the ID to fetch specific data via a
companion tool. Raw data never enters context unless the agent explicitly asks for it.

### Pattern: File reader with companion line-fetch

```python
# Primary tool — returns structure, never raw content
def ReadFile(path: str) -> dict:
    with open(path) as f:
        lines = f.readlines()
    
    # Extract structure without loading file body
    structure = [
        l.strip() for l in lines
        if l.startswith(("def ", "class ", "async def ", "function ", "export ", "const "))
    ]
    
    return {
        "path": path,
        "total_lines": len(lines),
        "preview": "".join(lines[:8]),       # first 8 lines only
        "structure": structure[:20],          # function/class names
        "ref": path,                          # stable pointer back to this file
        "hint": f"Use ReadFileLines('{path}', start, end) to inspect a specific section."
    }
    # Token cost: ~150-250 tokens regardless of file size
    # vs. raw read: 400-5,000+ tokens

# Companion tool — targeted fetch, only called when agent needs specific lines
def ReadFileLines(path: str, start_line: int, end_line: int) -> dict:
    with open(path) as f:
        lines = f.readlines()
    return {
        "path": path,
        "lines": lines[start_line:end_line],
        "range": f"{start_line}-{end_line} of {len(lines)}"
    }
    # Token cost: proportional to range requested, agent-controlled
```

### Pattern: Config reader with key-fetch companion

```python
def ReadConfig(path: str) -> dict:
    import json, os
    with open(path) as f:
        data = json.load(f)
    
    return {
        "path": path,
        "ref": path,
        "key_count": len(data),
        "top_level_keys": list(data.keys()),
        "size_bytes": os.path.getsize(path),
        "hint": f"Use GetConfigValue('{path}', key) to retrieve a specific value."
    }
    # Returns key names only — 50-150 tokens vs 500-5,000 for raw file

def GetConfigValue(path: str, key: str) -> dict:
    import json
    with open(path) as f:
        data = json.load(f)
    value = data.get(key)
    return {"path": path, "key": key, "value": value, "found": key in data}
    # Returns one value — always < 50 tokens
```

### Pattern: API wrapper with field filtering

```python
def GetPullRequest(repo: str, pr_number: int) -> dict:
    raw = github_client.get_pr(repo, pr_number)  # ~200 fields

    return {
        "ref": f"pr_{repo}_{pr_number}",
        "number": raw["number"],
        "title": raw["title"],
        "state": raw["state"],
        "author": raw["user"]["login"],
        "files_changed": raw["changed_files"],
        "additions": raw["additions"],
        "deletions": raw["deletions"],
        "labels": [l["name"] for l in raw["labels"]],
        "body_preview": (raw.get("body") or "")[:300],
        # Pointer hints — not calls, just routing signals for the agent
        "_fetch": {
            "full_body": f"GetPRBody('{repo}', {pr_number})",
            "diff": f"GetPRDiff('{repo}', {pr_number})",
            "comments": f"GetPRComments('{repo}', {pr_number})",
            "files": f"GetPRFiles('{repo}', {pr_number})",
        }
    }
    # ~200 tokens vs 2,000-8,000 for raw API response
```

The `_fetch` dict is not executable — it's a routing hint. The agent reads it
and decides which follow-up call the task actually needs.

### Pattern: Search with grouping + pagination

```python
def SearchCodebase(query: str, max_files: int = 10) -> dict:
    import subprocess
    raw = subprocess.run(
        ["rg", "--json", query, "."],
        capture_output=True, text=True
    ).stdout.splitlines()
    
    # Parse and group by file
    by_file = {}
    for line in raw:
        import json
        try:
            item = json.loads(line)
            if item.get("type") == "match":
                f = item["data"]["path"]["text"]
                ln = item["data"]["line_number"]
                by_file.setdefault(f, []).append(ln)
        except Exception:
            continue
    
    # Sort by match density, return top N files
    ranked = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:max_files]
    
    return {
        "query": query,
        "total_matches": sum(len(v) for v in by_file.values()),
        "files_matched": len(by_file),
        "top_files": [
            {"file": f, "match_count": len(lns), "sample_lines": lns[:5]}
            for f, lns in ranked
        ],
        "hint": "Use ReadFileLines(path, start, end) to inspect specific matches."
    }
    # Returns ranked file list, not 800 raw matching lines
    # ~300 tokens vs 5,000-20,000+ for raw grep output
```

### Pattern: Database query with row cap and schema pointer

```python
def QueryDatabase(sql: str, max_rows: int = 20) -> dict:
    import sqlite3
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    
    # Get count first (cheap)
    count_sql = f"SELECT COUNT(*) FROM ({sql})"
    try:
        total = cur.execute(count_sql).fetchone()[0]
    except Exception:
        total = "unknown"
    
    # Fetch capped result
    cur.execute(sql + f" LIMIT {max_rows}")
    rows = cur.fetchall()
    columns = [d[0] for d in cur.description] if cur.description else []
    
    return {
        "sql": sql,
        "columns": columns,
        "total_rows": total,
        "rows_returned": len(rows),
        "rows": rows,
        "note": f"Showing {len(rows)} of {total} rows. Add OFFSET N to paginate."
            if isinstance(total, int) and total > max_rows else None
    }
    # Worst case: 20 rows × ~50 tokens = 1,000 tokens
    # vs. full result: could be 100,000+ tokens

### Pattern: Tool discovery meta-tool

Use when the tool surface is large (10+ tools). Prevents loading all definitions upfront.

```python
TOOL_REGISTRY = {
    "files": {
        "ReadFile": "Read a file's structure and preview. Returns pointer + summary.",
        "ReadFileLines": "Read specific line range from a file.",
        "WriteFile": "Write content to a file.",
        "SearchFiles": "Find files by name pattern.",
    },
    "database": {
        "QueryDatabase": "Run a SQL query with row cap.",
        "GetSchema": "Get database table schemas.",
        "GetTableSample": "Get sample rows from a table.",
    },
    "search": {
        "SearchCodebase": "Search code by keyword, returns grouped results.",
        "SearchLogs": "Search log files with filtering.",
    }
}

def ListAvailableTools(category: str = None) -> dict:
    """
    Returns tool names and descriptions.
    Call this before using a tool you haven't used in this session.
    """
    if category and category in TOOL_REGISTRY:
        return {"category": category, "tools": TOOL_REGISTRY[category]}
    return {"categories": list(TOOL_REGISTRY.keys()), 
            "hint": "Call ListAvailableTools(category) to see tools in a category."}
```

---

## 3. File Pointer Patterns

### Pattern: Conditional loading in SKILL.md / CLAUDE.md / AGENTS.md

The phrasing of file references controls whether they load immediately or on demand.

```markdown
# UNCONDITIONAL — loads every time (avoid)
Read ./docs/api-schema.md before beginning. It contains the API schema.

# CONDITIONAL — loads only when needed (use this)
- `./docs/api-schema.md` — Load if task involves validating or constructing API payloads.
- `./docs/error-codes.md` — Load only when debugging a specific error response.
- `./docs/examples/` — Load the file matching the endpoint the user mentions.
```

### Pattern: @file:line pointer syntax (CLAUDE.md / AGENTS.md)

For context files where you want to point the model to authoritative content
without inlining it:

```markdown
## Reference materials
IMPORTANT: When you encounter a file reference like @rules/auth.md, use your
Read tool to load it only if it's directly relevant to the current task.
Do not load all references upfront.

- Authentication: @src/auth/README.md
- DB schema: @docs/schema.md (load only for database tasks)
- API contracts: @docs/api/v2-spec.md:45 (line 45 is the endpoint index)
- Error handling: @docs/error-handling.md
```

The `:line_number` suffix tells the agent where to start reading, so it can
navigate large files without loading them from the top.

### Pattern: Pointer-over-copy for CLAUDE.md

From HumanLayer's documented best practice — prefer file references to copies:

```markdown
# COPY — goes stale, wastes tokens
## Auth pattern
Always use JWT validation like this:
```python
def validate_token(token):
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    ...
[40 lines of code that may be outdated]
```

# POINTER — always current, zero token cost until needed
## Auth pattern
See @src/auth/validate.py:1-45 for the current JWT validation implementation.
Load it if the task involves auth token handling.
```

### Pattern: Index file for large reference surfaces

When you have many reference files, create a lightweight index as the always-loaded
entry point. The index itself stays small; the agent navigates to specific files.

```markdown
# references/INDEX.md (always loaded — keep under 100 lines)

| File | Contents | Load when |
|------|----------|-----------|
| postgres.md | Schema, query patterns, connection config | DB task mentions PostgreSQL |
| mysql.md | Schema, query patterns | DB task mentions MySQL |
| auth.md | JWT, OAuth, session management | Task involves authentication |
| error-codes.md | API error code lookup table | Debugging an error response |
| endpoints/ | One file per API endpoint | User asks about that specific endpoint |
```

---

## 4. Session / Pipeline Patterns

### Pattern: Three-zone context model

Maintain context as three zones. Only the tail (recent turns) is ever raw;
everything else is compressed.

```
┌─────────────────────────────────────┐
│ STATIC ZONE                         │  ~2,000-5,000 tokens (cached)
│ System prompt + tool definitions    │
├─────────────────────────────────────┤
│ COMPRESSED HEAD                     │  ~3,000-8,000 tokens
│ Structured summary of past work     │  (intent, decisions, files, progress)
├─────────────────────────────────────┤
│ LIVE TAIL                           │  ~10,000-20,000 tokens
│ Last N turns verbatim               │
└─────────────────────────────────────┘
```

Trigger compression at 50-70% context capacity, not at overflow.
Proactive compression costs one summarization call; reactive overflow costs
a failed call + retry + potential context loss.

### Pattern: Structured working memory

State lives in a file/dict outside the conversation, not in message history.

```python
# session_state.json — written by tools, read selectively
{
    "intent": "Refactor auth module to use JWT",
    "completed": ["Read auth.py", "Identified 3 functions to change"],
    "in_progress": "Updating validate_token()",
    "files_modified": ["src/auth.py"],
    "decisions": ["Use PyJWT", "Keep backward compat for v1 tokens"],
    "next_steps": ["Update tests", "Update docs"],
    "blockers": []
}
```

Each turn, the agent reads this file (100-200 tokens) instead of re-processing
20 turns of conversation history (20,000+ tokens).

### Pattern: Observation masking

After acting on a tool result, replace the raw output with a compact receipt:

```
# Turn 3 (full output — agent needs to read and act on it)
[ReadFile result] src/auth.py
def authenticate(user, password):
    [... 847 lines ...]

# Turn 15 (observation masked — agent acted on this in turn 3)
[ReadFile] src/auth.py — read turn 3, modified validate_token() ✓
```

Implementation: before each LLM call, scan message history for tool results
older than N turns. Replace content with one-line receipt. Keep the tool call
name so the agent remembers what it did, but discard the payload.

### Pattern: Subagent context isolation

Each subagent receives only what it needs. The parent agent retains only results.

```
Parent agent context:
  - Task plan (what we're doing)
  - File paths as pointers (not contents)
  - Progress summary

Search subagent receives:
  - Search query
  - Returns: list of relevant file paths (pointers, not contents)

Edit subagent receives:
  - One target file (contents)
  - Specific edit instruction
  - Returns: diff only (not the whole file post-edit)
```

---

## 5. Fallbacks: No API Access

When running inside claude.ai or Claude Code without an API key configured,
`call_llm_lightweight()` style secondary LLM calls are not available.
Use these deterministic alternatives instead.

### Deterministic chunked analysis (no API required)

```python
def AnalyzeLargeFileNoAPI(file_path: str, keywords: list) -> dict:
    with open(file_path) as f:
        lines = f.readlines()
    
    total = len(lines)
    
    # Strategy 1: Keyword-scored extraction
    scored = []
    for i, line in enumerate(lines):
        score = sum(1 for kw in keywords if kw.lower() in line.lower())
        if score > 0:
            scored.append((score, i, line.strip()))
    
    scored.sort(reverse=True)
    top = scored[:25]
    
    # Strategy 2: Structural extraction
    structure = [
        l.strip() for l in lines
        if l.startswith(("def ", "class ", "async def ", "function ", "export "))
    ]
    
    # Strategy 3: Head + tail (high-signal zones)
    head = "".join(lines[:20])
    tail = "".join(lines[-10:])
    
    return {
        "file": file_path,
        "total_lines": total,
        "structure": structure[:20],
        "keyword_matches": [{"line": i, "content": c, "score": s} for s, i, c in top],
        "head": head,
        "tail": tail,
        "ref": file_path,
        "hint": f"Use ReadFileLines('{file_path}', start, end) to read specific sections."
    }
```

### Deterministic session compaction (no API required)

Instead of LLM-based summarization, maintain a structured state dict that
the code (not the LLM) updates after each step:

```python
class SessionState:
    def __init__(self):
        self.state = {
            "intent": "",
            "completed": [],
            "in_progress": "",
            "files_touched": [],
            "decisions": [],
            "next_steps": [],
            "errors_seen": []
        }
    
    def record_completion(self, task: str, files: list = None):
        self.state["completed"].append(task)
        if files:
            self.state["files_touched"].extend(files)
    
    def to_context_string(self) -> str:
        """Serialize to a compact string for injection into context."""
        s = self.state
        parts = [f"Goal: {s['intent']}"]
        if s["completed"]:
            parts.append("Done: " + "; ".join(s["completed"][-5:]))  # last 5 only
        if s["in_progress"]:
            parts.append(f"Now: {s['in_progress']}")
        if s["files_touched"]:
            parts.append("Files: " + ", ".join(set(s["files_touched"])))
        return "\n".join(parts)
    # Typical output: 100-200 tokens regardless of session length
```

This replaces open-ended LLM summarization with deterministic state tracking.
No API calls needed. State stays fresh because the code writes it, not the model.
