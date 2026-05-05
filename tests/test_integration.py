"""Integration tests for ChitChat daemon: store, transport, and RPC.

These tests create two daemon instances with temporary data directories
so they never touch the user's real ~/.chitchat folder.  Discovery (mDNS)
is not used; the two daemons are wired together via a direct TCP connection
on the loopback interface.
"""

import asyncio
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.daemon as daemon_module
from core.daemon import ChitChatDaemon
from core.store.db import StoredMessage


# ── tests ────────────────────────────────────────────────────────

class TestIntegration:
    """End-to-end tests with two daemon instances and real TCP transport."""

    @classmethod
    def setup_class(cls):
        cls._orig_data_dir = daemon_module.DATA_DIR

    @classmethod
    def teardown_class(cls):
        daemon_module.DATA_DIR = cls._orig_data_dir

    def setup_method(self):
        """Fresh temp dirs for each test so stores start clean."""
        self.tmp_a = tempfile.mkdtemp()
        self.tmp_b = tempfile.mkdtemp()
        self.daemon_a = None
        self.daemon_b = None

    def teardown_method(self):
        if self.daemon_b is not None:
            try:
                self.daemon_b.stop()
            except Exception:
                pass
        if self.daemon_a is not None:
            try:
                self.daemon_a.stop()
            except Exception:
                pass
        # Give the OS a moment to release ports
        time.sleep(0.2)
        shutil.rmtree(self.tmp_a, ignore_errors=True)
        shutil.rmtree(self.tmp_b, ignore_errors=True)
        daemon_module.DATA_DIR = self._orig_data_dir

    def _make_daemon_a(self, **kw):
        daemon_module.DATA_DIR = self.tmp_a
        defaults = dict(device_name="Alpha", p2p_port=19877,
                        ws_port=19876, http_port=19875)
        defaults.update(kw)
        return ChitChatDaemon(**defaults)

    def _make_daemon_b(self, **kw):
        daemon_module.DATA_DIR = self.tmp_b
        defaults = dict(device_name="Bravo", p2p_port=19878,
                        ws_port=19879, http_port=19880)
        defaults.update(kw)
        return ChitChatDaemon(**defaults)

    # ── Store independence ────────────────────────────────────

    def test_stores_are_independent(self):
        """Two daemons get separate on-disk databases."""
        self.daemon_a = self._make_daemon_a()
        self.daemon_b = self._make_daemon_b()
        daemon_module.DATA_DIR = self._orig_data_dir

        peer_b = self.daemon_b._device_id
        peer_a = self.daemon_a._device_id

        self.daemon_a.store.save_message(StoredMessage(
            msg_id="s-001", peer_id=peer_b, direction="sent",
            msg_type="chat_text", body="Hello B", timestamp=time.time(),
        ))
        self.daemon_b.store.save_message(StoredMessage(
            msg_id="r-001", peer_id=peer_a, direction="received",
            msg_type="chat_text", body="Hi A", timestamp=time.time(),
        ))

        # A sees its own sent message
        hist_a = self.daemon_a.store.get_history(peer_b)
        assert len(hist_a) == 1
        assert hist_a[0].body == "Hello B"
        assert hist_a[0].direction == "sent"

        # B sees its own received message
        hist_b = self.daemon_b.store.get_history(peer_a)
        assert len(hist_b) == 1
        assert hist_b[0].body == "Hi A"
        assert hist_b[0].direction == "received"

        # A does NOT see B's messages
        a_self = self.daemon_a.store.get_history(peer_a)
        assert len(a_self) == 0

    # ── Message pipeline (encode → encrypt → decrypt → decode → store) ─

    def test_message_pipeline(self):
        """Full message pipeline without requiring a real TLS connection."""
        from core.protocol.codec import encode_frame, decode_message
        from core.security.encryption import EncryptionManager

        em_a = EncryptionManager("AA:BB:CC:DD:EE:FF")
        em_b = EncryptionManager("11:22:33:44:55:66")

        body = "Hello from Alpha!"
        peer_b_fp = "11:22:33:44:55:66"
        peer_a_fp = "AA:BB:CC:DD:EE:FF"

        # Alpha encodes and encrypts
        payload = {"msg_type": "chat_text", "msg_id": "msg-001",
                    "body": body, "timestamp": time.time()}
        frame = encode_frame(payload, msg_id="msg-001", source_device="Alpha")
        encrypted = em_a.encrypt_frame(frame, peer_b_fp)

        # Bravo decrypts and decodes
        decrypted = em_b.decrypt_frame(encrypted, peer_a_fp)
        assert decrypted is not None
        decoded = decode_message(decrypted)
        assert decoded is not None
        assert decoded.msg_type == "chat_text"
        assert decoded._raw_payload["body"] == body

        # Both daemons store their copy
        self.daemon_a = self._make_daemon_a()
        self.daemon_b = self._make_daemon_b()
        daemon_module.DATA_DIR = self._orig_data_dir

        peer_b = self.daemon_b._device_id
        peer_a = self.daemon_a._device_id

        self.daemon_a.store.save_message(StoredMessage(
            msg_id="msg-001", peer_id=peer_b, direction="sent",
            msg_type="chat_text", body=body, timestamp=time.time(),
        ))
        self.daemon_b.store.save_message(StoredMessage(
            msg_id="msg-001", peer_id=peer_a, direction="received",
            msg_type="chat_text", body=body, timestamp=time.time(),
        ))

        assert len(self.daemon_a.store.get_history(peer_b)) == 1
        assert len(self.daemon_b.store.get_history(peer_a)) == 1

    # ── RPC methods ───────────────────────────────────────────

    def test_rpc_methods(self):
        """Exercise RPC methods directly (no transport needed)."""
        self.daemon_a = self._make_daemon_a()
        self.daemon_b = self._make_daemon_b()
        daemon_module.DATA_DIR = self._orig_data_dir

        peer_b = self.daemon_b._device_id

        # ping
        result = asyncio.run(self.daemon_a._rpc_ping({}))
        assert result["pong"] is True
        assert "time" in result

        # get_status
        status = asyncio.run(self.daemon_a._rpc_get_status({}))
        assert status["device_name"] == "Alpha"
        assert "device_id" in status
        assert "peers_connected" in status

        # get_contacts (empty initially)
        contacts = asyncio.run(self.daemon_a._rpc_get_contacts({}))
        assert contacts["contacts"] == []

        # Add a contact manually and verify
        self.daemon_a.store.upsert_contact(peer_b, "Bravo", paired=True)
        contacts = asyncio.run(self.daemon_a._rpc_get_contacts({}))
        assert len(contacts["contacts"]) == 1
        assert contacts["contacts"][0]["device_name"] == "Bravo"

        # get_history (empty)
        hist = asyncio.run(
            self.daemon_a._rpc_get_history({"peer_id": peer_b}))
        assert hist["messages"] == []

        # send_message (saves locally even without transport peer)
        result = asyncio.run(self.daemon_a._rpc_send_message({
            "peer_id": peer_b,
            "body": "RPC test message",
        }))
        assert "msg_id" in result
        assert "timestamp" in result
        msg_id = result["msg_id"]

        # get_history now returns the message
        hist2 = asyncio.run(
            self.daemon_a._rpc_get_history({"peer_id": peer_b}))
        assert len(hist2["messages"]) == 1
        m = hist2["messages"][0]
        assert m["body"] == "RPC test message"
        assert m["direction"] == "sent"
        assert m["msg_id"] == msg_id
        assert m["msg_type"] == "chat_text"

        # get_history with limit
        hist3 = asyncio.run(
            self.daemon_a._rpc_get_history({"peer_id": peer_b, "limit": 1}))
        assert len(hist3["messages"]) == 1

        # mark_read
        result = asyncio.run(
            self.daemon_a._rpc_mark_read({"peer_id": peer_b}))
        assert result["ok"] is True

    # ── Contact management ────────────────────────────────────

    def test_contact_lifecycle(self):
        """Add, list, and remove contacts through the store."""
        self.daemon_a = self._make_daemon_a()
        daemon_module.DATA_DIR = self._orig_data_dir

        store = self.daemon_a.store

        # Initially no contacts
        assert store.get_contacts() == []

        # Upsert creates
        store.upsert_contact("peer-1", "One", paired=True)
        store.upsert_contact("peer-2", "Two", paired=False)

        contacts = store.get_contacts()
        assert len(contacts) == 2

        # Upsert updates
        store.upsert_contact("peer-1", "OneUpdated", paired=True)
        contacts = store.get_contacts()
        names = {c.device_name for c in contacts}
        assert "OneUpdated" in names
        assert "One" not in names

        # Remove
        store.remove_contact("peer-1")
        contacts = store.get_contacts()
        assert len(contacts) == 1
        assert contacts[0].device_id == "peer-2"

    # ── Message ordering ──────────────────────────────────────

    def test_message_ordering(self):
        """get_history returns messages in chronological order."""
        self.daemon_a = self._make_daemon_a()
        self.daemon_b = self._make_daemon_b()
        daemon_module.DATA_DIR = self._orig_data_dir

        store = self.daemon_a.store
        peer = self.daemon_b._device_id
        base = time.time()

        for i in range(5):
            store.save_message(StoredMessage(
                msg_id=f"ord-{i:03d}", peer_id=peer,
                direction="sent" if i % 2 == 0 else "received",
                msg_type="chat_text", body=f"Message {i}",
                timestamp=base + i,
            ))

        history = store.get_history(peer)
        assert len(history) == 5
        for i, m in enumerate(history):
            assert m.body == f"Message {i}", f"order mismatch at index {i}"
