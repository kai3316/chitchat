#!/usr/bin/env bash
# Start ChitChat. Creates the virtual environment on first run, then
# launches the daemon and opens the Web UI in a browser.
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
VENV="$ROOT/.venv"

# ── Locate a Python interpreter ─────────────────────────────────
PYTHON=""
if [ -x "$VENV/bin/python" ]; then
    PYTHON="$VENV/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "Python 3.10+ not found. Install it, then run: python3 install.py"
    exit 1
fi

# ── First run: create the virtual environment ───────────────────
if [ ! -x "$VENV/bin/python" ]; then
    echo "First run - setting up the Python environment..."
    "$PYTHON" "$ROOT/install.py" --no-shortcuts
    if [ -x "$VENV/bin/python" ]; then
        PYTHON="$VENV/bin/python"
    fi
fi

# ── Read --http-port / --name from the arguments ────────────────
HTTP_PORT=9875
HAS_NAME=0
SHOW_HELP=0
ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --http-port)
            HTTP_PORT="$2"
            ARGS+=("$1" "$2")
            shift 2
            ;;
        --name|-n)
            HAS_NAME=1
            ARGS+=("$1" "$2")
            shift 2
            ;;
        --help|-h)
            SHOW_HELP=1
            ARGS+=("$1")
            shift
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

if [ "$SHOW_HELP" -eq 1 ]; then
    exec "$PYTHON" -m core.daemon --help
fi

if [ "$HAS_NAME" -eq 0 ]; then
    ARGS+=("--name" "$(hostname)")
fi

echo ""
echo "  Starting ChitChat (Web UI: http://127.0.0.1:$HTTP_PORT)"
echo "  Press Ctrl+C to stop."
echo ""

open_browser() {
    sleep 3
    URL="http://127.0.0.1:$HTTP_PORT"
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open "$URL" >/dev/null 2>&1 &
    fi
}
open_browser &

exec "$PYTHON" -m core.daemon "${ARGS[@]}"
