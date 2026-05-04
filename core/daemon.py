"""ChitChat daemon — JSON-RPC WebSocket server for Flutter UI communication.

Architecture:
  Flutter UI ←→ localhost:9876 (WebSocket / JSON-RPC) ←→ daemon ←→ P2P network

The daemon runs as a background process. Flutter connects to it via WebSocket
on localhost. All UI actions are JSON-RPC requests; network events are pushed
as JSON-RPC notifications.
"""

import asyncio
import json
import logging
import os
import secrets
import sys
import threading
import time
import uuid

import websockets
from websockets.server import serve as ws_serve

from core.protocol.codec import encode_frame, decode_message, CHAT_MSG_TYPES
from core.transport.connection import TransportManager, PortInUseError
from core.transport.discovery import Discovery
from core.security.pairing import PairingManager
from core.security.encryption import EncryptionManager
from core.store.db import MessageStore, StoredMessage
from core.relay.client import RelayClient

logger = logging.getLogger(__name__)

DEFAULT_PORT = 9876  # WebSocket port for Flutter UI
DEFAULT_P2P_PORT = 9877  # TCP port for P2P communication
DATA_DIR = os.path.join(os.path.expanduser("~"), ".chitchat")


class ChitChatDaemon:
    """Main daemon managing P2P networking, storage, and UI communication."""

    def __init__(self, device_name: str = "", port: int = DEFAULT_P2P_PORT):
        os.makedirs(DATA_DIR, exist_ok=True)

        self._device_name = device_name or f"ChitChat-{secrets.token_hex(2)}"
        self._port = port
        self._ws_port = DEFAULT_PORT
        self._running = False
        self._ws_clients: set = set()

        # ── Identity & Security ───────────────────────────────
        self.pairing_mgr = PairingManager(
            device_id=self._load_or_create_device_id(),
            device_name=self._device_name,
        )
        identity = self.pairing_mgr.load_or_create_identity(
            private_key_pem=self._load_key("private_key.pem"),
            certificate_pem=self._load_key("certificate.pem"),
        )
        # Persist identity
        self._save_key("private_key.pem", identity.private_key_pem)
        self._save_key("certificate.pem", identity.certificate_pem)

        logger.info("Device ID: %s  Fingerprint: %s", identity.device_id[:12], identity.fingerprint_short)

        # ── Encryption ─────────────────────────────────────────
        self.enc_mgr = EncryptionManager(identity.fingerprint)

        # ── Storage ────────────────────────────────────────────
        self.store = MessageStore(os.path.join(DATA_DIR, "chitchat.db"))

        # ── Transport ──────────────────────────────────────────
        self.transport_mgr = TransportManager(
            device_id=identity.device_id,
            device_name=self._device_name,
            port=port,
            pairing_mgr=self.pairing_mgr,
        )
        self.transport_mgr.set_encryption_manager(self.enc_mgr)
        self.transport_mgr.set_on_peer_message(self._on_peer_message)
        self.transport_mgr.set_on_wake(self._on_wake)
        self.transport_mgr.set_on_security_alert(self._on_security_alert)

        # ── Discovery ──────────────────────────────────────────
        self.discovery = Discovery(
            device_id=identity.device_id,
            device_name=self._device_name,
            port=port,
            service_type="_chitchat._tcp",
        )
        self.discovery.set_callbacks(
            on_found=self._on_peer_found,
            on_lost=self._on_peer_lost,
        )

        # ── Relay (Phase 4 stub) ───────────────────────────────
        self.relay = RelayClient()

        # ── Pending requests (for JSON-RPC request/response) ──
        self._pending: dict[str, asyncio.Future] = {}

    # ═══════════════════════════════════════════════════════════
    # Identity helpers
    # ═══════════════════════════════════════════════════════════

    def _load_or_create_device_id(self) -> str:
        path = os.path.join(DATA_DIR, "device_id")
        if os.path.exists(path):
            with open(path) as f:
                return f.read().strip()
        did = uuid.uuid4().hex
        with open(path, "w") as f:
            f.write(did)
        return did

    def _load_key(self, filename: str) -> str:
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
        return ""

    def _save_key(self, filename: str, data: str) -> None:
        path = os.path.join(DATA_DIR, filename)
        with open(path, "w") as f:
            f.write(data)
        os.chmod(path, 0o600)

    # ═══════════════════════════════════════════════════════════
    # Lifecycle
    # ═══════════════════════════════════════════════════════════

    def start(self) -> None:
        """Start all services."""
        try:
            self.transport_mgr.start_server()
        except PortInUseError as e:
            logger.error("P2P port %d is in use: %s", self._port, e)
            raise
        self.discovery.start()
        self._running = True
        logger.info("ChitChat daemon started — P2P on :%d, WS on :%d", self._port, self._ws_port)

    def stop(self) -> None:
        """Stop all services."""
        self._running = False
        self.discovery.stop()
        self.transport_mgr.stop_server()
        self.relay.disconnect()
        logger.info("ChitChat daemon stopped")

    # ═══════════════════════════════════════════════════════════
    # WebSocket server for Flutter UI
    # ═══════════════════════════════════════════════════════════

    async def run_ws_server(self) -> None:
        """Start the WebSocket server for Flutter UI connections."""
        logger.info("Starting WebSocket server on ws://127.0.0.1:%d", self._ws_port)
        async with ws_serve(self._handle_ws_client, "127.0.0.1", self._ws_port):
            await asyncio.Future()  # run forever

    async def _handle_ws_client(self, ws):
        """Handle a Flutter UI WebSocket connection."""
        self._ws_clients.add(ws)
        peer = ws.remote_address
        logger.info("UI client connected: %s", peer)
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                    response = await self._dispatch(msg)
                    if response is not None:
                        await ws.send(json.dumps(response))
                except json.JSONDecodeError:
                    await ws.send(json.dumps({"error": "invalid json"}))
                except Exception as e:
                    logger.exception("Error handling WS message")
                    await ws.send(json.dumps({"error": str(e)}))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._ws_clients.discard(ws)
            logger.info("UI client disconnected: %s", peer)

    async def _dispatch(self, msg: dict) -> dict | None:
        """Dispatch a JSON-RPC message. Returns response or None for notifications."""
        method = msg.get("method", "")
        params = msg.get("params", {})
        req_id = msg.get("id")

        handler = {
            "send_message": self._rpc_send_message,
            "get_history": self._rpc_get_history,
            "get_contacts": self._rpc_get_contacts,
            "pair_device": self._rpc_pair_device,
            "send_typing": self._rpc_send_typing,
            "react": self._rpc_react,
            "mark_read": self._rpc_mark_read,
            "get_status": self._rpc_get_status,
            "ping": self._rpc_ping,
        }.get(method)

        if handler is None:
            return {"id": req_id, "error": f"unknown method: {method}"}

        result = await handler(params)
        if req_id is not None:
            return {"id": req_id, "result": result}
        return None

    # ═══════════════════════════════════════════════════════════
    # JSON-RPC handlers
    # ═══════════════════════════════════════════════════════════

    async def _rpc_send_message(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        msg_type = params.get("type", "chat_text")
        body = params.get("body", "")

        msg_id = uuid.uuid4().hex
        ts = time.time()

        # Store locally
        stored = StoredMessage(
            msg_id=msg_id, peer_id=peer_id, direction="sent",
            msg_type=msg_type, body=body, timestamp=ts,
            delivered=False, read=False,
        )
        self.store.save_message(stored)

        # Encode and send via P2P
        payload = {
            "msg_type": msg_type,
            "msg_id": msg_id,
            "body": body,
            "timestamp": ts,
            "reply_to": params.get("reply_to", ""),
        }
        data = encode_frame(payload, msg_id=msg_id, source_device=self._device_name)

        sent = self.transport_mgr.send_to_peer(peer_id, data)
        if sent:
            self.store.mark_delivered(msg_id)

        # Try relay if direct send failed
        if not sent and self.relay.is_connected:
            sent = self.relay.send(peer_id, data)

        return {"msg_id": msg_id, "timestamp": ts, "sent": sent}

    async def _rpc_get_history(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        before = params.get("before", "")
        limit = params.get("limit", 50)
        messages = self.store.get_history(peer_id, before, limit)
        return {"messages": [m.to_dict() for m in messages]}

    async def _rpc_get_contacts(self, params: dict) -> dict:
        contacts = self.store.get_contacts()
        # Add online status from connected peers
        online_ids = set(self.transport_mgr.get_connected_peers())
        contact_list = []
        for c in contacts:
            d = c.to_dict()
            d["online"] = c.device_id in online_ids
            contact_list.append(d)

        # Also include connected-but-not-in-contacts peers
        known_ids = {c.device_id for c in contacts}
        for pid, name in self.transport_mgr.get_connected_peers_with_names():
            if pid not in known_ids:
                contact_list.append({
                    "device_id": pid, "device_name": name,
                    "paired": True, "last_message": "",
                    "last_time": 0.0, "unread_count": 0, "online": True,
                })

        return {"contacts": contact_list}

    async def _rpc_pair_device(self, params: dict) -> dict:
        code = params.get("code", "")
        peer_id = params.get("peer_id", "")
        if not code or not peer_id:
            return {"ok": False, "error": "code and peer_id required"}

        ok = self.pairing_mgr.confirm_pairing(peer_id, code)
        if ok:
            # Trigger reconnection to the newly paired peer
            self.discovery._wake_recovery()
        return {"ok": ok}

    async def _rpc_send_typing(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        payload = {"msg_type": "typing", "timestamp": time.time()}
        data = encode_frame(payload, source_device=self._device_name)
        self.transport_mgr.send_to_peer(peer_id, data)
        return {"ok": True}

    async def _rpc_react(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        msg_id = params["msg_id"]
        emoji = params.get("emoji", "👍")
        payload = {
            "msg_type": "reaction", "msg_id": msg_id,
            "emoji": emoji, "timestamp": time.time(),
        }
        data = encode_frame(payload, source_device=self._device_name)
        self.transport_mgr.send_to_peer(peer_id, data)
        return {"ok": True}

    async def _rpc_mark_read(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        self.store.mark_all_read(peer_id)
        # Send read receipt
        connected = self.transport_mgr.get_connected_peers()
        if peer_id in connected:
            payload = {"msg_type": "read_receipt", "timestamp": time.time()}
            data = encode_frame(payload, source_device=self._device_name)
            self.transport_mgr.send_to_peer(peer_id, data)
        return {"ok": True}

    async def _rpc_get_status(self, params: dict) -> dict:
        identity = self.pairing_mgr.get_identity()
        return {
            "device_id": identity.device_id,
            "device_name": self._device_name,
            "fingerprint_short": identity.fingerprint_short,
            "peers_connected": len(self.transport_mgr.get_connected_peers()),
            "peers_online": self.transport_mgr.get_connected_peers_with_names(),
            "p2p_port": self._port,
        }

    async def _rpc_ping(self, params: dict) -> dict:
        return {"pong": True, "time": time.time()}

    # ═══════════════════════════════════════════════════════════
    # Event broadcasting to Flutter clients
    # ═══════════════════════════════════════════════════════════

    async def _broadcast_event(self, event: str, data: dict) -> None:
        """Send an event to all connected Flutter clients."""
        payload = json.dumps({"event": event, "data": data})
        dead = set()
        for ws in self._ws_clients:
            try:
                await ws.send(payload)
            except websockets.exceptions.ConnectionClosed:
                dead.add(ws)
            except Exception:
                dead.add(ws)
        self._ws_clients -= dead

    def _broadcast_event_sync(self, event: str, data: dict) -> None:
        """Thread-safe wrapper to broadcast from non-async contexts."""
        asyncio.run_coroutine_threadsafe(
            self._broadcast_event(event, data), self._loop
        )

    # ═══════════════════════════════════════════════════════════
    # P2P message handler
    # ═══════════════════════════════════════════════════════════

    def _on_peer_message(self, msg) -> None:
        """Handle incoming messages from P2P peers."""
        msg_type = getattr(msg, "msg_type", "") or "chat_text"
        raw = getattr(msg, "_raw_payload", {})
        peer_id = getattr(msg, "source_device", "")

        if msg_type == "chat_text":
            body = raw.get("body", "")
            msg_id = raw.get("msg_id", uuid.uuid4().hex)
            ts = raw.get("timestamp", time.time())
            stored = StoredMessage(
                msg_id=msg_id, peer_id=peer_id, direction="received",
                msg_type="chat_text", body=body, timestamp=ts,
            )
            self.store.save_message(stored)
            self._broadcast_event_sync("message_received", stored.to_dict())

            # Send ack
            identity = self.pairing_mgr.get_identity()
            ack = encode_frame({"msg_type": "ack", "ack_msg_id": msg_id},
                               source_device=identity.device_id)
            self.transport_mgr.send_to_peer(peer_id, ack)

        elif msg_type == "typing":
            self._broadcast_event_sync("typing", {"peer_id": peer_id})

        elif msg_type == "read_receipt":
            self._broadcast_event_sync("read_receipt", {"peer_id": peer_id})

        elif msg_type == "reaction":
            self._broadcast_event_sync("reaction", {
                "peer_id": peer_id,
                "msg_id": raw.get("msg_id", ""),
                "emoji": raw.get("emoji", "👍"),
            })

        elif msg_type == "ack":
            ack_msg_id = raw.get("ack_msg_id", "")
            if ack_msg_id:
                self.store.mark_delivered(ack_msg_id)
            self._broadcast_event_sync("message_delivered", {"msg_id": ack_msg_id})

        elif msg_type == "presence":
            status = raw.get("status", "online")
            self._broadcast_event_sync("presence", {"peer_id": peer_id, "status": status})

        elif msg_type == "chat_image" or msg_type == "chat_file":
            body = raw.get("body", "")
            file_name = raw.get("file_name", "")
            msg_id = raw.get("msg_id", uuid.uuid4().hex)
            ts = raw.get("timestamp", time.time())
            stored = StoredMessage(
                msg_id=msg_id, peer_id=peer_id, direction="received",
                msg_type=msg_type, body=json.dumps({"file_name": file_name, "data": body}),
                timestamp=ts,
            )
            self.store.save_message(stored)
            self._broadcast_event_sync("message_received", stored.to_dict())

    # ═══════════════════════════════════════════════════════════
    # Discovery callbacks
    # ═══════════════════════════════════════════════════════════

    def _on_peer_found(self, device_id: str, device_name: str, address: str, port: int) -> None:
        """Called by Discovery when a new peer is found via mDNS."""
        logger.info("Peer found: %s (%s) at %s:%d", device_name, device_id[:12], address, port)
        self.transport_mgr.connect_to_peer(device_id, device_name, address, port)
        self.store.upsert_contact(device_id, device_name, paired=False)

    def _on_peer_lost(self, device_id: str) -> None:
        """Called by Discovery when a peer disappears."""
        logger.info("Peer lost: %s", device_id[:12])
        self.transport_mgr.disconnect_peer(device_id)
        self._broadcast_event_sync("peer_offline", {"peer_id": device_id})

    def _on_wake(self) -> None:
        """Called by TransportManager after wake-from-sleep recovery."""
        self.discovery._wake_recovery()
        logger.info("Wake recovery complete")

    def _on_security_alert(self, peer_name: str, expected_fp: str, received_fp: str) -> None:
        """Called when a peer's certificate fingerprint has changed."""
        logger.warning("SECURITY ALERT: %s cert changed! Expected=%s Got=%s",
                       peer_name, expected_fp[:16], received_fp[:16])
        self._broadcast_event_sync("security_alert", {
            "peer_name": peer_name,
            "expected_fp": expected_fp[:16],
            "received_fp": received_fp[:16],
        })


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    daemon = ChitChatDaemon()
    try:
        daemon.start()
    except PortInUseError:
        logger.error("P2P port already in use. Is another instance running?")
        sys.exit(1)

    # Store event loop reference for thread-safe broadcasting
    daemon._loop = asyncio.get_running_loop()

    await daemon.run_ws_server()


if __name__ == "__main__":
    asyncio.run(main())
