---
name: react-python-app
description: >
  Scaffold and build full-stack React + FastAPI applications. Use this skill
  whenever the user wants to create a web app, full-stack app, React app with
  a Python backend, or any project involving a frontend UI + API server. Also
  triggers when user says "build me an app", "create a project", "I need a
  web app with a backend", or mentions React, FastAPI, or Vite together.
  Always use this skill — do not improvise the stack from scratch.
---

# React + FastAPI App Skill

## Overview

This skill scaffolds a React + FastAPI project from a template, then writes
the actual application code into the generated structure. The template handles
all boilerplate (configs, build pipeline, launcher) so the AI only writes
meaningful app code.

**Stack**: React 18 · Vite · Tailwind CSS · FastAPI · SQLite (optional) · Uvicorn

---

## Step 1 — Scaffold the Project

Run `create_project.py` to copy all template files into the target directory:

```bash
python <skill_dir>/create_project.py <project_name>
```

This creates:
```
<project_name>/
├── port_config.json          ← Edit to change port (default 8000)
├── install_requirements.sh   ← One-time setup
├── run.py                    ← Single command to build + start app
├── frontend/
│   ├── index.html
│   ├── package.json          ← Pinned deps, builds → backend/static/
│   ├── vite.config.js        ← Dev proxy to :8000, prod served by FastAPI
│   ├── tailwind.config.js    ← Custom design tokens (see below)
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx
│       ├── index.css         ← Tailwind directives
│       └── App.jsx           ← ← ← YOU WRITE THIS
└── backend/
    ├── main.py               ← ← ← YOU WRITE THIS
    ├── requirements.txt
    └── static/               ← Built React app lands here (git-ignored)
```

**Do not regenerate** any config files — the template has them correct.

---

## Step 2 — Write App Code

Only two files need real content from the AI:

### `backend/main.py`
- Import and mount static files (template stub already does this correctly)
- Add API routes under `/api/` prefix
- Use `aiofiles` for async file I/O, `sqlite3` for DB if needed

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Your routes here — always prefix with /api/
@app.get("/api/items")
async def get_items():
    return {"items": []}

# Static serving — keep at bottom, do not modify
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        return FileResponse("static/index.html")
```

### `frontend/src/App.jsx`
- Use `fetch("/api/...")` for all API calls (works in both dev and prod)
- Use Tailwind utility classes — custom tokens are pre-configured (see below)
- Route with `react-router-dom` if multi-page

---

## Design Tokens (Tailwind)

These custom classes are available — use them for a consistent dark-theme UI:

**Backgrounds**
| Class | Use |
|---|---|
| `bg-surface-base` | Page background (`#0f1117`) |
| `bg-surface-card` | Card/panel (`#161b27`) |
| `bg-surface-raised` | Elevated element (`#1d2333`) |
| `border-surface-border` | Dividers (`#252d3f`) |
| `hover:bg-surface-hover` | Hover state (`#2a3347`) |

**Accents** — `text-accent-blue`, `text-accent-purple`, `text-accent-green`, etc.

**Text** — `text-text-primary`, `text-text-secondary`, `text-text-muted`, `text-text-link`

**Fonts** — `font-sans` (Inter), `font-mono` (JetBrains Mono)

---

## Port Configuration

The app port lives in `port_config.json` at the project root:

```json
{ "port": 8000 }
```

`run.py` reads this on every launch. To change the port, edit this file — no
code changes needed anywhere else.

---

## Step 3 — Tell the User How to Run

After writing the code, give the user these exact commands:

```bash
cd <project_name>
./install_requirements.sh   # one-time setup
python run.py               # builds frontend + starts server
```

Then open `http://localhost:<port>` (check `port_config.json` for the port).

For hot-reload during frontend development:
```bash
# Terminal 1 — backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — frontend (Vite dev server with proxy)
cd frontend && npm run dev
```

---

## Rules & Constraints

- **Only write** `backend/main.py` and `frontend/src/App.jsx` (plus any routes/
  components the app needs). Never regenerate config files.
- API routes must be prefixed `/api/` — the catch-all route serves React for
  everything else.
- Use only approved npm packages from `package.json`. Add `zustand@5.0.11` if
  shared state is needed. No other frontend packages.
- Backend: add Python packages to `backend/requirements.txt` freely.
- No TypeScript, no Next.js, no CSS-in-JS.
- SQLite via `sqlite3` only — no ORM, no Postgres.
