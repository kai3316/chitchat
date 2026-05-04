"""SQLite store for chat messages, contacts, and device identity."""

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
    peer_id: str        # conversation partner device_id
    direction: str      # "sent" or "received"
    msg_type: str       # "chat_text", "chat_image", "chat_file", etc.
    body: str           # text content, file path, or JSON metadata
    timestamp: float
    delivered: bool = False
    read: bool = False

    def to_dict(self):
        return {
            "msg_id": self.msg_id, "peer_id": self.peer_id,
            "direction": self.direction, "msg_type": self.msg_type,
            "body": self.body, "timestamp": self.timestamp,
            "delivered": self.delivered, "read": self.read,
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

    def to_dict(self):
        return {
            "device_id": self.device_id, "device_name": self.device_name,
            "paired": self.paired, "last_message": self.last_message,
            "last_time": self.last_time, "unread_count": self.unread_count,
            "online": self.online,
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
                        read INTEGER NOT NULL DEFAULT 0
                    );
                    CREATE INDEX IF NOT EXISTS idx_messages_peer ON messages(peer_id, timestamp);
                    CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

                    CREATE TABLE IF NOT EXISTS contacts (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        paired INTEGER NOT NULL DEFAULT 1,
                        last_message TEXT NOT NULL DEFAULT '',
                        last_time REAL NOT NULL DEFAULT 0.0,
                        unread_count INTEGER NOT NULL DEFAULT 0
                    );
                ''')
                conn.commit()
            finally:
                conn.close()

    # ── Messages ──────────────────────────────────────────────

    def save_message(self, msg: StoredMessage) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO messages (msg_id, peer_id, direction, msg_type, body, timestamp, delivered, read) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (msg.msg_id, msg.peer_id, msg.direction, msg.msg_type, msg.body, msg.timestamp, int(msg.delivered), int(msg.read)),
                )
                # Update contact last message
                conn.execute(
                    "INSERT INTO contacts (device_id, device_name, last_message, last_time) "
                    "VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(device_id) DO UPDATE SET last_message=excluded.last_message, last_time=excluded.last_time",
                    (msg.peer_id, msg.peer_id, msg.body[:200] if msg.body else "", msg.timestamp),
                )
                if msg.direction == "received" and not msg.read:
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
                    "SELECT device_id, device_name, paired, last_message, last_time, unread_count FROM contacts ORDER BY last_time DESC"
                ).fetchall()
                return [
                    Contact(
                        device_id=r["device_id"], device_name=r["device_name"],
                        paired=bool(r["paired"]), last_message=r["last_message"],
                        last_time=r["last_time"], unread_count=r["unread_count"],
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


def _row_to_msg(row: sqlite3.Row) -> StoredMessage:
    return StoredMessage(
        msg_id=row["msg_id"], peer_id=row["peer_id"],
        direction=row["direction"], msg_type=row["msg_type"],
        body=row["body"], timestamp=row["timestamp"],
        delivered=bool(row["delivered"]), read=bool(row["read"]),
    )
