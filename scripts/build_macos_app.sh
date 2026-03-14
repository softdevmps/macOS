#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

source .venv/bin/activate
python -m pip install pyinstaller
pyinstaller --noconfirm packaging/macos/ScreenCaptureHelper.spec

echo "Build listo en: $ROOT_DIR/dist/ScreenCaptureHelper.app"
