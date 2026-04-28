#!/bin/bash

APP_FILE="main.py"  # Change this to your desired Python filename
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
else
    # Try to find python or python3
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "Neither python nor python3 found. Please install Python."
        read -p "Press enter to exit"
        exit 1
    fi
fi

# Run the Python app
$PYTHON_CMD "$APP_FILE"

# Keep terminal open after execution
read -p "Press enter to exit"
