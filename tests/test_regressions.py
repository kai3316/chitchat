"""Regression tests for the defects that made ChitChat unusable.

Each test here corresponds to a concrete failure observed in the field:

* inbound messages were filed under the sender's *display name* instead
  of its authenticated device id, so no conversation ever showed a reply;
* ``send_to_peer`` reported success as ``None`` and could not resolve the
  hashed mDNS id that discovery hands out;
* discovery persisted a second, phantom contact per peer;
* TLS key material was written into another application's data folder;
* the web UI hardcoded WebSocket port 9876.
"""

import os
import struct
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.config as config_mod
from core.daemon import ChitChatDaemon
from core.protocol.codec import ChatMessage, encode_frame
from core.store.db import MessageStore
from core.transport.connection import PeerConnection, TransportManager
from tests._tmp import make_tmp_dir, cleanup_tmp_dir


class _FakeSocket:
    """Minimal socket stand-in that replays pre-built frames then EOFs."""

    def __init__(self, chunks):
        self._chunks = list(chunks)
        self._buf = b""

    def settimeout(self, _timeout):
        pass

    def recv(self, n):
        while len(self._buf) < n and self._chunks:
            self._buf += self._chunks.pop(0)
        if not self._buf:
            return b""
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def getsockopt(self, *_args):
        return 0

    def shutdown(self, _how):
        pass

    def close(self):
        pass


def _wire(payload: dict, msg_id: str, source_device: str) -> bytes:
    frame = encode_frame(payload, msg_id=msg_id, source_device=source_device)
    return struct.pack(">I", len(frame)) + frame


class TestInboundIdentity:
    """Received messages must be keyed by the authenticated device id."""

    def setup_method(self):
        self.tmp = make_tmp_dir()
        self._orig = config_mod.CONFIG_DIR
        config_mod.configure(self.tmp)
        self.daemon = ChitChatDaemon(device_name="Local")

    def teardown_method(self):
        config_mod.configure(self._orig)
        cleanup_tmp_dir(self.tmp)

    def test_received_message_is_keyed_by_device_id_not_name(self):
        now = time.time()
        msg = ChatMessage(msg_type="chat_text", msg_id="m-1",
                          source_device="peer-device-id", timestamp=now)
        msg.source_name = "Peer Display Name"
        msg._raw_payload = {
            "msg_type": "chat_text", "msg_id": "m-1",
            "body": "hello there", "timestamp": now,
        }

        self.daemon._on_peer_message(msg)

        history = self.daemon.store.get_history("peer-device-id")
        assert len(history) == 1, history
        assert history[0].body == "hello there"
        assert history[0].peer_id == "peer-device-id"

        # The display name must never become a conversation key.
        assert self.daemon.store.get_history("Peer Display Name") == []

        contacts = self.daemon.store.get_contacts()
        assert [c.device_id for c in contacts] == ["peer-device-id"]
        assert contacts[0].device_name == "Peer Display Name"

    def test_peer_connection_overrides_claimed_sender(self):
        payload = {"msg_type": "chat_text", "msg_id": "m-2",
                   "body": "spoofed?", "timestamp": 1.0}
        wire = _wire(payload, msg_id="m-2", source_device="Display Name")
        conn = PeerConnection("authenticated-id", "Real Name",
                              _FakeSocket([wire]))
        seen = []
        conn.set_on_message(seen.append)
        conn._running = True          # normally set by start()
        conn._recv_loop()

        assert len(seen) == 1
        assert seen[0].source_device == "authenticated-id"
        assert seen[0].source_name == "Real Name"

    def test_unnamed_message_is_rejected_not_misfiled(self):
        msg = ChatMessage(msg_type="chat_text", msg_id="m-3",
                          source_device="", timestamp=1.0)
        msg._raw_payload = {"msg_type": "chat_text", "msg_id": "m-3",
                            "body": "orphan", "timestamp": 1.0}
        self.daemon._on_peer_message(msg)
        assert self.daemon.store.get_contacts() == []


class TestTransportReporting:
    def setup_method(self):
        self.tmp = make_tmp_dir()
        self._orig = config_mod.CONFIG_DIR
        config_mod.configure(self.tmp)
        self.transport = TransportManager(
            device_id="self-id", device_name="Self", port=0,
            pairing_mgr=type("P", (), {"is_peer_paired": lambda *a: False})(),
        )

    def teardown_method(self):
        config_mod.configure(self._orig)
        cleanup_tmp_dir(self.tmp)

    def test_send_to_unknown_peer_reports_false(self):
        assert self.transport.send_to_peer("nobody", b"payload") is False

    def test_hashed_id_resolves_to_real_id(self):
        with self.transport._lock:
            self.transport._hash_to_real_id["abc123hash00"] = "real-device-id"
        assert self.transport.resolve_peer_id("abc123hash00") == "real-device-id"
        assert self.transport.resolve_peer_id("real-device-id") == "real-device-id"
        # is_connected must accept either form
        assert self.transport.is_connected("abc123hash00") is False


class TestContactDeduplication:
    def setup_method(self):
        self.tmp = make_tmp_dir()
        self._orig = config_mod.CONFIG_DIR
        config_mod.configure(self.tmp)
        self.store = MessageStore(os.path.join(self.tmp, "chat.db"))

    def teardown_method(self):
        config_mod.configure(self._orig)
        cleanup_tmp_dir(self.tmp)

    def test_discovery_alias_is_merged_into_real_contact(self):
        self.store.upsert_contact("mDNS-hash", "Peer", paired=False)
        self.store.upsert_contact("RealName", "Peer", paired=True)

        adopted = self.store.adopt_contact_aliases(
            "real-device-id", ["mDNS-hash", "RealName"])

        assert set(adopted) == {"mDNS-hash", "RealName"}
        contacts = self.store.get_contacts()
        assert [c.device_id for c in contacts] == ["real-device-id"]

    def test_messages_under_alias_move_to_real_id(self):
        from core.store.db import StoredMessage
        self.store.save_message(StoredMessage(
            msg_id="old-1", peer_id="mDNS-hash", direction="received",
            msg_type="chat_text", body="old message", timestamp=1.0))
        self.store.adopt_contact_aliases("real-device-id", ["mDNS-hash"])

        history = self.store.get_history("real-device-id")
        assert [m.body for m in history] == ["old message"]
        assert self.store.get_history("mDNS-hash") == []

    def test_discovery_found_creates_no_contact(self):
        daemon = ChitChatDaemon(device_name="Local")
        daemon._on_peer_found("some-hash", "Peer", "127.0.0.1", 1)
        assert daemon.store.get_contacts() == []


class TestDataDirectory:
    def test_configure_redirects_every_stored_file(self):
        tmp = make_tmp_dir()
        orig = config_mod.CONFIG_DIR
        try:
            config_mod.configure(tmp)
            daemon = ChitChatDaemon(device_name="Local")
            assert os.path.dirname(daemon.store._db_path) == os.path.abspath(tmp)
            assert os.path.exists(os.path.join(tmp, "private_key.pem"))
            assert os.path.exists(os.path.join(tmp, "device_id"))
        finally:
            config_mod.configure(orig)
            cleanup_tmp_dir(tmp)

    def test_tls_scratch_dir_is_inside_chitchat_not_clipsync(self):
        tmp = make_tmp_dir()
        orig = config_mod.CONFIG_DIR
        try:
            config_mod.configure(tmp)
            scratch = TransportManager._secure_scratch_dir()
            assert os.path.abspath(tmp) in str(scratch)
            assert "clipsync" not in str(scratch).lower()
        finally:
            config_mod.configure(orig)
            cleanup_tmp_dir(tmp)


class TestWebUiBootstrap:
    def test_page_carries_the_real_websocket_port(self):
        tmp = make_tmp_dir()
        orig = config_mod.CONFIG_DIR
        try:
            config_mod.configure(tmp)
            daemon = ChitChatDaemon(device_name="Local", ws_port=19999,
                                    http_port=19998)
            html = daemon._render_web_ui()
            assert '"wsPort": 19999' in html
            assert "window.CHITCHAT_CONFIG" in html
            # The UI must read the injected value rather than a constant.
            assert "CHITCHAT_CONFIG.wsPort" in html
        finally:
            config_mod.configure(orig)
            cleanup_tmp_dir(tmp)


class TestDiscoveryAddress:
    """mDNS must never advertise loopback, or nobody can reach this device.

    macOS was the worst case: ``socket.gethostname()`` often resolves to
    nothing there, so the address list came back empty and the daemon
    advertised 127.0.0.1.
    """

    def test_advertised_addresses_are_routable(self):
        from core.transport.discovery import (
            _get_all_local_addresses, _primary_outbound_ip)

        primary = _primary_outbound_ip()
        assert primary == "" or not primary.startswith("127.")
        for address in _get_all_local_addresses():
            assert not address.startswith("127."), address
            assert not address.startswith("169.254."), address

    def test_selected_address_matches_the_default_route(self):
        from core.transport.discovery import _get_local_address, _primary_outbound_ip
        primary = _primary_outbound_ip()
        selected = _get_local_address()
        if primary:
            assert selected == primary, (selected, primary)


class TestWebUiContract:
    """The embedded UI and the daemon must agree on names.

    A mismatch here is invisible until a user notices that reactions or
    group messages never appear, so it is asserted mechanically.
    """

    # Events the daemon may emit that the UI intentionally ignores today.
    IGNORED_EVENTS = {"presence"}

    def _daemon_source(self) -> str:
        import inspect
        from core import daemon as daemon_module
        return inspect.getsource(daemon_module)

    def test_every_rpc_the_ui_calls_is_dispatchable(self):
        import re
        from core.web_ui import WEB_UI_HTML
        called = set(re.findall(r"sendRPC\(\s*'([a-z_]+)'", WEB_UI_HTML))
        exported = set(re.findall(r'"([a-z_]+)":\s*self\._rpc_', self._daemon_source()))
        missing = called - exported
        assert not missing, f"UI calls unimplemented RPCs: {sorted(missing)}"

    def test_every_broadcast_event_is_handled_by_the_ui(self):
        import re
        from core.web_ui import WEB_UI_HTML
        broadcast = set(re.findall(
            r'_broadcast_sync\(\s*"([a-z_]+)"', self._daemon_source()))
        handled = set(re.findall(r"case '([a-z_]+)':", WEB_UI_HTML))
        unhandled = broadcast - handled - self.IGNORED_EVENTS
        assert not unhandled, f"UI ignores daemon events: {sorted(unhandled)}"

    def test_security_alert_reaches_the_user(self):
        from core.web_ui import WEB_UI_HTML
        assert "handleSecurityAlert" in WEB_UI_HTML
        assert "case 'security_alert':" in WEB_UI_HTML
