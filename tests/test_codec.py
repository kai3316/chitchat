"""Tests for the ChitChat binary frame codec."""

import json
import struct
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.protocol.codec import (
    encode_frame, decode_message, encode_binary_chunk,
    ChatMessage, CHAT_MSG_TYPES, FILE_TRANSFER_MSG_TYPES,
    MAGIC,
)


class TestEncodeFrame:
    def test_basic_frame_encoding(self):
        payload = {"msg_type": "chat_text", "body": "hello", "timestamp": 1234567890.0}
        data = encode_frame(payload, msg_id="test123", source_device="test-device")
        assert isinstance(data, bytes)
        assert len(data) > 10

    def test_frame_magic_bytes(self):
        payload = {"msg_type": "chat_text", "body": "hi"}
        data = encode_frame(payload, msg_id="abc", source_device="dev")
        magic = struct.unpack(">H", data[:2])[0]
        assert magic == MAGIC
        assert hex(magic) == "0x4343"  # "CC" for ChitChat

    def test_frame_roundtrip(self):
        payload = {
            "msg_type": "chat_text",
            "body": "Hello, World!",
            "timestamp": 1234567890.5,
            "msg_id": "abc123def456",
        }
        encoded = encode_frame(payload, msg_id="abc123def456", source_device="sender-device")
        decoded = decode_message(encoded)
        assert decoded is not None
        assert decoded.msg_type == "chat_text"
        assert decoded.msg_id == "abc123def456"
        assert decoded.source_device == "sender-device"
        raw = decoded._raw_payload
        assert raw["body"] == "Hello, World!"

    def test_roundtrip_with_unicode(self):
        payload = {
            "msg_type": "chat_text",
            "body": "你好世界 🌍",
            "timestamp": 1234567890.0,
        }
        encoded = encode_frame(payload, msg_id="test", source_device="dev")
        decoded = decode_message(encoded)
        assert decoded is not None
        assert decoded._raw_payload["body"] == "你好世界 🌍"

    def test_default_msg_type(self):
        """Messages without msg_type should default to chat_text."""
        payload = {"body": "test", "timestamp": 123.0}
        encoded = encode_frame(payload, source_device="dev")
        decoded = decode_message(encoded)
        assert decoded is not None
        assert decoded.msg_type == "chat_text"


class TestChatMessageTypes:
    def test_all_required_types_present(self):
        required = {"chat_text", "chat_image", "chat_file", "typing",
                     "read_receipt", "reaction", "presence", "ack", "ping", "pong"}
        assert required.issubset(CHAT_MSG_TYPES)

    def test_chat_message_dataclass(self):
        msg = ChatMessage(
            msg_type="chat_text",
            msg_id="123",
            source_device="dev1",
            timestamp=1234567890.0,
            _raw_payload={"body": "hi"},
        )
        assert msg.msg_type == "chat_text"
        assert msg.msg_id == "123"
        assert msg.source_device == "dev1"
        assert msg._raw_payload["body"] == "hi"


class TestBinaryChunkEncoding:
    def test_binary_chunk(self):
        raw_data = b"\x00\x01\x02\x03" * 100
        encoded = encode_binary_chunk("a" * 32, 5, 20, raw_data)
        assert isinstance(encoded, bytes)
        assert len(encoded) > len(raw_data)  # has header

    def test_binary_chunk_magic(self):
        encoded = encode_binary_chunk("b" * 32, 0, 10, b"hello")
        magic = struct.unpack(">H", encoded[:2])[0]
        assert hex(magic) == "0x4243"  # "BC" for Binary Chunk


class TestDecodeInvalidData:
    def test_too_short(self):
        assert decode_message(b"\x43\x43") is None

    def test_wrong_magic(self):
        payload = json.dumps({"body": "test"}).encode()
        bad_frame = struct.pack(">H", 0xFFFF) + b"\x02" + struct.pack(">I", len(payload)) + b"\x00\x00\x00\x00\x00" + payload
        assert decode_message(bad_frame) is None

    def test_empty_payload(self):
        data = struct.pack(">H", MAGIC) + b"\x02" + struct.pack(">I", 0) + struct.pack(">I", 0) + b"\x00"
        assert decode_message(data) is None
