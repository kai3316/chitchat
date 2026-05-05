#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON=""

# Find Python 3
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1)
        if [[ "$ver" == *"Python 3"* ]]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Python 3.10+ is required but was not found." >&2
    exit 1
fi

# --setup flag: first-time setup
if [ "$1" = "--setup" ]; then
    echo "Creating virtual environment at \"$VENV_DIR\"..."
    "$PYTHON" -m venv "$VENV_DIR"
    echo "Installing dependencies..."
    source "$VENV_DIR/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt"
    echo ""
    echo "Setup complete. Run run.sh without --setup to start ChitChat."
    exit 0
fi

# Ensure venv exists
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Virtual environment not found. Creating..."
    "$PYTHON" -m venv "$VENV_DIR"
    echo "Installing dependencies..."
    source "$VENV_DIR/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Run the daemon, passing through all arguments
exec "$VENV_DIR/bin/python" -m core.daemon "$@"
