"""ChitChat daemon configuration."""

import json
import os
from pathlib import Path


DEFAULT_CONFIG = {
    "device_name": "",
    "p2p_port": 9877,
    "ws_port": 9876,
    "http_port": 9875,
    "http_bind": "0.0.0.0",
    "relay_url": "",
    "relay_enabled": False,
    "debug": False,
    "auto_accept_pairs": False,
}

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".chitchat")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def load_config() -> dict:
    """Load config from file, falling back to defaults."""
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                user = json.load(f)
            cfg.update(user)
        except (json.JSONDecodeError, IOError):
            pass
    return cfg


def save_config(cfg: dict) -> None:
    """Save config to file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def get_data_dir() -> str:
    """Ensure the data directory exists and return its path."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    return CONFIG_DIR
