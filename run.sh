#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"

# Find python (venv first, then system)
if [ -f "$VENV/bin/python" ]; then
    PYTHON="$VENV/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "Python 3.10+ not found. Install it then run: python3 setup.py"
    exit 1
fi

# First-time setup if no venv
if [ ! -f "$VENV/bin/python" ]; then
    echo "First time? Running setup..."
    "$PYTHON" "$ROOT/setup.py"
    if [ -f "$VENV/bin/python" ]; then
        PYTHON="$VENV/bin/python"
    fi
fi

# Auto-detect LAN IP
LAN_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}' 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

# Auto-name from hostname if not specified
HAS_NAME=0
for arg in "$@"; do
    [[ "$arg" == "--name" || "$arg" == "-n" ]] && HAS_NAME=1
done

if [ "$HAS_NAME" -eq 0 ]; then
    echo "Starting ChitChat daemon on port 9875..."
    exec "$PYTHON" -m core.daemon --name "$(hostname)"
else
    exec "$PYTHON" -m core.daemon "$@"
fi
