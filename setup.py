#!/usr/bin/env python3
"""ChitChat one-click cross-platform installer.

Usage:
    python setup.py              # auto-detect, install deps, create launchers
    python setup.py --relay URL  # also configure relay server

This script works on Windows, macOS, and Linux. It creates a virtual
environment, installs Python dependencies, and generates OS-specific
launcher shortcuts.
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


def find_python():
    """Find the best Python 3 interpreter."""
    # Python 3.13+ on Windows might be in Windows Apps
    for cmd in ["python3", "python"]:
        try:
            out = subprocess.check_output(
                [cmd, "--version"], stderr=subprocess.STDOUT, text=True
            )
            if "Python 3" in out:
                return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    print("ERROR: Python 3.10+ is required. Install from https://python.org")
    sys.exit(1)


def create_venv():
    """Create virtual environment if it doesn't exist."""
    if os.path.exists(VENV_DIR):
        print(f"  Virtual environment already exists: {VENV_DIR}")
        return

    print(f"  Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)


def pip_install():
    """Install dependencies into the venv."""
    req = os.path.join(SCRIPT_DIR, "requirements.txt")
    if not os.path.exists(req):
        print("  WARNING: requirements.txt not found, skipping pip install")
        return

    if sys.platform == "win32":
        pip = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:
        pip = os.path.join(VENV_DIR, "bin", "pip")

    print("  Installing dependencies...")
    subprocess.check_call([pip, "install", "-r", req, "--quiet"])


def create_windows_shortcut(name, target, args=""):
    """Create a .bat shortcut on Windows."""
    bat_path = os.path.join(SCRIPT_DIR, f"{name}.bat")
    if target.endswith(".py"):
        python = os.path.join(VENV_DIR, "Scripts", "python.exe")
        content = f'@"{python}" "{target}" {args} %*\npause\n'
    else:
        content = f'@"{target}" {args} %*\n'

    with open(bat_path, "w") as f:
        f.write(content)
    print(f"  Launcher created: {bat_path}")


def create_linux_shortcut(name, target, args=""):
    """Create a shell launcher and .desktop file on Linux."""
    # Shell script
    sh_path = os.path.join(SCRIPT_DIR, name)
    if target.endswith(".py"):
        python = os.path.join(VENV_DIR, "bin", "python")
        content = f'#!/usr/bin/env bash\ncd "$(dirname "$BASH_SOURCE")"\nexec "{python}" "{target}" {args} "$@"\n'
    else:
        content = f'#!/usr/bin/env bash\ncd "$(dirname "$BASH_SOURCE")"\nexec "{target}" {args} "$@"\n'

    with open(sh_path, "w") as f:
        f.write(content)
    os.chmod(sh_path, 0o755)
    print(f"  Launcher created: {sh_path}")

    # .desktop file for app menu
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(desktop_dir, exist_ok=True)
    desktop_path = os.path.join(desktop_dir, f"chitchat-{name}.desktop")
    icon = os.path.join(SCRIPT_DIR, "icon.png")

    # Determine if this is the daemon or just a helper
    if name == "chitchat":
        desktop_content = f"""[Desktop Entry]
Name=ChitChat
Comment=Secure P2P Chat
Exec={sh_path}
Icon={icon}
Terminal=true
Type=Application
Categories=Network;Chat;
Keywords=chat;p2p;encrypted;
"""
        with open(desktop_path, "w") as f:
            f.write(desktop_content)
        os.chmod(desktop_path, 0o644)
        print(f"  Desktop entry: {desktop_path}")


def create_macos_app():
    """Create a macOS .app bundle wrapper."""
    app_dir = os.path.join(SCRIPT_DIR, "ChitChat.app")
    macos_dir = os.path.join(app_dir, "Contents", "MacOS")
    resources_dir = os.path.join(app_dir, "Contents", "Resources")
    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)

    python = os.path.join(VENV_DIR, "bin", "python")
    daemon_path = os.path.join(SCRIPT_DIR, "core", "daemon.py")

    # Info.plist
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>ChitChat</string>
    <key>CFBundleIdentifier</key><string>chat.chitchat.app</string>
    <key>CFBundleVersion</key><string>1.0.0</string>
    <key>CFBundleExecutable</key><string>chitchat.sh</string>
    <key>LSUIElement</key><true/>
</dict>
</plist>"""

    with open(os.path.join(app_dir, "Contents", "Info.plist"), "w") as f:
        f.write(plist)

    # Executable
    launcher = f"""#!/usr/bin/env bash
cd "{SCRIPT_DIR}"
exec "{python}" -m core.daemon "$@"
"""
    launcher_path = os.path.join(macos_dir, "chitchat.sh")
    with open(launcher_path, "w") as f:
        f.write(launcher)
    os.chmod(launcher_path, 0o755)

    print(f"  macOS app: {app_dir}")


def save_config(relay_url=""):
    """Save daemon config file."""
    config_dir = os.path.join(os.path.expanduser("~"), ".chitchat")
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
    pip_install()

    # Step 4: Save config
    save_config(args.relay)

    # Step 5: Create launchers
    if not args.no_shortcuts:
        daemon = os.path.join(SCRIPT_DIR, "core", "daemon.py")
        if os_type == "windows":
            create_windows_shortcut("Start-ChitChat", daemon, "--name My-PC")
        elif os_type == "macos":
            create_linux_shortcut("chitchat", daemon, "--name My-Mac")
            create_macos_app()
        else:
            create_linux_shortcut("chitchat", daemon, "--name My-Linux")

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
|    2. Run: python setup.py                           |
|    3. Start the daemon and open the Web UI           |
|    4. Both devices auto-discover on the same LAN     |
|                                                      |
+------------------------------------------------------+
""")


if __name__ == "__main__":
    main()
