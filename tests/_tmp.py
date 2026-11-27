"""Shared helpers for the ChitChat test suite.

Temporary directories normally live under the system temp folder, but in
restricted environments (sandboxes, locked-down corporate machines) that
folder can be unwritable.  ``make_tmp_dir`` verifies the location first
and falls back to a folder inside the project.
"""

import os
import shutil
import tempfile
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOCAL_TMP_ROOT = os.path.join(ROOT, ".pytest_tmp")


def _is_writable(path: str) -> bool:
    probe = os.path.join(path, f".probe-{uuid.uuid4().hex}")
    try:
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.unlink(probe)
        return True
    except OSError:
        return False


def make_tmp_dir(prefix: str = "chitchat-test-") -> str:
    """Create a writable temporary directory and return its path.

    ``tempfile.mkdtemp`` is deliberately avoided: it applies a private
    (0700) ACL on Windows, which restrictive sandboxes and some managed
    machines treat as "no access" for child processes.  ``os.makedirs``
    keeps the inherited permissions and works everywhere.
    """
    for base in (tempfile.gettempdir(), _LOCAL_TMP_ROOT):
        candidate = os.path.join(base, prefix + uuid.uuid4().hex)
        try:
            os.makedirs(candidate, exist_ok=True)
        except OSError:
            continue
        if _is_writable(candidate):
            return candidate
        shutil.rmtree(candidate, ignore_errors=True)
    raise RuntimeError("no writable temporary directory available")


def cleanup_tmp_dir(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)
