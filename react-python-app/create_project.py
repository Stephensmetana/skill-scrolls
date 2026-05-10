#!/usr/bin/env python3
"""
Creates a new React + FastAPI project by copying template files.
Usage: python create_project.py <target_directory>
"""
import os
import sys
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
TEMPLATES = SCRIPT_DIR / "template_files"


def create_project(target: str):
    dest = Path(target).resolve()

    if not TEMPLATES.exists():
        print(f"❌ template_files/ not found at {TEMPLATES}")
        sys.exit(1)

    print(f"Creating project at: {dest}\n")

    # Copy entire template tree
    shutil.copytree(TEMPLATES, dest, dirs_exist_ok=True)

    # Make scripts executable
    for script in [dest / "install_requirements.sh", dest / "run.py"]:
        if script.exists():
            script.chmod(0o755)

    print("✅ Project created!\n")
    print("Next steps:")
    print(f"  cd {dest}")
    print(f"  ./install_requirements.sh")
    print(f"  python run.py")
    print(f"\nTo change the port, edit port_config.json before running.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_project.py <target_directory>")
        sys.exit(1)

    target = sys.argv[1]
    if Path(target).exists():
        print(f"⚠️  Directory '{target}' already exists. Files will be merged/overwritten.")

    try:
        create_project(target)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
