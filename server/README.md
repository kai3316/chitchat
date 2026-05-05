# ChitChat Relay Server

A blind relay for the ChitChat secure messaging platform.  The server routes
encrypted message blobs between devices over WebSocket — it never decrypts or
inspects plaintext.

## Quick Start

```bash
go build -o relay-server .
./relay-server
```

With custom port and queue size:

```bash
PORT=9090 MAX_QUEUE=200 ./relay-server
```

## Docker

Build the image:

```bash
docker build -t chitchat-relay .
```

Run:

```bash
docker run -p 8080:8080 chitchat-relay
```

With environment variables:

```bash
docker run -p 9090:9090 -e PORT=9090 -e MAX_QUEUE=200 chitchat-relay
```

## API Endpoints

### GET /health

Health check.  Returns client count, presence count, and queued message totals.

```json
{
  "status": "ok",
  "time": 1712345678,
  "clients": 42,
  "presence": 42,
  "queued": 0,
  "max_queue": 100
}
```

### GET /api/presence

List currently online device IDs.

```json
{
  "online": ["device-a", "device-b"],
  "count": 2
}
```

### POST /api/send

Send a message to a device via HTTP (alternative to the WebSocket channel).

**Headers:**
- `Content-Type: application/json`
- `X-Device-Fingerprint: <hex>` (required, or pass `?fp=<hex>` as query param)

**Body:**

```json
{
  "to": "<recipient-device-id>",
  "from": "<sender-device-id>",
  "payload": "<base64-encoded-encrypted-blob>"
}
```

**Response 200 OK:**

```json
{
  "status": "ok",
  "delivered": true,
  "queued": false
}
```

### WS /ws

WebSocket endpoint for persistent device connections.

**Query params:** `?fp=<hex-fingerprint>` (or `X-Device-Fingerprint` header)

**First message (auth):**

```json
{"type": "auth", "device_id": "<device-id>"}
```

**Subsequent messages (relay):**

```json
{"to": "<recipient-id>", "payload": "<base64>"}
```

The server adds `"from"` automatically from the authenticated device ID.

**Incoming messages:**

```json
{"to": "<your-device-id>", "from": "<sender-id>", "payload": "<base64>"}
```

**Presence events (broadcast):**

```json
{"event": "presence", "data": {"peer_id": "<device-id>", "status": "online"}}
{"event": "presence", "data": {"peer_id": "<device-id>", "status": "offline"}}
```

## Environment Variables

| Variable     | Default | Description                                  |
|-------------|---------|----------------------------------------------|
| `PORT`      | `8080`  | TCP listen port                              |
| `MAX_QUEUE` | `100`   | Max queued messages per offline device       |

## Architecture

- One goroutine per connected device (read pump).
- One goroutine per connected device (write pump with buffered channel).
- Central event loop serialises register/unregister operations.
- Message routing via buffered channels — no lock held during I/O.
- Graceful shutdown on SIGINT / SIGTERM (drains in-flight messages, 10 s deadline).

## Security Model

The relay is a **blind pipe**.  All message payloads are pre-encrypted by the
clients before they reach the server.  The server authenticates devices via
their certificate fingerprint but never possesses the private key and cannot
decrypt any message content.
