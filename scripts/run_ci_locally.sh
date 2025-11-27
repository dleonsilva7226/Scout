#!/bin/bash
set -e

echo "🔧 Running CI locally..."

# activate venv if exists
if [ -d ".venv" ]; then
  echo "📦 Activating virtual environment..."
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "⚠️ .venv not found — skipping activation"
fi

echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ -f "dev-requirements.txt" ]; then
  echo "📥 Installing dev dependencies..."
  pip install -r dev-requirements.txt
else
  echo "⚠️ dev-requirements.txt not found — installing pytest directly"
  pip install pytest
fi

echo "🧪 Running tests..."
pytest

echo "✅ Local CI passed (same result CI would produce)!"
