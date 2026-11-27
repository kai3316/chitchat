"""ChitChat daemon configuration.

The data directory resolution order is:

1. the ``--data-dir`` command-line option
2. the ``CHITCHAT_HOME`` environment variable
3. ``~/.chitchat``

Everything ChitChat persists — device identity, TLS key material, the
SQLite database and ``config.json`` — lives inside that single directory,
so the app never writes next to another program's files.
"""

import json
import os
import tempfile

DEFAULT_CONFIG = {
    "device_name": "",
    "p2p_port": 9877,
    "ws_port": 9876,
    "http_port": 9875,
    "http_bind": "0.0.0.0",
    "ws_bind": "0.0.0.0",
    "relay_url": "",
    "relay_enabled": False,
    "debug": False,
    "auto_accept_pairs": False,
}

CONFIG_FILENAME = "config.json"

# Resolved lazily by ``configure()`` (or by the module import defaults).
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".chitchat")


def _env_data_dir() -> str:
    """Return the data directory requested by the environment, if any."""
    env = os.environ.get("CHITCHAT_HOME", "").strip()
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return ""


def _default_data_dir() -> str:
    return _env_data_dir() or os.path.join(os.path.expanduser("~"), ".chitchat")


# Apply the environment override at import time so that submodules which
# ``from core.config import CONFIG_DIR`` see the right directory.
CONFIG_DIR = _default_data_dir()


def configure(data_dir: str = "") -> str:
    """Pin the data directory for this process and return it.

    Passing an empty string re-resolves from the environment.  Call this
    before constructing the daemon when the directory comes from a CLI
    flag.
    """
    global CONFIG_DIR
    if data_dir:
        CONFIG_DIR = os.path.abspath(os.path.expanduser(data_dir))
    else:
        CONFIG_DIR = _default_data_dir()
    os.makedirs(CONFIG_DIR, exist_ok=True)
    return CONFIG_DIR


def config_path() -> str:
    return os.path.join(CONFIG_DIR, CONFIG_FILENAME)


def get_data_dir() -> str:
    """Ensure the data directory exists and return its path."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    return CONFIG_DIR


def load_config(path: str = "") -> dict:
    """Load config from file, falling back to defaults.

    ``path`` may point at an explicit config file; otherwise the file in
    the current data directory is used.  Unknown keys are preserved so
    newer configs survive a downgrade.
    """
    cfg = dict(DEFAULT_CONFIG)
    target = path or config_path()
    if os.path.exists(target):
        try:
            with open(target, "r", encoding="utf-8") as f:
                user = json.load(f)
            if isinstance(user, dict):
                cfg.update(user)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save_config(cfg: dict, path: str = "") -> None:
    """Save config atomically so a crash cannot truncate it."""
    target = path or config_path()
    directory = os.path.dirname(os.path.abspath(target)) or get_data_dir()
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".config-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
