# ChitChat

<p align="center">
  <strong>Chat that just works. LAN or cloud.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square" alt="License: Apache 2.0">
  <img src="https://img.shields.io/badge/platform-iOS%20%7C%20Android%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20Web-lightgrey?style=flat-square" alt="Platforms: iOS, Android, Windows, macOS, Linux, Web">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/flutter-3.0%2B-blue?style=flat-square&logo=flutter" alt="Flutter 3.0+">
  <img src="https://img.shields.io/badge/go-1.21%2B-00ADD8?style=flat-square&logo=go" alt="Go 1.21+">
</p>

---

**ChitChat** is a modern, multi-platform chat application that combines direct peer-to-peer
LAN communication with cloud relay fallback. When peers are nearby, messages flow directly
over your local network with zero server cost and minimal latency. When they leave the LAN,
a lightweight relay server bridges the gap seamlessly. All communication is end-to-end
encrypted with TLS 1.3 and AES-256-GCM.

## Why ChitChat?

| | ChitChat | Signal / WhatsApp | Telegram | Discord |
|---|---|---|---|---|
| **P2P LAN** | Yes, mDNS auto-discovery | No | No | No |
| **Relay fallback** | Self-hosted (~8 MB Go binary) | Vendor-hosted | Vendor-hosted | Vendor-hosted |
| **E2E encryption** | TLS 1.3 + AES-256-GCM | Signal Protocol | MTProto | No E2E (servers) |
| **Identity** | Ed25519 certs + TOFU pairing | Phone number | Phone number | Email |
| **No phone number** | Yes | No | No | Yes |
| **Self-hostable** | Fully | No | No | No |
| **Cross-platform** | 6 platforms | 4 | Many | 5 |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FLUTTER UI LAYER                              │
│              Material Design 3  ·  Dark Mode  ·  6 Platforms            │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │  WebSocket (localhost:9876)
                               │  JSON-RPC (request / response + push events)
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          PYTHON DAEMON (core/)                          │
│                                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│   │ Discovery│  │ Transport│  │ Security │  │  Relay   │  │  Store  │ │
│   │  (mDNS)  │  │  (TCP)   │  │  (TLS)   │  │ (WS Tx)  │  │ (SQLite)│ │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│        │             │             │             │             │        │
│   mDNS │             │       TCP + TLS 1.3       │      WebSocket        │
│   SRV  │             │    AES-256-GCM (E2E)      │                       │
│        ▼             ▼                           ▼                       │
└───────────────┬──────────────────┬──────────────────────────────────────┘
                │                  │
       P2P LAN │                  │ Internet / WAN
     (direct)  │                  │ (relay fallback)
               ▼                  ▼
      ┌──────────────┐   ┌──────────────────┐
      │   Peer B     │   │  GO RELAY SERVER │
      │  (same LAN)  │   │  (server/main.go) │
      │              │   │  ~8 MB binary     │
      └──────────────┘   │  WebSocket hub    │
                         └──────────┬─────────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │  Peer C  │
                              │ (remote) │
                              └──────────┘
```

## Features

### P2P LAN Chat
Zero server cost, minimal latency. Messages flow directly between devices on the same
network. Uses mDNS (Bonjour/Avahi) for automatic peer discovery -- no typing IP addresses.

### E2E Encryption
Every message is encrypted with **TLS 1.3** over the wire and **AES-256-GCM** for data at rest.
Ed25519 certificate-based identities with **TOFU (Trust On First Use)** pairing ensure you
connect to the right device every time.

### Relay Fallback
When a peer leaves the LAN, relay fallback activates automatically and transparently.
The relay is a standalone **~8 MB Go binary** you host yourself -- no third-party servers.

### Cross-Platform
One Flutter codebase, six targets: **iOS, Android, Windows, macOS, Linux, Web**.
Native performance everywhere with Material Design 3 polish.

### Rich Messages
Text, images, files, and voice messages. Typing indicators, read receipts, and
emoji reactions make conversations feel alive.

### Self-Hosted Relay
The relay server is a single static binary with no runtime dependencies.
Deploy it on a $5 VPS, behind a reverse proxy, or on a Raspberry Pi.

### Modern UI
Material Design 3 with full dark mode support, smooth animations, and an
indigo/violet accent palette. Designed to feel native on every platform.

### Persistent Storage
All messages are stored in a local SQLite database with indexing for fast
history search. Contacts, pairing trust, and preferences persist across restarts.

## Project Structure

```
chitchat/
  core/               Python daemon — P2P networking, encryption, storage
    daemon.py             Entry point: JSON-RPC WebSocket server for Flutter
    protocol/             Binary message framing (codec.py)
    transport/            TCP transport layer + mDNS discovery
    security/             Ed25519 identity, TLS, AES-256-GCM, TOFU pairing
    store/                SQLite message store with history and contacts
    relay/                WebSocket relay client for fallback transport
  app/                Flutter UI — Material Design 3
    lib/
      main.dart           App entry point, theme, routing
      models/             Data models (Message, Contact)
      screens/            Chat list, chat thread, settings screens
      services/           Daemon WebSocket service bridge
  server/             Go relay server
    main.go               WebSocket hub — device registration, message routing
    go.mod                Single dependency: gorilla/websocket
  tests/              Python test suite
  docs/               GitHub Pages landing page
```

## Quick Start

### Prerequisites

- **Python 3.10+** for the daemon
- **Flutter SDK 3.0+** for the UI
- **Go 1.21+** for the relay server (optional)

### 1. Start the Python daemon

```bash
cd chitchat
pip install -e .
python core/daemon.py
```

The daemon starts mDNS discovery, opens TCP port 9877 for P2P, and listens on
`ws://127.0.0.1:9876` for the Flutter UI.

### 2. Run the Flutter app

```bash
cd app
flutter pub get
flutter run
```

### 3. (Optional) Run the relay server

```bash
cd server
go run main.go
# Or build a static binary:
go build -ldflags="-s -w" -o chitchat-relay main.go
```

The relay listens on `:9878` and handles WebSocket connections from daemons that
cannot reach each other directly.

## Development Phases

| Phase | Scope | Status |
|---|---|---|
| **MVP** | P2P text chat, mDNS discovery, Ed25519 identity, local SQLite storage | In progress |
| **V1.0** | Rich media (images, files, voice), relay fallback, typed indicators + receipts | Planned |
| **V1.5** | Group chats, message threads, contact favorites, search | Planned |
| **V2.0** | Voice/video calls, bot API plugin system, relay federation, channels | Planned |

## Contributing

Contributions are welcome. Please open an issue to discuss your idea before
submitting a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-idea`)
3. Commit your changes (`git commit -m 'Add amazing idea'`)
4. Push to the branch (`git push origin feature/amazing-idea`)
5. Open a Pull Request

## License

ChitChat is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for the full text.

---

<p align="center">
  <a href="https://github.com/chitchat">GitHub</a>
  &nbsp;&middot;&nbsp;
  <a href="https://chitchat.github.io">Website</a>
</p>
