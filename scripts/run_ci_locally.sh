#!/bin/bash
set -e

echo "🔧 Running CI locally..."

# activate venv if exists
if [ -d ".venv" ]; then
  echo "📦 Activating virtual environment..."
  source .venv/bin/activate
else
  echo "⚠️ .venv not found — skipping activation"
fi

echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

echo "📥 Installing dependencies..."
pip install -r requirements.txt
pip install pytest

echo "🧪 Running tests..."
pytest

echo "✅ Local CI passed (same result CI would produce)!"
