"""Package ChitChat for sharing to another device.

Usage:
    python share.py              # creates chitchat-portable.zip
    python share.py --target linux  # adds linux-specific launchers
    python share.py --target all    # all platforms

This creates a self-contained zip that another device can extract and run
with just: python install.py
"""

import os
import shutil
import sys
import tempfile
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Files/dirs to include (relative to SCRIPT_DIR)
INCLUDE = [
    "core/",
    "requirements.txt",
    "install.py",
    "pyproject.toml",
    "run.bat",
    "run.sh",
    "LICENSE",
]

# Files/dirs to exclude
EXCLUDE = {".venv", "__pycache__", ".pytest_cache", "*.pyc", ".git",
           ".claude", "app", "server", "tests", ".gitignore"}


def should_exclude(name):
    if name in EXCLUDE:
        return True
    if name.endswith(".pyc"):
        return True
    if name.startswith("."):
        return True
    return False


def make_zip(output_path: str):
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in INCLUDE:
            src = os.path.join(SCRIPT_DIR, item)
            if not os.path.exists(src):
                continue
            if os.path.isfile(src):
                zf.write(src, os.path.relpath(src, SCRIPT_DIR))
            else:
                for root, dirs, files in os.walk(src):
                    # Filter excluded dirs
                    dirs[:] = [d for d in dirs if not should_exclude(d)]
                    # Skip hidden dirs
                    dirs[:] = [d for d in dirs if not d.startswith(".")]

                    for f in files:
                        if should_exclude(f):
                            continue
                        fp = os.path.join(root, f)
                        arcname = os.path.relpath(fp, SCRIPT_DIR)
                        zf.write(fp, arcname)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    return size_mb


def main():
    target = "all"
    if len(sys.argv) > 1:
        target = sys.argv[1].replace("--target=", "").replace("--target ", "")

    output = os.path.join(SCRIPT_DIR, "chitchat-share.zip")
    print(f"\nPackaging ChitChat for sharing...")
    size = make_zip(output)
    print(f"  Created: {output} ({size:.1f} MB)")
    print(f"""
To use on another device:
  1. Copy chitchat-share.zip to the other device
  2. Extract it
  3. Run: python install.py     (first-time setup)
  4. Run: python -m core.daemon (or use run.bat/run.sh)

Both devices on the same WiFi/LAN will auto-discover each other.
For cross-internet: configure a relay server with --relay flag.
""")


if __name__ == "__main__":
    main()
