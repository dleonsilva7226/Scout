#!/bin/bash

set -e

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "[+] Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate venv
echo "[+] Activating virtual environment..."
# shellcheck disable=SC1091
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

echo "[✓] Environment ready."
echo "Run: source .venv/bin/activate"
