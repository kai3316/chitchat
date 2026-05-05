"""SQLite store for chat messages, contacts, groups, and device identity."""

import json
import os
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StoredMessage:
    msg_id: str
    peer_id: str        # conversation partner device_id (or group_id for groups)
    direction: str      # "sent" or "received"
    msg_type: str       # "chat_text", "chat_image", "chat_file", etc.
    body: str           # text content, file path, or JSON metadata
    timestamp: float
    delivered: bool = False
    read: bool = False
    reply_to: str = ""  # msg_id being replied to
    is_group: bool = False

    def to_dict(self):
        return {
            "msg_id": self.msg_id, "peer_id": self.peer_id,
            "direction": self.direction, "msg_type": self.msg_type,
            "body": self.body, "timestamp": self.timestamp,
            "delivered": self.delivered, "read": self.read,
            "reply_to": self.reply_to, "is_group": self.is_group,
        }


@dataclass
class Contact:
    device_id: str
    device_name: str
    paired: bool = True
    last_message: str = ""
    last_time: float = 0.0
    unread_count: int = 0
    online: bool = False
    is_group: bool = False
    member_count: int = 0

    def to_dict(self):
        return {
            "device_id": self.device_id, "device_name": self.device_name,
            "paired": self.paired, "last_message": self.last_message,
            "last_time": self.last_time, "unread_count": self.unread_count,
            "online": self.online, "is_group": self.is_group,
            "member_count": self.member_count,
        }


@dataclass
class GroupInfo:
    group_id: str
    name: str
    members: list[str]   # list of device_ids
    created_by: str
    created_at: float
    last_message: str = ""
    last_time: float = 0.0
    unread_count: int = 0

    def to_dict(self):
        return {
            "group_id": self.group_id, "name": self.name,
            "members": self.members, "created_by": self.created_by,
            "created_at": self.created_at, "last_message": self.last_message,
            "last_time": self.last_time, "unread_count": self.unread_count,
        }


class MessageStore:
    """Thread-safe SQLite store for chat messages and contacts."""

    def __init__(self, db_path: str = ""):
        if not db_path:
            db_path = os.path.join(os.path.expanduser("~"), ".chitchat", "chitchat.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            try:
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS messages (
                        msg_id TEXT PRIMARY KEY,
                        peer_id TEXT NOT NULL,
                        direction TEXT NOT NULL CHECK(direction IN ('sent','received')),
                        msg_type TEXT NOT NULL DEFAULT 'chat_text',
                        body TEXT NOT NULL DEFAULT '',
                        timestamp REAL NOT NULL,
                        delivered INTEGER NOT NULL DEFAULT 0,
                        read INTEGER NOT NULL DEFAULT 0,
                        reply_to TEXT NOT NULL DEFAULT '',
                        is_group INTEGER NOT NULL DEFAULT 0
                    );
                    CREATE INDEX IF NOT EXISTS idx_messages_peer ON messages(peer_id, timestamp);
                    CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

                    CREATE TABLE IF NOT EXISTS contacts (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        paired INTEGER NOT NULL DEFAULT 1,
                        last_message TEXT NOT NULL DEFAULT '',
                        last_time REAL NOT NULL DEFAULT 0.0,
                        unread_count INTEGER NOT NULL DEFAULT 0,
                        is_group INTEGER NOT NULL DEFAULT 0,
                        member_count INTEGER NOT NULL DEFAULT 0
                    );

                    CREATE TABLE IF NOT EXISTS groups (
                        group_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        members TEXT NOT NULL DEFAULT '[]',
                        created_by TEXT NOT NULL DEFAULT '',
                        created_at REAL NOT NULL,
                        last_message TEXT NOT NULL DEFAULT '',
                        last_time REAL NOT NULL DEFAULT 0.0,
                        unread_count INTEGER NOT NULL DEFAULT 0
                    );

                    CREATE TABLE IF NOT EXISTS group_members (
                        group_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        device_name TEXT NOT NULL DEFAULT '',
                        joined_at REAL NOT NULL,
                        PRIMARY KEY (group_id, device_id),
                        FOREIGN KEY (group_id) REFERENCES groups(group_id)
                    );

                    CREATE TABLE IF NOT EXISTS reactions (
                        msg_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        emoji TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        PRIMARY KEY (msg_id, device_id),
                        FOREIGN KEY (msg_id) REFERENCES messages(msg_id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_reactions_msg ON reactions(msg_id);
                ''')
                # Add columns that may be missing from older DB versions
                for col, dtype in [
                    ("reply_to", "TEXT NOT NULL DEFAULT ''"),
                    ("is_group", "INTEGER NOT NULL DEFAULT 0"),
                ]:
                    try:
                        conn.execute(f"ALTER TABLE messages ADD COLUMN {col} {dtype}")
                    except sqlite3.OperationalError:
                        pass  # column already exists
                for col, dtype in [
                    ("is_group", "INTEGER NOT NULL DEFAULT 0"),
                    ("member_count", "INTEGER NOT NULL DEFAULT 0"),
                ]:
                    try:
                        conn.execute(f"ALTER TABLE contacts ADD COLUMN {col} {dtype}")
                    except sqlite3.OperationalError:
                        pass
                conn.commit()
            finally:
                conn.close()

    # ── Messages ──────────────────────────────────────────────

    def save_message(self, msg: StoredMessage) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO messages (msg_id, peer_id, direction, msg_type, body, timestamp, delivered, read, reply_to, is_group) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (msg.msg_id, msg.peer_id, msg.direction, msg.msg_type, msg.body,
                     msg.timestamp, int(msg.delivered), int(msg.read), msg.reply_to, int(msg.is_group)),
                )
                preview = _msg_preview(msg)
                if msg.is_group:
                    conn.execute(
                        "UPDATE groups SET last_message=?, last_time=? WHERE group_id=?",
                        (preview, msg.timestamp, msg.peer_id),
                    )
                else:
                    conn.execute(
                        "INSERT INTO contacts (device_id, device_name, last_message, last_time) "
                        "VALUES (?, ?, ?, ?) "
                        "ON CONFLICT(device_id) DO UPDATE SET last_message=excluded.last_message, last_time=excluded.last_time",
                        (msg.peer_id, msg.peer_id, preview, msg.timestamp),
                    )
                if msg.direction == "received" and not msg.read:
                    if msg.is_group:
                        conn.execute(
                            "UPDATE groups SET unread_count = unread_count + 1 WHERE group_id = ?",
                            (msg.peer_id,),
                        )
                    else:
                        conn.execute(
                            "UPDATE contacts SET unread_count = unread_count + 1 WHERE device_id = ?",
                            (msg.peer_id,),
                        )
                conn.commit()
            finally:
                conn.close()

    def get_history(self, peer_id: str, before_msg_id: str = "", limit: int = 50) -> list[StoredMessage]:
        with self._lock:
            conn = self._get_conn()
            try:
                if before_msg_id:
                    row = conn.execute("SELECT timestamp FROM messages WHERE msg_id = ?", (before_msg_id,)).fetchone()
                    if row:
                        before_ts = row[0]
                        rows = conn.execute(
                            "SELECT * FROM messages WHERE peer_id = ? AND timestamp < ? ORDER BY timestamp DESC LIMIT ?",
                            (peer_id, before_ts, limit),
                        ).fetchall()
                    else:
                        rows = []
                else:
                    rows = conn.execute(
                        "SELECT * FROM messages WHERE peer_id = ? ORDER BY timestamp DESC LIMIT ?",
                        (peer_id, limit),
                    ).fetchall()
                return [_row_to_msg(r) for r in reversed(rows)]
            finally:
                conn.close()

    def get_message(self, msg_id: str) -> Optional[StoredMessage]:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT * FROM messages WHERE msg_id = ?", (msg_id,)).fetchone()
                return _row_to_msg(row) if row else None
            finally:
                conn.close()

    def mark_delivered(self, msg_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("UPDATE messages SET delivered = 1 WHERE msg_id = ?", (msg_id,))
                conn.commit()
            finally:
                conn.close()

    def mark_read(self, msg_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("UPDATE messages SET read = 1 WHERE msg_id = ?", (msg_id,))
                conn.commit()
            finally:
                conn.close()

    def mark_all_read(self, peer_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("UPDATE messages SET read = 1 WHERE peer_id = ? AND direction = 'received'", (peer_id,))
                conn.execute("UPDATE contacts SET unread_count = 0 WHERE device_id = ?", (peer_id,))
                conn.commit()
            finally:
                conn.close()

    # ── Contacts ──────────────────────────────────────────────

    def upsert_contact(self, device_id: str, device_name: str, paired: bool = True) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO contacts (device_id, device_name, paired) VALUES (?, ?, ?) "
                    "ON CONFLICT(device_id) DO UPDATE SET device_name=excluded.device_name, paired=excluded.paired",
                    (device_id, device_name, int(paired)),
                )
                conn.commit()
            finally:
                conn.close()

    def get_contacts(self) -> list[Contact]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT * FROM contacts ORDER BY last_time DESC"
                ).fetchall()
                return [
                    Contact(
                        device_id=r["device_id"], device_name=r["device_name"],
                        paired=bool(r["paired"]), last_message=r["last_message"],
                        last_time=r["last_time"], unread_count=r["unread_count"],
                        is_group=bool(_col(r, "is_group", 0)),
                        member_count=_col(r, "member_count", 0),
                    )
                    for r in rows
                ]
            finally:
                conn.close()

    def remove_contact(self, device_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM contacts WHERE device_id = ?", (device_id,))
                conn.execute("DELETE FROM messages WHERE peer_id = ?", (device_id,))
                conn.commit()
            finally:
                conn.close()

    # ── Groups ─────────────────────────────────────────────────

    def create_group(self, group_id: str, name: str, members: list[str],
                     created_by: str) -> GroupInfo:
        with self._lock:
            conn = self._get_conn()
            try:
                now = time.time()
                conn.execute(
                    "INSERT INTO groups (group_id, name, members, created_by, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (group_id, name, json.dumps(members), created_by, now),
                )
                for mid in members:
                    conn.execute(
                        "INSERT OR REPLACE INTO group_members (group_id, device_id, device_name, joined_at) "
                        "VALUES (?, ?, ?, ?)",
                        (group_id, mid, mid, now),
                    )
                # Add as a contact entry for the UI
                conn.execute(
                    "INSERT OR REPLACE INTO contacts (device_id, device_name, is_group, member_count) "
                    "VALUES (?, ?, 1, ?)",
                    (group_id, name, len(members)),
                )
                conn.commit()
                return GroupInfo(
                    group_id=group_id, name=name, members=members,
                    created_by=created_by, created_at=now,
                )
            finally:
                conn.close()

    def get_groups(self) -> list[GroupInfo]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT * FROM groups ORDER BY last_time DESC"
                ).fetchall()
                return [
                    GroupInfo(
                        group_id=r["group_id"], name=r["name"],
                        members=json.loads(r["members"]),
                        created_by=r["created_by"], created_at=r["created_at"],
                        last_message=r["last_message"], last_time=r["last_time"],
                        unread_count=r["unread_count"],
                    )
                    for r in rows
                ]
            finally:
                conn.close()

    def get_group(self, group_id: str) -> Optional[GroupInfo]:
        with self._lock:
            conn = self._get_conn()
            try:
                r = conn.execute(
                    "SELECT * FROM groups WHERE group_id = ?", (group_id,)
                ).fetchone()
                if not r:
                    return None
                return GroupInfo(
                    group_id=r["group_id"], name=r["name"],
                    members=json.loads(r["members"]),
                    created_by=r["created_by"], created_at=r["created_at"],
                    last_message=r["last_message"], last_time=r["last_time"],
                    unread_count=r["unread_count"],
                )
            finally:
                conn.close()

    def add_group_member(self, group_id: str, device_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO group_members (group_id, device_id, device_name, joined_at) "
                    "VALUES (?, ?, ?, ?)",
                    (group_id, device_id, device_id, time.time()),
                )
                r = conn.execute(
                    "SELECT members FROM groups WHERE group_id = ?", (group_id,)
                ).fetchone()
                if r:
                    members = json.loads(r["members"])
                    if device_id not in members:
                        members.append(device_id)
                        conn.execute(
                            "UPDATE groups SET members = ? WHERE group_id = ?",
                            (json.dumps(members), group_id),
                        )
                        conn.execute(
                            "UPDATE contacts SET member_count = ? WHERE device_id = ?",
                            (len(members), group_id),
                        )
                conn.commit()
            finally:
                conn.close()

    def remove_group_member(self, group_id: str, device_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "DELETE FROM group_members WHERE group_id = ? AND device_id = ?",
                    (group_id, device_id),
                )
                r = conn.execute(
                    "SELECT members FROM groups WHERE group_id = ?", (group_id,)
                ).fetchone()
                if r:
                    members = json.loads(r["members"])
                    if device_id in members:
                        members.remove(device_id)
                        conn.execute(
                            "UPDATE groups SET members = ? WHERE group_id = ?",
                            (json.dumps(members), group_id),
                        )
                        conn.execute(
                            "UPDATE contacts SET member_count = ? WHERE device_id = ?",
                            (len(members), group_id),
                        )
                conn.commit()
            finally:
                conn.close()

    def get_group_members(self, group_id: str) -> list[str]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT device_id FROM group_members WHERE group_id = ?",
                    (group_id,),
                ).fetchall()
                return [r["device_id"] for r in rows]
            finally:
                conn.close()

    def get_thread_messages(self, parent_msg_id: str, limit: int = 50) -> list[StoredMessage]:
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT * FROM messages WHERE reply_to = ? ORDER BY timestamp DESC LIMIT ?",
                    (parent_msg_id, limit),
                ).fetchall()
                return [_row_to_msg(r) for r in reversed(rows)]
            finally:
                conn.close()

    # ── Reactions ──────────────────────────────────────────────

    def add_reaction(self, msg_id: str, device_id: str, emoji: str) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO reactions (msg_id, device_id, emoji, timestamp) "
                    "VALUES (?, ?, ?, ?)",
                    (msg_id, device_id, emoji, time.time()),
                )
                conn.commit()
            finally:
                conn.close()

    def remove_reaction(self, msg_id: str, device_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "DELETE FROM reactions WHERE msg_id = ? AND device_id = ?",
                    (msg_id, device_id),
                )
                conn.commit()
            finally:
                conn.close()

    def get_reactions(self, msg_id: str) -> dict[str, list[str]]:
        """Returns {emoji: [device_ids]} for a message."""
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT emoji, device_id FROM reactions WHERE msg_id = ?",
                    (msg_id,),
                ).fetchall()
                result = {}
                for r in rows:
                    result.setdefault(r["emoji"], []).append(r["device_id"])
                return result
            finally:
                conn.close()


def _col(row, name: str, default=0):
    """Safely read a column from a sqlite3.Row, returning default if missing."""
    if name in row.keys():
        return row[name]
    return default


def _msg_preview(msg: StoredMessage) -> str:
    """Return a human-readable preview string for a message."""
    if not msg.body:
        return ""
    if msg.msg_type == "chat_text":
        return msg.body[:200]
    if msg.msg_type == "chat_image":
        try:
            meta = json.loads(msg.body)
            name = meta.get("file_name", "")
            return f"Image: {name}" if name else "Image"
        except (json.JSONDecodeError, TypeError):
            return "Image"
    if msg.msg_type == "chat_file":
        try:
            meta = json.loads(msg.body)
            name = meta.get("file_name", "file")
            return f"File: {name}"
        except (json.JSONDecodeError, TypeError):
            return "File"
    if msg.msg_type == "chat_voice":
        try:
            meta = json.loads(msg.body)
            dur = meta.get("duration", 0)
            return f"Voice ({dur}s)"
        except (json.JSONDecodeError, TypeError):
            return "Voice"
    if msg.msg_type == "chat_link":
        try:
            meta = json.loads(msg.body)
            title = meta.get("title", "") or meta.get("url", "")
            return f"Link: {title}"[:200]
        except (json.JSONDecodeError, TypeError):
            return "Link"
    return msg.body[:200]


def _row_to_msg(row: sqlite3.Row) -> StoredMessage:
    return StoredMessage(
        msg_id=row["msg_id"], peer_id=row["peer_id"],
        direction=row["direction"], msg_type=row["msg_type"],
        body=row["body"], timestamp=row["timestamp"],
        delivered=bool(row["delivered"]), read=bool(row["read"]),
        reply_to=row["reply_to"] if "reply_to" in row.keys() else "",
        is_group=bool(row["is_group"]) if "is_group" in row.keys() else False,
    )
