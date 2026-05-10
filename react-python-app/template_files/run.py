#!/usr/bin/env python3
"""
Single-command launcher: builds the React frontend, then starts FastAPI.
Edit port_config.json to change the port.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
PORT_CONFIG = ROOT / "port_config.json"
FRONTEND_DIR = ROOT / "frontend"
BACKEND_DIR = ROOT / "backend"


def load_port() -> int:
    try:
        return int(json.loads(PORT_CONFIG.read_text())["port"])
    except Exception:
        print("⚠️  Could not read port_config.json — defaulting to port 8000")
        return 8000


def build_frontend():
    if not FRONTEND_DIR.exists():
        print("⚠️  No frontend/ directory found — skipping build.")
        return

    print("📦 Installing frontend dependencies...")
    subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True)

    print("🔨 Building frontend → backend/static/ ...")
    subprocess.run(["npm", "run", "build"], cwd=FRONTEND_DIR, check=True)
    print("✅ Frontend built.\n")


def start_backend(port: int):
    venv_python = ROOT / "venv" / "bin" / "python"
    uvicorn_cmd = (
        [str(venv_python), "-m", "uvicorn"]
        if venv_python.exists()
        else ["uvicorn"]
    )

    print(f"🚀 Starting app at http://localhost:{port}\n")
    os.chdir(BACKEND_DIR)
    subprocess.run(uvicorn_cmd + ["main:app", "--port", str(port), "--reload"])


if __name__ == "__main__":
    port = load_port()
    try:
        build_frontend()
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend build failed: {e}")
        sys.exit(1)
    start_backend(port)
