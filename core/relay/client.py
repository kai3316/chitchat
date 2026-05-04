"""Relay server client — placeholder for Phase 4."""
import logging

logger = logging.getLogger(__name__)


class RelayClient:
    """Connects to the relay server when LAN peers are unreachable."""

    def __init__(self, relay_url: str = ""):
        self._url = relay_url
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        logger.info("Relay client: not implemented yet (Phase 4)")
        return False

    def disconnect(self) -> None:
        self._connected = False

    def send(self, peer_id: str, data: bytes) -> bool:
        return False
