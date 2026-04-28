---
name: skill-cli-generator
description: Generates a SKILL.md and Python CLI script for any API or service, following the Agent Skill + CLI Architecture pattern. Use this skill whenever the user wants to integrate an API using the skill/CLI pattern, says things like "create a skill and CLI for [API]", "build a CLI for [service]", "generate a skill for [link]", or pastes API documentation and wants an agent-ready integration. Always activate this skill when the user provides API docs and wants to connect an AI agent to an external service.
---

# Skill + CLI Generator

Reads API documentation and produces two files: a `SKILL.md` and a Python CLI script, following the Agent Skill + CLI Architecture pattern.

## What You Will Produce

Two files, always both, always together:
1. `{service}-SKILL.md` — the rulebook an AI loads to use this integration
2. `{service}-cli.py` — the Python script the AI calls to talk to the API

---

## Step 1: Read the API Documentation

The user will provide a URL, a local file, or paste content directly. Read it fully before doing anything else.

Extract and note:
- **Resources** — what nouns exist (users, orders, messages, etc.)
- **Operations** — what can be done per resource (list, get, create, update, delete)
- **Auth method** — API key, Bearer token, OAuth, Basic auth
- **Base URL** — the exact API root
- **Pagination** — cursors, next-page tokens, or offset/limit?
- **Response shapes** — what do success and error responses look like?
- **Rate limits** — anything the CLI should be aware of?

If the docs are incomplete or ambiguous, ask the user before proceeding.

---

## Step 2: Design the Command Surface

Before writing any code, decide which commands to expose. Apply these rules:

**Abstract the plumbing** — hide inside the script:
- Auth headers and token formats
- Base URL construction
- HTTP retry logic
- Raw response parsing

**Expose the knobs** — make these CLI flags:
- Filters (status, owner, date range)
- Limits and pagination cursors
- Sort order
- Output format

**Do not** create one function per use case. `orders get-recent-failed` is wrong. `orders list --status failed --limit 20` is right. Composable flags let the AI construct any combination the user needs.

**For every high-volume resource**, create both:
- An index command: returns IDs + minimal metadata only (`resource list-ids`)
- A fetch command: returns full detail for one item by ID (`resource get --id <id>`)

**For any resource that changes over time**, add cursor support to the list command so the AI can resume without re-reading data it already has.

**For every write operation**, add `--dry-run` that prints intent without executing.

---

## Step 3: Write the SKILL.md

The SKILL.md teaches a future AI how to use the CLI you are about to write. Concise enough to not burn context. Complete enough that the AI never has to guess.

Required sections:

**`## When to Use`** — name the service and list specific user intents that trigger this skill.

**`## Prerequisites`** — the exact env var name(s) to set, any one-time auth setup.

**`## Commands`** — every command with real flag examples. Always show `--output json`. Group by resource noun.

**`## Output Interpretation`** — which fields matter, what values signal a problem, what an empty result means.

**`## Error Handling`** — exit codes and stderr patterns mapped to actions. Cover at minimum: auth failure, not-found, rate limit exceeded.

---

## Step 4: Write the CLI Script

Language: **Python 3, standard library only** (`urllib`, `json`, `argparse`, `sys`, `os`). No pip installs.

### Structure (follow this order)

```
1. Shebang: #!/usr/bin/env python3
2. Module docstring: usage examples + required env vars
3. Constants: BASE_URL, DEFAULT_TIMEOUT, DEFAULT_LIMIT
4. make_request(method, path, params=None, body=None) — single HTTP helper
5. One function per subcommand
6. build_parser() — all argparse setup
7. main()
8. if __name__ == "__main__": main()
```

### Rules

- Auth: read from `os.environ` — fail immediately with a clear message if missing
- Subcommand naming: noun → verb (`orders list`, `orders get`, `orders create`)
- List commands: accept `--limit` (default 20) and `--cursor`; return `{"items": [...], "total": N, "next_cursor": "..." or null}`
- Get commands: accept `--id` (required); return single object on stdout
- Write commands: accept `--dry-run`; when set, print intent and exit 0 without calling the API
- `--output json` (default) and `--output table` on all commands
- stdout = data only. stderr = errors only. Never mix.
- Exit 0 = success, exit 1 = usage/config error, exit 2 = API error
- Timeout: 30s on all HTTP calls
- No interactive prompts

---

## Step 5: Deliver

Present both files. Then tell the user:
1. Which env var(s) to set and where to find the value
2. The first command to run to verify auth works: `python {service}-cli.py {resource} list --limit 1`
3. Any API gaps — operations you didn't implement and why

---

## Quality Check Before Delivering

**SKILL.md:**
- [ ] "When to Use" names the specific service
- [ ] Every command example uses real flag names from the actual API docs
- [ ] `--output json` shown for every command
- [ ] Error handling covers: auth failure, not-found, rate limit
- [ ] Output interpretation says what to *do* with the data, not just what fields exist

**CLI script:**
- [ ] Auth reads from env var — not hardcoded, not from args
- [ ] All subcommands follow noun→verb pattern
- [ ] List commands return the standard `{items, total, next_cursor}` shape
- [ ] Write commands have `--dry-run`
- [ ] Exit codes are correct throughout
- [ ] No interactive prompts anywhere
- [ ] Standard library only — no imports that require pip
