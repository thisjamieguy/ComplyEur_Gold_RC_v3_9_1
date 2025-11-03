#!/usr/bin/env bash
set -euo pipefail

# Activate venv if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

HOST="127.0.0.1"
PORT="5001"

# Find first free port in range 5001-5010
TRY=$PORT
for p in $(seq 5001 5010); do
  STATUS=$(python3 - <<PYEOF
import socket
s = socket.socket()
try:
    s.bind(('127.0.0.1', $p))
    s.close()
    print("FREE")
except OSError:
    print("BUSY")
PYEOF
)
  if [ "$STATUS" = "FREE" ]; then
    TRY=$p
    break
  fi
done

echo "➡️  Starting app on http://${HOST}:${TRY}/login"
export PORT=$TRY
export HOST=$HOST
python run_auth.py

