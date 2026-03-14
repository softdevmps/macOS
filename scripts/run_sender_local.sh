#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

source .venv/bin/activate
SERVER_URL="${SERVER_URL:-http://127.0.0.1:5050/upload}"
export SERVER_URL
exec python sender/sender.py
