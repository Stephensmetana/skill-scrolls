---
name: python-dev
description: >
  Standards and conventions for creating, running, and managing Python projects.
  Use this skill whenever you are building a new Python app, adding libraries to
  an existing one, running a Python script, or setting up project structure.
  Triggers include: any Python file creation, pip install mentions, requirements,
  virtual environments, "make a python app", "run my python script", or any
  request to build something in Python. Always consult this skill before writing
  Python project scaffolding or choosing how to install or run a Python app.
---

# Python Development Standards

This skill defines how to structure, install, and run Python projects consistently.
The goal: projects that any developer (or the AI in a future session) can pick up
and run without guesswork.

---

## Decision: Does This Project Need pip Packages?

Ask this first. It determines the entire project structure.

| Situation | What to create |
|---|---|
| No external pip packages needed | Just `main.py` (and other `.py` files). No scripts needed. |
| One or more pip packages needed | `requirements.txt` + `install_requirements.sh` + `run_app.sh` |

---

## Projects WITH pip Dependencies

### Required Files

**`requirements.txt`** — lists all pip packages the app needs.

```
# requirements.txt
requests==2.31.0
flask>=3.0.0
pandas
```

Guidelines for `requirements.txt`:
- One package per line
- Pin versions with `==` for reproducible installs (preferred for apps)
- Use `>=` when the project is a library or needs flexibility
- Only include **direct** dependencies — not transitive ones
- Add a comment at the top if the list is long, grouping related packages
- Do NOT include dev-only tools here (linters, test runners) — see below

**`install_requirements.sh`** — creates the .venv and installs packages.

Copy from `assets/install_requirements.sh`. Do not modify unless there is a
specific reason (e.g., a post-install step is needed).

**`run_app.sh`** — activates the .venv and runs the app.

Copy from `assets/run_app.sh`. Update the `APP_FILE` variable at the top if the
entry point is not `main.py`.

### Optional but Recommended

**`.gitignore`** — always include if git is involved. At minimum:

```
.venv/
__pycache__/
*.pyc
.env
```

**`requirements_dev.txt`** — for dev-only tools (linters, formatters, test runners).
These should NOT be in `requirements.txt`.

```
# requirements_dev.txt
pytest>=8.0
black
flake8
mypy
```

---

## Projects WITHOUT pip Dependencies

Keep it simple. Just create the Python files. No scripts, no venv, no
`requirements.txt`. Running is just:

```bash
python3 main.py
```

Don't over-engineer it. A script that only uses the standard library doesn't
need a virtual environment.

---

## File Naming Conventions

| File | Purpose |
|---|---|
| `main.py` | Entry point — what gets run. Always use this name. |
| `requirements.txt` | Runtime pip dependencies |
| `requirements_dev.txt` | Dev-only dependencies (optional) |
| `install_requirements.sh` | Creates .venv + installs requirements |
| `run_app.sh` | Activates .venv + runs main.py |
| `.gitignore` | Excludes `.venv/`, `__pycache__/`, `.env` from git |
| `.env` | Secrets and config (never committed to git) |

---

## Running the App

When executing a Python app in the bash tool:

1. **Check if `run_app.sh` exists.** If it does, always use it:
   ```bash
   bash run_app.sh
   ```

2. **If `run_app.sh` does not exist** (stdlib-only project), run directly:
   ```bash
   python3 main.py
   ```

Never run `python main.py` directly if `run_app.sh` is present — the script
handles .venv activation and ensures the right Python binary is used.

---

## Creating a New Project — Checklist

When building a new Python app from scratch:

- [ ] Identify all pip packages needed
- [ ] Create `main.py` as the entry point
- [ ] Create additional `.py` modules as needed (keep files focused)
- [ ] If pip packages are needed:
  - [ ] Create `requirements.txt` with pinned or bounded versions
  - [ ] Copy `install_requirements.sh` from assets (update if needed)
  - [ ] Copy `run_app.sh` from assets (update `APP_FILE` if entry point ≠ `main.py`)
  - [ ] Create `.gitignore` excluding `.venv/`, `__pycache__/`, `.env`
- [ ] If no pip packages: just the `.py` files

### New Project File Layout

With dependencies:
```
my-project/
├── main.py
├── requirements.txt
├── install_requirements.sh
├── run_app.sh
├── .gitignore
├── .venv/
└── (other .py modules)
```

Without dependencies:
```
my-project/
├── main.py
└── (other .py modules)
```

---

## Adding Dependencies to an Existing Project

If a new pip package is needed during development:

1. Add it to `requirements.txt` (with version pin)
2. If `install_requirements.sh` doesn't exist yet, create it now
3. If `run_app.sh` doesn't exist yet, create it now
4. Re-run `bash install_requirements.sh` to update the .venv

---

## Python Code Quality Baseline

Even without a full linting setup, follow these minimums:

- Use `if __name__ == "__main__":` in `main.py` to guard the entry point
- Use type hints on function signatures where practical
- Keep functions small and single-purpose
- Put constants at the top of files in UPPER_SNAKE_CASE
- Use `.env` + `python-dotenv` for secrets and config — never hardcode them
- Handle exceptions explicitly; avoid bare `except:` clauses

---

## Assets Reference

The `assets/` directory contains the canonical shell scripts:

- `assets/install_requirements.sh` — copy this verbatim when creating a new project
- `assets/run_app.sh` — copy this and update `APP_FILE` if the entry point isn't `main.py`

These scripts are intentionally simple and stable. Modify them only when a
project has a specific need (e.g., environment variable setup before install,
running a different command after activation).
