"""Tests for the SQLite message and contact store."""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.store.db import MessageStore, StoredMessage, Contact
from tests._tmp import make_tmp_dir, cleanup_tmp_dir


class TestMessageStore:
    @classmethod
    def setup_class(cls):
        cls._tmpdir = make_tmp_dir()
        cls.db_path = os.path.join(cls._tmpdir, "test.db")
        cls.store = MessageStore(cls.db_path)

    @classmethod
    def teardown_class(cls):
        cleanup_tmp_dir(cls._tmpdir)

    def setup_method(self):
        # Clean tables before each test
        conn = self.store._get_conn()
        try:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM contacts")
            conn.commit()
        finally:
            conn.close()

    def test_save_and_retrieve_message(self):
        msg = StoredMessage(
            msg_id="msg-001", peer_id="peer-abc", direction="sent",
            msg_type="chat_text", body="Hello!", timestamp=time.time(),
        )
        self.store.save_message(msg)
        result = self.store.get_message("msg-001")
        assert result is not None
        assert result.msg_id == "msg-001"
        assert result.body == "Hello!"
        assert result.direction == "sent"
        assert result.peer_id == "peer-abc"

    def test_get_history_returns_messages_in_order(self):
        base = time.time()
        for i in range(5):
            self.store.save_message(StoredMessage(
                msg_id=f"msg-{i:03d}", peer_id="peer-x", direction="sent",
                msg_type="chat_text", body=f"Message {i}", timestamp=base + i,
            ))
        history = self.store.get_history("peer-x", limit=50)
        assert len(history) == 5
        for i, m in enumerate(history):
            assert m.body == f"Message {i}"

    def test_get_history_with_pagination(self):
        base = time.time()
        for i in range(10):
            self.store.save_message(StoredMessage(
                msg_id=f"pag-{i:03d}", peer_id="peer-p", direction="received",
                msg_type="chat_text", body=f"Msg {i}", timestamp=base + i,
            ))
        # Get first 5
        page1 = self.store.get_history("peer-p", limit=5)
        assert len(page1) == 5
        assert page1[0].body == "Msg 5"
        assert page1[4].body == "Msg 9"

        # Get next 5 (before the earliest in page1)
        page2 = self.store.get_history("peer-p", before_msg_id=page1[0].msg_id, limit=5)
        assert len(page2) == 5
        assert page2[0].body == "Msg 0"
        assert page2[4].body == "Msg 4"

    def test_mark_delivered(self):
        msg = StoredMessage(msg_id="md-001", peer_id="peer-d", direction="sent",
                            msg_type="chat_text", body="test", timestamp=time.time())
        self.store.save_message(msg)
        self.store.mark_delivered("md-001")
        result = self.store.get_message("md-001")
        assert result.delivered is True

    def test_mark_read(self):
        msg = StoredMessage(msg_id="mr-001", peer_id="peer-r", direction="sent",
                            msg_type="chat_text", body="test", timestamp=time.time())
        self.store.save_message(msg)
        self.store.mark_read("mr-001")
        result = self.store.get_message("mr-001")
        assert result.read is True

    def test_mark_all_read(self):
        for i in range(3):
            self.store.save_message(StoredMessage(
                msg_id=f"mar-{i:03d}", peer_id="peer-mar", direction="received",
                msg_type="chat_text", body=f"Unread {i}", timestamp=time.time() + i,
            ))
        self.store.mark_all_read("peer-mar")
        for i in range(3):
            m = self.store.get_message(f"mar-{i:03d}")
            assert m.read is True

    def test_upsert_contact(self):
        self.store.upsert_contact("c-001", "Alice", paired=True)
        contacts = self.store.get_contacts()
        assert len(contacts) == 1
        assert contacts[0].device_id == "c-001"
        assert contacts[0].device_name == "Alice"
        assert contacts[0].paired is True

    def test_upsert_contact_updates_existing(self):
        self.store.upsert_contact("c-002", "Bob", paired=True)
        self.store.upsert_contact("c-002", "Bobby", paired=False)
        contacts = self.store.get_contacts()
        assert contacts[0].device_name == "Bobby"
        assert contacts[0].paired is False

    def test_remove_contact(self):
        self.store.upsert_contact("c-003", "Charlie")
        self.store.remove_contact("c-003")
        contacts = self.store.get_contacts()
        assert len(contacts) == 0

    def test_save_message_updates_contact_last_message(self):
        self.store.upsert_contact("peer-lm", "LastMsg")
        msg = StoredMessage(msg_id="lm-001", peer_id="peer-lm", direction="received",
                            msg_type="chat_text", body="Hey there!", timestamp=time.time())
        self.store.save_message(msg)
        contacts = self.store.get_contacts()
        assert contacts[0].last_message == "Hey there!"

    def test_unread_count(self):
        self.store.upsert_contact("peer-ur", "Unread")
        for i in range(3):
            self.store.save_message(StoredMessage(
                msg_id=f"ur-{i:03d}", peer_id="peer-ur", direction="received",
                msg_type="chat_text", body=f"msg {i}", timestamp=time.time() + i,
            ))
        contacts = self.store.get_contacts()
        assert contacts[0].unread_count == 3
        self.store.mark_all_read("peer-ur")
        contacts = self.store.get_contacts()
        assert contacts[0].unread_count == 0

    def test_contact_order_by_last_time(self):
        base = time.time()
        self.store.upsert_contact("c-a", "A")
        self.store.upsert_contact("c-b", "B")
        self.store.save_message(StoredMessage(
            msg_id="ord-a", peer_id="c-a", direction="sent",
            msg_type="chat_text", body="a", timestamp=base,
        ))
        self.store.save_message(StoredMessage(
            msg_id="ord-b", peer_id="c-b", direction="sent",
            msg_type="chat_text", body="b", timestamp=base + 10,
        ))
        contacts = self.store.get_contacts()
        assert contacts[0].device_id == "c-b"  # most recent first
        assert contacts[1].device_id == "c-a"
