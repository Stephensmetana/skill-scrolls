#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
echo "✅ Python dependencies installed."

echo ""
echo "📦 Installing frontend npm packages..."
cd frontend && npm install
echo "✅ Frontend packages installed."

echo ""
echo "🎉 Setup complete! Run the app with:"
echo "   python run.py"
