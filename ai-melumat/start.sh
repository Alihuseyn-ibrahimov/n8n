#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
echo "Brauzer: http://127.0.0.1:8090"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
