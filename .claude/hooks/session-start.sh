#!/bin/bash
set -euo pipefail

# Only run in remote (web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

echo "=== VLBH Energy MCP — Session Start Hook ==="

# --- Python dependencies ---
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
  pip install -q -r requirements.txt
  echo "Python dependencies installed."
else
  echo "No requirements.txt found, skipping Python setup."
fi

# --- Swift Package resolution ---
echo "Resolving Swift Package dependencies..."
if [ -f "Package.swift" ]; then
  if command -v swift &> /dev/null; then
    swift package resolve 2>/dev/null || echo "Swift not available in this environment, skipping."
  else
    echo "Swift toolchain not available, skipping SPM resolution."
  fi
else
  echo "No Package.swift found, skipping Swift setup."
fi

# --- Validate Python imports ---
echo "Validating Python backend..."
python -c "from main import app; print(f'FastAPI app loaded: {len(app.routes)} routes')" 2>/dev/null || echo "Warning: Python validation failed."

echo "=== Session Start Hook complete ==="
