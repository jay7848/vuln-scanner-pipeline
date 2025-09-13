#!/usr/bin/env bash
set -euo pipefail

### ---------------------------
### Helpers
### ---------------------------
die() { echo "ERROR: $*" >&2; exit 1; }

# pick a python
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  die "Python not found. Install Python 3.10+ (Windows/WSL: sudo apt install -y python3)."
fi

### ---------------------------
### Ensure we're at repo root
### ---------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

### ---------------------------
### Make `scanner` importable
### ---------------------------
# 1) ensure package marker
[ -f scanner/__init__.py ] || touch scanner/__init__.py

# 2) ensure repo root is importable for any child Python process
export PYTHONPATH="${PYTHONPATH:-.}:."

### ---------------------------
### Virtualenv (best effort)
### ---------------------------
if [ ! -d ".venv" ]; then
  if ! $PY -m venv .venv 2>/dev/null; then
    echo "Note: venv creation failed (likely missing ensurepip/venv)."
    echo "On Ubuntu/WSL, run:  sudo apt update && sudo apt install -y python3-venv"
    echo "Continuing with system Python…"
  fi
fi

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

### ---------------------------
### Python deps
### ---------------------------
if [ -f requirements.txt ]; then
  pip install -q --upgrade pip
  pip install -q -r requirements.txt
else
  echo "No requirements.txt found at repo root; skipping pip install."
fi

### ---------------------------
### Docker preflight
### ---------------------------
command -v docker >/dev/null 2>&1 || die "Docker not found. Start Docker Desktop and ensure 'docker' works in this shell."
docker info >/dev/null 2>&1 || die "Docker daemon not reachable. Start Docker Desktop and retry."

### ---------------------------
### Build demo image
### ---------------------------
IMAGE="demo-app:dev"
docker build -f DemoApp.Dockerfile -t "$IMAGE" .

### ---------------------------
### Scan + Report
### ---------------------------
mkdir -p reports

# Run as modules so 'scanner' is importable regardless of cwd
$PY -m scanner.scan "$IMAGE" "reports/demo-app.json"
$PY -m scanner.report "reports/demo-app.filtered.json" "reports/demo-app.html"

### ---------------------------
### Email (optional)
### ---------------------------
# This will send only if your script is configured to look at env vars or CLI flags;
# keep it here if your process expects to always attempt email.
$PY -m scanner.notify_email \
  --image "$IMAGE" \
  --report-json "reports/demo-app.filtered.json" \
  --report-html "reports/demo-app.html"

echo "Done. Reports are in ./reports"
