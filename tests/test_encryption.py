"""Tests for the ChitChat encryption layer."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.security.encryption import (
    EncryptionManager, encrypt, decrypt, is_encrypted,
    derive_key, make_password_hash, verify_password,
    _ENCRYPTED_PREFIX,
)


class TestEncryptionManager:
    def test_init(self):
        em = EncryptionManager("AA:BB:CC:DD:EE:FF")
        assert em is not None
        assert len(em.storage_key) == 32

    def test_encrypt_decrypt_frame(self):
        em = EncryptionManager("AA:BB:CC:DD:EE:FF")
        plaintext = b"Hello, ChitChat!"
        peer_fp = "11:22:33:44:55:66"
        ciphertext = em.encrypt_frame(plaintext, peer_fp)
        assert ciphertext != plaintext
        assert is_encrypted(ciphertext)

        decrypted = em.decrypt_frame(ciphertext, peer_fp)
        assert decrypted == plaintext

    def test_decrypt_plaintext_returns_none(self):
        """Plaintext data without the encrypted prefix returns None."""
        em = EncryptionManager("AA:BB:CC:DD:EE:FF")
        result = em.decrypt_frame(b"not encrypted data", "peer-fp")
        assert result is None  # no prefix = not decryptable

    def test_different_peers_different_keys(self):
        em = EncryptionManager("AA:BB:CC:DD:EE:FF")
        pt = b"secret message"
        ct1 = em.encrypt_frame(pt, "fp-aaa")
        ct2 = em.encrypt_frame(pt, "fp-bbb")
        # Different peer fingerprints produce different ciphertexts
        assert ct1 != ct2

    def test_wrong_peer_cannot_decrypt(self):
        em = EncryptionManager("AA:BB:CC:DD:EE:FF")
        ct = em.encrypt_frame(b"classified", "fp-alice")
        result = em.decrypt_frame(ct, "fp-bob")
        assert result is None  # auth failure

    def test_storage_encrypt_decrypt(self):
        em = EncryptionManager("AA:BB:CC:DD:EE:FF")
        plain = "sensitive config data"
        enc = em.encrypt_storage(plain)
        assert enc != plain
        dec = em.decrypt_storage(enc)
        assert dec == plain

    def test_storage_decrypt_legacy_plaintext(self):
        """Legacy plaintext config values should pass through."""
        em = EncryptionManager("AA:BB:CC:DD:EE:FF")
        result = em.decrypt_storage("plaintext config")
        assert result == "plaintext config"

    def test_with_password(self):
        em = EncryptionManager("AA:BB:CC:DD:EE:FF", password="my-secret")
        ct = em.encrypt_frame(b"data", "fp-x")
        dec = em.decrypt_frame(ct, "fp-x")
        assert dec == b"data"

    def test_password_changes_key(self):
        em_no_pw = EncryptionManager("fp-base")
        em_pw = EncryptionManager("fp-base", password="pw")
        ct_no_pw = em_no_pw.encrypt_frame(b"test", "peer")
        ct_pw = em_pw.encrypt_frame(b"test", "peer")
        assert ct_no_pw != ct_pw  # different keys

    def test_tampered_data_fails(self):
        em = EncryptionManager("fp-test")
        ct = em.encrypt_frame(b"tamper-proof", "peer")
        # Flip a byte in the ciphertext
        tampered = bytearray(ct)
        tampered[-10] ^= 0x01
        result = em.decrypt_frame(bytes(tampered), "peer")
        assert result is None


class TestEncryptedPrefix:
    def test_prefix(self):
        assert _ENCRYPTED_PREFIX == b"\x01CCE"

    def test_is_encrypted_detection(self):
        assert is_encrypted(b"\x01CCE" + b"more data")
        assert not is_encrypted(b"plain data")
        assert not is_encrypted(b"\x01CBE" + b"old prefix")  # old ClipSync prefix


class TestPasswordFunctions:
    def test_derive_key(self):
        key = derive_key("password123", b"mysalt")
        assert len(key) == 32

    def test_derive_key_deterministic(self):
        k1 = derive_key("pw", b"salt")
        k2 = derive_key("pw", b"salt")
        assert k1 == k2

    def test_derive_key_different_salts(self):
        k1 = derive_key("pw", b"salt1")
        k2 = derive_key("pw", b"salt2")
        assert k1 != k2

    def test_password_hash_verify(self):
        h = make_password_hash("mypassword", "fp")
        assert isinstance(h, str)
        assert len(h) == 32  # hex chars
        assert verify_password("mypassword", "fp", h) is True
        assert verify_password("wrongpassword", "fp", h) is False


class TestRawEncryptDecrypt:
    def test_raw_encrypt_decrypt(self):
        key = b"\x00" * 32
        pt = b"hello world"
        ct = encrypt(pt, key)
        assert ct != pt
        dec = decrypt(ct, key)
        assert dec == pt

    def test_raw_decrypt_wrong_key(self):
        key1 = b"\x00" * 32
        key2 = b"\x01" * 32
        ct = encrypt(b"test", key1)
        assert decrypt(ct, key2) is None

    def test_raw_decrypt_no_prefix(self):
        assert decrypt(b"no prefix data", b"\x00" * 32) is None
