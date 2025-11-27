#!/bin/bash

set -e

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "[+] Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate venv
echo "[+] Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "[+] Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
  echo "[+] Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
else
  echo "[!] requirements.txt not found!"
  exit 1
fi

# Install dev dependencies if file exists
if [ -f "dev-requirements.txt" ]; then
  echo "[+] Installing development dependencies from dev-requirements.txt..."
  pip install -r dev-requirements.txt
else
  echo "[i] No dev-requirements.txt found — skipping dev deps."
fi

echo "[✓] Environment ready."
echo "Run: source .venv/bin/activate"
