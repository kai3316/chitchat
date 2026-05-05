"""ChitChat daemon — JSON-RPC WebSocket server + HTTP web UI.

Architecture:
  Web UI / Flutter ←→ localhost:9876 (WS) ←→ daemon ←→ P2P network
                 ←→ localhost:9875 (HTTP) ← built-in chat SPA

The built-in web UI makes ChitChat usable immediately — open a browser,
connect to the daemon, and start chatting. No Flutter SDK required.
"""

import argparse
import asyncio
import json
import logging
import os
import secrets
import signal
import sys
import threading
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import websockets
from websockets.asyncio.server import serve as ws_serve

from core.protocol.codec import encode_frame, decode_message, CHAT_MSG_TYPES
from core.transport.connection import TransportManager, PortInUseError
from core.transport.discovery import Discovery
from core.security.pairing import PairingManager
from core.security.encryption import EncryptionManager
from core.store.db import MessageStore, StoredMessage
from core.config import load_config, save_config, CONFIG_DIR as DATA_DIR

logger = logging.getLogger(__name__)

DEFAULT_HTTP_PORT = 9875   # HTTP server for web UI
DEFAULT_WS_PORT = 9876     # WebSocket for UI clients
DEFAULT_P2P_PORT = 9877    # TCP for P2P communication

# ── Web UI (embedded SPA) ─────────────────────────────────────
try:
    from core.web_ui import WEB_UI_HTML
except ImportError:
    WEB_UI_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>ChitChat</title>
<style>body{font-family:system-ui,sans-serif;background:#0f0f14;color:#f0f0f5;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
a{color:#7C67D6}</style></head><body><div style="text-align:center">
<h1>ChitChat</h1><p>Web UI not loaded.</p>
<p>Run <code>python -m core.web_ui</code> to generate it.</p></div></body></html>"""


class ChitChatDaemon:
    """Main daemon: P2P networking + storage + WS/HTTP servers."""

    def __init__(self, device_name: str = "", p2p_port: int = DEFAULT_P2P_PORT,
                 ws_port: int = DEFAULT_WS_PORT, http_port: int = DEFAULT_HTTP_PORT,
                 bind_http: str = "0.0.0.0", relay_url: str = ""):
        os.makedirs(DATA_DIR, exist_ok=True)

        self._device_name = device_name or f"ChitChat-{secrets.token_hex(2)}"
        self._p2p_port = p2p_port
        self._ws_port = ws_port
        self._http_port = http_port
        self._bind_http = bind_http
        self._relay_url = relay_url
        self._running = False
        self._ws_clients: set = set()
        self._loop = None

        # ── Identity & Security ───────────────────────────────
        self.pairing_mgr = PairingManager(
            device_id=self._load_or_create_device_id(),
            device_name=self._device_name,
        )
        identity = self.pairing_mgr.load_or_create_identity(
            private_key_pem=self._load_key("private_key.pem"),
            certificate_pem=self._load_key("certificate.pem"),
        )
        self._save_key("private_key.pem", identity.private_key_pem)
        self._save_key("certificate.pem", identity.certificate_pem)
        self._device_id = identity.device_id

        logger.info("Device: %s  Name: %s  FP: %s",
                     identity.device_id[:12], self._device_name, identity.fingerprint_short)

        # ── Encryption ─────────────────────────────────────────
        self.enc_mgr = EncryptionManager(identity.fingerprint)

        # ── Storage ────────────────────────────────────────────
        self.store = MessageStore(os.path.join(DATA_DIR, "chitchat.db"))

        # ── Transport ──────────────────────────────────────────
        self.transport_mgr = TransportManager(
            device_id=identity.device_id, device_name=self._device_name,
            port=p2p_port, pairing_mgr=self.pairing_mgr,
        )
        self.transport_mgr.set_encryption_manager(self.enc_mgr)
        self.transport_mgr.set_on_peer_message(self._on_peer_message)
        self.transport_mgr.set_on_wake(self._on_wake)
        self.transport_mgr.set_on_security_alert(self._on_security_alert)

        # ── Relay ──────────────────────────────────────────────
        from core.relay.client import RelayClient
        self.relay = RelayClient(
            relay_url=relay_url,
            device_id=identity.device_id,
            device_name=self._device_name,
            on_message=self._on_relay_message,
        )

        # ── Discovery ──────────────────────────────────────────
        self.discovery = Discovery(
            device_id=identity.device_id, device_name=self._device_name,
            port=p2p_port, service_type="_chitchat._tcp",
        )
        self.discovery.set_callbacks(
            on_found=self._on_peer_found, on_lost=self._on_peer_lost)

    # ═══════════════════════════════════════════════════════════
    # Identity helpers
    # ═══════════════════════════════════════════════════════════

    def _load_or_create_device_id(self) -> str:
        path = os.path.join(DATA_DIR, "device_id")
        if os.path.exists(path):
            return open(path).read().strip()
        did = uuid.uuid4().hex
        with open(path, "w") as f:
            f.write(did)
        return did

    def _load_key(self, filename: str) -> str:
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            return open(path).read()
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
        try:
            self.transport_mgr.start_server()
        except PortInUseError:
            logger.error("P2P port %d is in use. Is another instance running?", self._p2p_port)
            raise
        self.discovery.start()
        if self._relay_url:
            self.relay.start()
        self._running = True
        logger.info("Daemon started — P2P :%d  WS :%d  HTTP :%d",
                     self._p2p_port, self._ws_port, self._http_port)

    def stop(self) -> None:
        self._running = False
        self.discovery.stop()
        self.relay.stop()
        self.transport_mgr.stop_server()
        logger.info("Daemon stopped")

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def device_name(self) -> str:
        return self._device_name

    # ═══════════════════════════════════════════════════════════
    # HTTP server (serves embedded web UI)
    # ═══════════════════════════════════════════════════════════

    def _create_http_server(self) -> HTTPServer:
        daemon = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/" or self.path == "/index.html":
                    self._send_html(WEB_UI_HTML)
                elif self.path == "/health":
                    self._send_json({
                        "status": "ok",
                        "device": daemon._device_name,
                        "peers": len(daemon.transport_mgr.get_connected_peers()),
                        "time": time.time(),
                    })
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path == "/api/chat":
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length) if content_length else b"{}"
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        self._send_json({"ok": False, "error": "invalid json"}, 400)
                        return
                    peer_id = data.get("peer_id", "")
                    text = data.get("text", "")
                    if peer_id and text:
                        # Run sync send in thread
                        threading.Thread(
                            target=lambda: daemon._sync_send_message(peer_id, text),
                            daemon=True,
                        ).start()
                        self._send_json({"ok": True})
                    else:
                        self._send_json({"ok": False, "error": "peer_id and text required"}, 400)
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # suppress HTTP log noise

            def _send_html(self, html: str):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))

            def _send_json(self, data: dict, status: int = 200):
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode("utf-8"))

        return HTTPServer((self._bind_http, self._http_port), Handler)

    def _sync_send_message(self, peer_id: str, text: str) -> None:
        """Synchronous wrapper for sending messages (called from HTTP thread)."""
        msg_id = uuid.uuid4().hex
        ts = time.time()
        stored = StoredMessage(
            msg_id=msg_id, peer_id=peer_id, direction="sent",
            msg_type="chat_text", body=text, timestamp=ts,
        )
        self.store.save_message(stored)
        payload = {"msg_type": "chat_text", "msg_id": msg_id, "body": text, "timestamp": ts}
        data = encode_frame(payload, msg_id=msg_id, source_device=self._device_name)
        self.transport_mgr.send_to_peer(peer_id, data)

    # ═══════════════════════════════════════════════════════════
    # WebSocket server
    # ═══════════════════════════════════════════════════════════

    async def run_ws_server(self) -> None:
        logger.info("WebSocket server on ws://127.0.0.1:%d", self._ws_port)
        async with ws_serve(self._handle_ws, "127.0.0.1", self._ws_port):
            await asyncio.Future()

    async def _handle_ws(self, ws):
        self._ws_clients.add(ws)
        logger.info("WS client connected: %s", ws.remote_address)
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                    response = await self._dispatch(msg)
                    if response is not None:
                        await ws.send(json.dumps(response))
                except json.JSONDecodeError:
                    await ws.send(json.dumps({"error": "invalid json"}))
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception:
                    logger.exception("WS handler error")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._ws_clients.discard(ws)
            logger.info("WS client disconnected: %s", ws.remote_address)

    async def _dispatch(self, msg: dict) -> dict | None:
        method = msg.get("method", "")
        params = msg.get("params", {})
        req_id = msg.get("id")

        handler = {
            "send_message": self._rpc_send_message,
            "get_history": self._rpc_get_history,
            "get_contacts": self._rpc_get_contacts,
            "mark_read": self._rpc_mark_read,
            "send_typing": self._rpc_send_typing,
            "react": self._rpc_react,
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
    # RPC handlers
    # ═══════════════════════════════════════════════════════════

    async def _rpc_send_message(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        msg_type = params.get("type", "chat_text")
        body = params.get("body", "")
        msg_id = uuid.uuid4().hex
        ts = time.time()

        self.store.save_message(StoredMessage(
            msg_id=msg_id, peer_id=peer_id, direction="sent",
            msg_type=msg_type, body=body, timestamp=ts,
        ))
        payload = {"msg_type": msg_type, "msg_id": msg_id, "body": body,
                    "timestamp": ts, "reply_to": params.get("reply_to", "")}
        data = encode_frame(payload, msg_id=msg_id, source_device=self._device_name)
        sent = self.transport_mgr.send_to_peer(peer_id, data)
        if sent:
            self.store.mark_delivered(msg_id)
        return {"msg_id": msg_id, "timestamp": ts, "sent": sent}

    async def _rpc_get_history(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        before = params.get("before", "")
        limit = min(params.get("limit", 50), 200)
        msgs = self.store.get_history(peer_id, before, limit)
        return {"messages": [m.to_dict() for m in msgs]}

    async def _rpc_get_contacts(self, params: dict) -> dict:
        contacts = self.store.get_contacts()
        online_ids = set(self.transport_mgr.get_connected_peers())
        result = []
        for c in contacts:
            d = c.to_dict()
            d["online"] = c.device_id in online_ids
            result.append(d)
        known_ids = {c.device_id for c in contacts}
        for pid, name in self.transport_mgr.get_connected_peers_with_names():
            if pid not in known_ids:
                result.append({
                    "device_id": pid, "device_name": name or pid[:8],
                    "paired": True, "last_message": "", "last_time": 0.0,
                    "unread_count": 0, "online": True,
                })
        return {"contacts": result}

    async def _rpc_mark_read(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        self.store.mark_all_read(peer_id)
        if peer_id in self.transport_mgr.get_connected_peers():
            payload = {"msg_type": "read_receipt", "timestamp": time.time()}
            data = encode_frame(payload, source_device=self._device_name)
            self.transport_mgr.send_to_peer(peer_id, data)
        return {"ok": True}

    async def _rpc_send_typing(self, params: dict) -> dict:
        peer_id = params["peer_id"]
        payload = {"msg_type": "typing", "timestamp": time.time()}
        data = encode_frame(payload, source_device=self._device_name)
        self.transport_mgr.send_to_peer(peer_id, data)
        return {"ok": True}

    async def _rpc_react(self, params: dict) -> dict:
        payload = {"msg_type": "reaction", "msg_id": params["msg_id"],
                    "emoji": params.get("emoji", "👍"), "timestamp": time.time()}
        data = encode_frame(payload, source_device=self._device_name)
        self.transport_mgr.send_to_peer(params["peer_id"], data)
        return {"ok": True}

    async def _rpc_get_status(self, params: dict) -> dict:
        return {
            "device_id": self._device_id,
            "device_name": self._device_name,
            "peers_connected": len(self.transport_mgr.get_connected_peers()),
            "peers_online": self.transport_mgr.get_connected_peers_with_names(),
            "p2p_port": self._p2p_port,
        }

    async def _rpc_ping(self, params: dict) -> dict:
        return {"pong": True, "time": time.time()}

    # ═══════════════════════════════════════════════════════════
    # Event broadcasting
    # ═══════════════════════════════════════════════════════════

    async def _broadcast_event(self, event: str, data: dict) -> None:
        payload = json.dumps({"event": event, "data": data})
        dead = set()
        for ws in self._ws_clients:
            try:
                await ws.send(payload)
            except (websockets.exceptions.ConnectionClosed, Exception):
                dead.add(ws)
        self._ws_clients -= dead

    def _broadcast_sync(self, event: str, data: dict) -> None:
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._broadcast_event(event, data), self._loop)

    # ═══════════════════════════════════════════════════════════
    # P2P message handler
    # ═══════════════════════════════════════════════════════════

    def _on_peer_message(self, msg) -> None:
        msg_type = getattr(msg, "msg_type", "") or "chat_text"
        raw = getattr(msg, "_raw_payload", {})
        peer_id = getattr(msg, "source_device", "")

        if msg_type == "chat_text":
            mid = raw.get("msg_id", uuid.uuid4().hex)
            ts = raw.get("timestamp", time.time())
            stored = StoredMessage(
                msg_id=mid, peer_id=peer_id, direction="received",
                msg_type="chat_text", body=raw.get("body", ""), timestamp=ts,
            )
            self.store.save_message(stored)
            self._broadcast_sync("message_received", stored.to_dict())
            # Send ack
            ack = encode_frame({"msg_type": "ack", "ack_msg_id": mid},
                               source_device=self._device_id)
            self.transport_mgr.send_to_peer(peer_id, ack)

        elif msg_type == "typing":
            self._broadcast_sync("typing", {"peer_id": peer_id})

        elif msg_type == "read_receipt":
            self._broadcast_sync("read_receipt", {"peer_id": peer_id})

        elif msg_type == "reaction":
            self._broadcast_sync("reaction", {
                "peer_id": peer_id,
                "msg_id": raw.get("msg_id", ""),
                "emoji": raw.get("emoji", "👍"),
            })

        elif msg_type == "ack":
            ack_id = raw.get("ack_msg_id", "")
            if ack_id:
                self.store.mark_delivered(ack_id)
            self._broadcast_sync("message_delivered", {"msg_id": ack_id})

        elif msg_type == "presence":
            self._broadcast_sync("presence", {
                "peer_id": peer_id, "status": raw.get("status", "online")})

        elif msg_type in ("chat_image", "chat_file"):
            mid = raw.get("msg_id", uuid.uuid4().hex)
            ts = raw.get("timestamp", time.time())
            stored = StoredMessage(
                msg_id=mid, peer_id=peer_id, direction="received",
                msg_type=msg_type,
                body=json.dumps({"file_name": raw.get("file_name", ""), "data": raw.get("body", "")}),
                timestamp=ts,
            )
            self.store.save_message(stored)
            self._broadcast_sync("message_received", stored.to_dict())

    # ═══════════════════════════════════════════════════════════
    # Discovery callbacks
    # ═══════════════════════════════════════════════════════════

    def _on_peer_found(self, device_id: str, device_name: str, address: str, port: int) -> None:
        logger.info("Peer found: %s (%s) @ %s:%d", device_name, device_id[:12], address, port)
        self.transport_mgr.connect_to_peer(device_id, device_name, address, port)
        self.store.upsert_contact(device_id, device_name, paired=False)

    def _on_peer_lost(self, device_id: str) -> None:
        logger.info("Peer lost: %s", device_id[:12])
        self.transport_mgr.disconnect_peer(device_id)
        self._broadcast_sync("peer_offline", {"peer_id": device_id})

    def _on_wake(self) -> None:
        self.discovery._wake_recovery()
        logger.info("Wake recovery complete")

    def _on_security_alert(self, peer_name: str, expected: str, received: str) -> None:
        logger.warning("SECURITY: %s cert changed! %s → %s", peer_name, expected[:16], received[:16])
        self._broadcast_sync("security_alert", {
            "peer_name": peer_name, "expected": expected[:16], "received": received[:16]})

    def _on_relay_message(self, msg: dict) -> None:
        """Handle a message received through the relay server."""
        from_peer = msg.get("from", "")
        payload_hex = msg.get("payload", "")
        try:
            data = bytes.fromhex(payload_hex)
            frame = decode_message(data)
            if frame:
                setattr(frame, "source_device", from_peer)
                self._on_peer_message(frame)
        except Exception:
            logger.exception("Failed to decode relay message")


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="ChitChat daemon")
    parser.add_argument("--name", "-n", default="", help="Device display name")
    parser.add_argument("--p2p-port", type=int, default=0, help="P2P TCP port")
    parser.add_argument("--ws-port", type=int, default=0, help="WebSocket port")
    parser.add_argument("--http-port", type=int, default=0, help="HTTP server port")
    parser.add_argument("--bind", default="", help="HTTP bind address (0.0.0.0 for LAN access)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--relay", default="", help="Relay server URL (e.g. ws://relay.example.com:8080)")
    parser.add_argument("--config", default="", help="Path to config file")
    args = parser.parse_args()

    cfg = load_config()

    # CLI args override config
    device_name = args.name or cfg.get("device_name", "")
    p2p_port = args.p2p_port or cfg.get("p2p_port", DEFAULT_P2P_PORT)
    ws_port = args.ws_port or cfg.get("ws_port", DEFAULT_WS_PORT)
    http_port = args.http_port or cfg.get("http_port", DEFAULT_HTTP_PORT)
    bind_http = args.bind or cfg.get("http_bind", "0.0.0.0")
    debug = args.debug or cfg.get("debug", False)
    relay_url = args.relay or cfg.get("relay_url", "")

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Suppress noisy library logs
    for lib in ("zeroconf", "websockets", "asyncio"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    daemon = ChitChatDaemon(
        device_name=device_name,
        p2p_port=p2p_port,
        ws_port=ws_port,
        http_port=http_port,
        bind_http=bind_http,
        relay_url=relay_url,
    )
    try:
        daemon.start()
    except PortInUseError:
        logger.error("Port %d is in use. Is another instance running?", p2p_port)
        sys.exit(1)

    # Start HTTP server in a thread
    httpd = daemon._create_http_server()
    http_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    http_thread.start()

    local_ip = "127.0.0.1"
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    relay_status = f"Relay:   {relay_url}" if relay_url else "Relay:   (disabled - LAN only)"
    print(f"""
+--------------------------------------------------------------+
|                    ChitChat v1.0.0                           |
|                                                              |
|  Device:     {daemon.device_name:<50s}|
|  P2P:        tcp://0.0.0.0:{daemon._p2p_port:<40d}|
|  Web UI:     http://{local_ip}:{daemon._http_port:<45d}|
|  Web UI:     http://127.0.0.1:{daemon._http_port:<43d}|
|  WebSocket:  ws://127.0.0.1:{daemon._ws_port:<42d}|
|  {relay_status:<54s}|
|                                                              |
|  Open the Web UI in a browser to start chatting!             |
+--------------------------------------------------------------+
""")

    async def run_async():
        daemon._loop = asyncio.get_running_loop()
        await daemon.run_ws_server()

    try:
        asyncio.run(run_async())
    except KeyboardInterrupt:
        pass
    finally:
        daemon.stop()
        httpd.shutdown()
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
