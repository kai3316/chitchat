"""Relay server client for cross-LAN communication."""

import asyncio
import json
import logging
import threading
import time

import websockets

logger = logging.getLogger(__name__)

RECONNECT_DELAY = 5
MAX_RECONNECT_DELAY = 60


class RelayClient:
    """WebSocket client that connects to the ChitChat relay server.

    When LAN peers are unreachable, the daemon can fall back to the relay
    server to route messages. The relay only sees encrypted blobs — it
    cannot read message content.
    """

    def __init__(self, relay_url: str = "", device_id: str = "",
                 device_name: str = "", on_message=None):
        self._url = relay_url
        self._device_id = device_id
        self._device_name = device_name
        self._on_message = on_message
        self._ws = None
        self._connected = False
        self._running = False
        self._thread = None
        self._loop = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        """Start the relay client in a background thread."""
        if not self._url:
            logger.info("Relay URL not configured — skipping")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the relay client."""
        self._running = False
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_loop())

    async def _connect_loop(self) -> None:
        delay = RECONNECT_DELAY
        while self._running:
            try:
                ws_url = f"{self._url}/ws?device_id={self._device_id}&name={self._device_name}"
                async with websockets.connect(ws_url, ping_interval=30) as ws:
                    self._ws = ws
                    self._connected = True
                    delay = RECONNECT_DELAY
                    logger.info("Relay connected: %s", self._url)
                    await self._read_loop(ws)
            except Exception:
                logger.debug("Relay connection failed — retry in %ds", delay)
            finally:
                self._ws = None
                self._connected = False
            await asyncio.sleep(delay)
            delay = min(delay * 2, MAX_RECONNECT_DELAY)

    async def _read_loop(self, ws) -> None:
        async for raw in ws:
            try:
                msg = json.loads(raw)
                if self._on_message:
                    self._on_message(msg)
            except Exception:
                logger.exception("Relay message parse error")

    async def _disconnect(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None
        self._connected = False

    def send(self, peer_id: str, data: bytes) -> bool:
        """Queue a message for relay delivery. Returns True if queued."""
        if not self._connected or not self._loop:
            return False
        try:
            payload = json.dumps({
                "to": peer_id,
                "from": self._device_id,
                "payload": data.hex(),
            })
            asyncio.run_coroutine_threadsafe(
                self._ws.send(payload), self._loop)
            return True
        except Exception:
            return False
