# ChitChat

<p align="center">
  <strong>Chat that just works. LAN or cloud.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square" alt="License: Apache 2.0">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Web%20%7C%20any%20browser-lightgrey?style=flat-square" alt="Platforms: Windows, Web, any browser">
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
| **Cross-platform** | Any browser, no install | 4 | Many | 5 |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        UI LAYER (browser / Flutter)                     │
│           Material Design 3  ·  Dark Mode  ·  served by the daemon      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │  WebSocket (localhost:9876)
                               │  JSON-RPC (request / response + push events)
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          PYTHON DAEMON (core/)                          │
│                                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐   │
│   │ Discovery│  │ Transport│  │ Security │  │  Relay   │  │  Store  │   │
│   │  (mDNS)  │  │  (TCP)   │  │  (TLS)   │  │ (WS Tx)  │  │ (SQLite)│   │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘   │
│        │             │             │             │             │        │
│   mDNS │             │       TCP + TLS 1.3       │      WebSocket       │
│   SRV  │             │    AES-256-GCM (E2E)      │                      │
│        ▼             ▼                           ▼                      │
└───────────────┬──────────────────┬──────────────────────────────────────┘
                │                  │
       P2P LAN  │                  │ Internet / WAN
      (direct)  │                  │ (relay fallback)
                ▼                  ▼
      ┌──────────────┐     ┌───────────────────┐
      │   Peer B     │     │  GO RELAY SERVER  │
      │  (same LAN)  │     │  (server/main.go) │
      │              │     │  ~8 MB binary     │
      └──────────────┘     │  WebSocket hub    │
                           └────────┬──────────┘
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
The daemon runs anywhere Python 3.10+ runs, and its built-in web UI works in any
modern browser on **iOS, Android, Windows, macOS and Linux** — no app install
needed. An optional Flutter client ships with **Windows** and **Web** platform
folders; run `flutter create .` inside `app/` to generate the others.

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

## Quick Start — Same LAN (two devices, zero config)

### Prerequisites

- **Python 3.10+** — [python.org](https://python.org)
- A web browser (Chrome, Edge, Firefox, Safari — anything modern)

No Flutter SDK, Node.js or Go is required just to chat: the daemon serves its own
web UI.

### On each device

**Windows:**
```batch
run.bat
```

**macOS / Linux:**
```bash
chmod +x run.sh   # once, after downloading or unzipping
./run.sh
```
(If the executable bit got lost when the files were copied, `bash run.sh` always
works and skips the `chmod`.)

The first run creates `.venv` and installs dependencies automatically. After that
the daemon starts and **your browser opens at http://localhost:9875**. If it does
not open by itself, browse there manually.

Both devices will discover each other automatically via mDNS (Bonjour/Avahi) and
appear in the contact list within a few seconds.

Press **Ctrl+C** in the console to stop the daemon.

> **Firewall:** the first launch usually triggers a Windows Defender Firewall
> prompt. Allow access on **private networks** so peers can reach the P2P port
> (9877) and the Web UI (9875).
> On macOS the equivalent dialog says *"Do you want the application python3 to
> accept incoming network connections?"* — click **Allow**. Without it, other
> devices can be discovered but cannot connect back.

### macOS notes

- **Python 3.10+ is required.** The `/usr/bin/python3` shipped with older macOS is
  3.9 and will be rejected. Install a current one with
  `brew install python@3.12` or the [python.org installer](https://python.org),
  then check `python3 --version`.
- **Local Network permission (macOS 14+).** The first time the daemon runs, macOS
  asks whether the terminal may access the local network. If it was ever denied,
  discovery silently finds nothing: open **System Settings → Privacy & Security →
  Local Network** and enable it for Terminal (or iTerm / VS Code).
- **Gatekeeper:** if you downloaded the project as a zip, macOS may quarantine the
  extracted folder. Either run `xattr -dr com.apple.quarantine .` inside it, or
  simply `bash run.sh` — scripts run from Terminal are not blocked by quarantine.
- **Data lives in `~/.chitchat`.** Delete that folder to reset the device identity
  and local history.
- A macOS app bundle can be generated with `python3 install.py`; it appears as
  `ChitChat.app` in the project folder. The browser UI needs no bundle at all.

### Windows notes

- Double-click `run.bat`, or run `.\run.bat` from PowerShell / `run.bat` from cmd.
  No `chmod`, no extra tools — the batch file locates Python (`.venv`, then `py`,
  then `python`) and sets everything up on first launch.
- The first launch triggers a **Windows Defender Firewall** prompt. Allow access
  on **private networks**, otherwise peers can be seen but not reached.
- If "Windows protected your PC" (SmartScreen) appears for the downloaded archive,
  choose *More info → Run anyway* — it is an unsigned community build.
- Data lives in `%USERPROFILE%\.chitchat`. Delete that folder to reset identity
  and history.
- To run a second instance on the same PC (for testing), give it its own ports and
  data directory — see *Usage Scenarios* below.

### Linux notes

- Install Python **and** the venv module first; the latter is a separate package on
  Debian/Ubuntu and its absence is the most common first-run failure:

  ```bash
  sudo apt install python3 python3-venv      # Debian / Ubuntu / Mint
  sudo dnf install python3 python3-pip       # Fedora / RHEL
  sudo pacman -S python                      # Arch
  ```

- Open the firewall for the three TCP ports (skip if you are not running one):

  ```bash
  sudo ufw allow 9875/tcp   # Web UI
  sudo ufw allow 9876/tcp   # WebSocket for the browser UI
  sudo ufw allow 9877/tcp   # P2P chat
  ```

  mDNS discovery also needs **UDP 5353**; python-zeroconf handles the socket itself,
  but a firewall blocking 5353 will hide peers from each other.
- `run.sh` opens the page with `xdg-open`, which is simply skipped on a headless
  server — browse to `http://<host>:9875` from another machine instead.
- Data lives in `~/.chitchat`.

**Run it as a service** (headless box / Raspberry Pi):

```ini
# /etc/systemd/system/chitchat.service
[Unit]
Description=ChitChat daemon
After=network-online.target

[Service]
User=YOURUSER
WorkingDirectory=/opt/chitchat
ExecStart=/opt/chitchat/.venv/bin/python -m core.daemon --bind 0.0.0.0
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now chitchat
journalctl -u chitchat -f
```

---

### Sharing to another device

Want to put ChitChat on a USB stick or send it to another computer?

```bash
python share.py          # creates chitchat-share.zip
```

Copy the zip to the other device, extract it, then run `run.bat` (Windows) or
`./run.sh` (macOS/Linux) — or `python install.py` for a one-off setup.

---

## Usage Scenarios

| Scenario | How |
|---|---|
| **Two PCs on same WiFi** | Run `run.bat` / `./run.sh` on both. Both browsers open at `localhost:9875`. Auto-discovery connects them. |
| **PC + Phone (same WiFi)** | Run the launcher on the PC, then open `http://<PC-IP>:9875` on the phone. Both the HTTP and WebSocket ports listen on all interfaces by default. |
| **Two PCs on different networks** | Start the relay: `./server/relay-server.exe`. On each PC: `python -m core.daemon --relay ws://<RELAY_IP>:8080` |
| **Headless server / Raspberry Pi** | `python -m core.daemon --bind 0.0.0.0` (Web UI reachable from the LAN). No display needed. |
| **Several instances on one machine** | Give each its own ports and data directory: `python -m core.daemon --name B --p2p-port 19877 --ws-port 19876 --http-port 19875 --data-dir ./node-b` |

### CLI Options

```
python -m core.daemon --help

  --name, -n       Device name (default: hostname via launcher)
  --p2p-port       P2P TCP port (default: 9877)
  --http-port      Web UI HTTP port (default: 9875)
  --ws-port        WebSocket port used by the browser UI (default: 9876)
  --bind           HTTP bind address (default: 0.0.0.0)
  --ws-bind        WebSocket bind address (defaults to --bind)
  --relay          Relay server URL for cross-LAN messaging
  --data-dir       Where identity, database and config live
                   (default: $CHITCHAT_HOME or ~/.chitchat)
  --config         Path to an alternative config.json
  --debug          Verbose logging
```

Every file ChitChat persists — device identity, TLS key material, the SQLite
database and `config.json` — lives inside the data directory. Nothing is written
anywhere else on the machine.

### Flutter Desktop App (optional)

The Flutter client in `app/` talks to the same daemon over `ws://127.0.0.1:9876`.
It is optional and requires the Flutter SDK:

```bash
cd app
flutter pub get
flutter run -d windows    # or macos, linux
# Build release:
flutter build windows
```

### Relay Server (optional, Go)

```bash
cd server
go build -ldflags="-s -w" -o relay-server main.go  # ~8 MB
./relay-server                                      # listens on :8080
```

Docker:
```bash
cd server
docker build -t chitchat-relay .
docker run -p 8080:8080 chitchat-relay
```

### Tests

```bash
.venv/Scripts/python tests/run_tests.py     # Windows — no extra install needed
.venv/bin/python     tests/run_tests.py     # macOS / Linux
```

The runner is dependency-free. If you prefer pytest, `pip install pytest` and run
`python -m pytest` — the suite uses plain pytest-style tests.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser shows "Connecting…" forever | The daemon is not running, or another program owns port 9875/9876. Check the console and `--http-port`/`--ws-port`. |
| Peers never appear | Both devices must be on the same LAN, and mDNS (UDP 5353 + TCP 9877) must not be blocked by the firewall. |
| "Port 9877 is in use" | Another ChitChat instance is already running. Stop it, or pass `--p2p-port`. |
| Web UI is reachable from the LAN but messages fail | Allow the WebSocket port (9876) through the firewall as well — the page talks to it directly. |
| Want a clean identity | Delete the data directory (`~/.chitchat` by default) and restart. |

## Development Status

| Phase | Scope | Status |
|---|---|---|
| **Phase 1-2** | P2P text chat, mDNS discovery, Ed25519 identity, SQLite store, Web UI | Done — verified end-to-end (discovery → TLS pairing → bidirectional messages → delivery/read receipts) |
| **Phase 3** | Images, files, voice messages, link previews | Implemented; media is carried inside the message payload |
| **Phase 4** | Relay server, auto-failover, offline queue | Implemented (`server/main.go` + `core/relay`); not exercised in the default LAN setup |
| **Phase 5** | Group chat, threads, @mentions, reactions | Implemented (group invites create the group on the receiving side) |
| **Phase 6** | Keyboard shortcuts, PWA, notifications, accessibility | Implemented in the web UI |
| **V2.0** | Voice/video calls (WebRTC), bot/plugin API, Matrix bridge | Planned |

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
