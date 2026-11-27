#!/usr/bin/env python3
"""ChitChat one-click cross-platform installer.

Usage:
    python install.py              # auto-detect, install deps, create launchers
    python install.py --relay URL  # also configure relay server

This script works on Windows, macOS, and Linux. It creates a virtual
environment, installs Python dependencies, and generates OS-specific
launcher shortcuts.

Note: this is the end-user installer, not a setuptools script. The
package metadata lives in pyproject.toml, so ``pip install .`` installs
the daemon without ever running this file.
"""

import argparse
import os
import shutil
import subprocess
import sys
import venv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")


def detect_os():
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


MIN_PYTHON = (3, 10)


def _version_ok(cmd):
    """Return True when ``cmd`` is a Python >= MIN_PYTHON interpreter."""
    try:
        out = subprocess.check_output(
            [cmd, "--version"], stderr=subprocess.STDOUT, text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return False
    # Expect "Python 3.12.4"; keep only the numeric part.
    match = out.strip().split()
    if len(match) < 2:
        return False
    try:
        parts = tuple(int(p) for p in match[1].split(".")[:2])
    except ValueError:
        return False
    return parts >= MIN_PYTHON


def find_python():
    """Find the best Python >= 3.10 interpreter to build the venv with."""
    # The interpreter running this script is the safest choice.
    candidates = [sys.executable, "python3", "python", "py"]
    for cmd in candidates:
        if not cmd:
            continue
        if _version_ok(cmd):
            return cmd

    print(f"ERROR: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required. "
          "Install it from https://python.org")
    sys.exit(1)


def create_venv():
    """Create virtual environment if it doesn't exist."""
    if os.path.exists(os.path.join(VENV_DIR, "pyvenv.cfg")):
        print(f"  Virtual environment already exists: {VENV_DIR}")
        return

    print("  Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)


def pip_install():
    """Install dependencies into the venv. Returns True on success."""
    req = os.path.join(SCRIPT_DIR, "requirements.txt")
    if not os.path.exists(req):
        print("  WARNING: requirements.txt not found, skipping pip install")
        return True

    if sys.platform == "win32":
        pip = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:
        pip = os.path.join(VENV_DIR, "bin", "pip")

    print("  Installing dependencies...")
    try:
        subprocess.check_call([pip, "install", "-r", req, "--quiet"])
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"\n  ERROR: dependency installation failed ({exc}).")
        print("  Check your internet connection, then run: python install.py")
        return False
    return True


def create_windows_shortcut(name, args=""):
    """Create a .bat shortcut on Windows.

    The launcher must run ``-m core.daemon`` from the project root: running
    ``core/daemon.py`` directly puts ``core/`` on sys.path and the
    ``import core.*`` statements fail.
    """
    bat_path = os.path.join(SCRIPT_DIR, f"{name}.bat")
    python = os.path.join(VENV_DIR, "Scripts", "python.exe")
    content = (
        "@echo off\r\n"
        'cd /d "%~dp0"\r\n'
        f'"{python}" -m core.daemon {args} %*\r\n'
        "pause\r\n"
    )

    with open(bat_path, "w", newline="") as f:
        f.write(content)
    print(f"  Launcher created: {bat_path}")


def create_linux_shortcut(name, args=""):
    """Create a shell launcher (Linux and macOS).

    ``readlink -f`` is intentionally not used: macOS ships a BSD
    ``readlink`` that does not support ``-f`` until very recent versions.
    Changing into the script's own directory works everywhere.
    """
    sh_path = os.path.join(SCRIPT_DIR, name)
    python = os.path.join(VENV_DIR, "bin", "python")
    content = (
        '#!/bin/sh\n'
        'cd "$(dirname "$0")" || exit 1\n'
        f'exec "{python}" -m core.daemon {args} "$@"\n'
    )

    with open(sh_path, "w") as f:
        f.write(content)
    os.chmod(sh_path, 0o755)
    print(f"  Launcher created: {sh_path}")

    # .desktop file for the Linux app menu (not used on macOS)
    if sys.platform != "darwin":
        desktop_dir = os.path.expanduser("~/.local/share/applications")
        os.makedirs(desktop_dir, exist_ok=True)
        desktop_path = os.path.join(desktop_dir, f"chitchat-{name}.desktop")

        if name == "chitchat":
            icon = os.path.join(SCRIPT_DIR, "icon.png")
            icon_line = f"Icon={icon}\n" if os.path.exists(icon) else ""
            desktop_content = f"""[Desktop Entry]
Name=ChitChat
Comment=Secure P2P Chat
Exec={sh_path}
{icon_line}Terminal=true
Type=Application
Categories=Network;Chat;
Keywords=chat;p2p;encrypted;
"""
            with open(desktop_path, "w") as f:
                f.write(desktop_content)
            os.chmod(desktop_path, 0o644)
            print(f"  Desktop entry: {desktop_path}")


def create_macos_app():
    """Create a macOS .app bundle wrapper that opens the web UI."""
    app_dir = os.path.join(SCRIPT_DIR, "ChitChat.app")
    macos_dir = os.path.join(app_dir, "Contents", "MacOS")
    resources_dir = os.path.join(app_dir, "Contents", "Resources")
    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)

    python = os.path.join(VENV_DIR, "bin", "python")

    # Info.plist
    plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>ChitChat</string>
    <key>CFBundleDisplayName</key><string>ChitChat</string>
    <key>CFBundleIdentifier</key><string>chat.chitchat.app</string>
    <key>CFBundleVersion</key><string>1.0.0</string>
    <key>CFBundleShortVersionString</key><string>1.0.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleExecutable</key><string>chitchat.sh</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>LSUIElement</key><true/>
</dict>
</plist>"""

    with open(os.path.join(app_dir, "Contents", "Info.plist"), "w") as f:
        f.write(plist)

    # Executable: start the daemon, then open the browser once it is up.
    launcher = f"""#!/bin/bash
cd "{SCRIPT_DIR}" || exit 1
( sleep 3; open http://127.0.0.1:9875 ) &
exec "{python}" -m core.daemon "$@"
"""
    launcher_path = os.path.join(macos_dir, "chitchat.sh")
    with open(launcher_path, "w") as f:
        f.write(launcher)
    os.chmod(launcher_path, 0o755)

    print(f"  macOS app: {app_dir}")


def save_config(relay_url=""):
    """Save the daemon config file into the active data directory."""
    data_dir = os.environ.get("CHITCHAT_HOME", "").strip() or os.path.join(
        os.path.expanduser("~"), ".chitchat")
    config_dir = os.path.abspath(os.path.expanduser(data_dir))
    os.makedirs(config_dir, exist_ok=True)

    import json

    cfg_path = os.path.join(config_dir, "config.json")
    cfg = {}
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)

    if relay_url:
        cfg["relay_url"] = relay_url

    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"  Config saved: {cfg_path}")


# ── main ──────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="ChitChat cross-platform installer")
    p.add_argument("--relay", default="", help="Relay server URL for cross-LAN messaging")
    p.add_argument("--no-shortcuts", action="store_true", help="Skip creating launchers")
    args = p.parse_args()

    os_type = detect_os()
    print(f"\n  ChitChat Installer")
    print(f"  OS: {os_type}")
    print(f"  Project: {SCRIPT_DIR}\n")

    # Step 1: Find Python
    python = find_python()
    print(f"  Python: {python}")

    # Step 2: Create venv
    create_venv()

    # Step 3: Install dependencies
    if not pip_install():
        sys.exit(1)

    # Step 4: Save config
    save_config(args.relay)

    # Step 5: Create launchers
    if not args.no_shortcuts:
        if os_type == "windows":
            create_windows_shortcut("Start-ChitChat", "--name My-PC")
        elif os_type == "macos":
            create_linux_shortcut("chitchat", "--name My-Mac")
            create_macos_app()
        else:
            create_linux_shortcut("chitchat", "--name My-Linux")

    # Step 6: Print instructions
    print(f"""
+------------------------------------------------------+
|              ChitChat Setup Complete!                 |
|                                                      |
|  Start the daemon:                                   |""")

    if os_type == "windows":
        print(r"|    .\Start-ChitChat.bat                             |")
    else:
        print(r"|    ./chitchat                                       |")

    print(f"""|                                                      |
|  Then open in browser:                               |
|    http://localhost:9875                             |
|                                                      |
|  On another device:                                  |
|    1. Copy this entire folder to the other device    |
|    2. Run: python install.py                         |
|    3. Start the daemon and open the Web UI           |
|    4. Both devices auto-discover on the same LAN     |
|                                                      |
+------------------------------------------------------+
""")


if __name__ == "__main__":
    main()
