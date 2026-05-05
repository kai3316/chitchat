// ChitChat Relay Server — v1.0
//
// A production-ready WebSocket relay for the ChitChat secure messaging
// platform.  Routes opaque (already-encrypted) message blobs between
// devices.  The relay never sees plaintext — it is a blind pipe.
//
// Build:
//     go build -o relay-server .
//
// Run:
//     export PORT=8080           # default 8080
//     export MAX_QUEUE=100       # max queued messages per offline device
//     ./relay-server
//
// Docker:
//     docker build -t chitchat-relay .
//     docker run -p 8080:8080 chitchat-relay
//
// API:
//     GET  /health            health check (clients + queue counts)
//     GET  /api/presence      list online device IDs
//     POST /api/send          HTTP message send  {to, from, payload}
//     WS   /ws                device WebSocket (auth via first message)

package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"sync"
	"syscall"
	"time"

	"github.com/gorilla/websocket"
)

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Config holds server settings sourced from environment variables.
type Config struct {
	Port     int // listen port (env: PORT, default 8080)
	MaxQueue int // max queued messages per offline device (env: MAX_QUEUE, default 100)
}

func loadConfig() Config {
	cfg := Config{Port: 8080, MaxQueue: 100}

	if v := os.Getenv("PORT"); v != "" {
		if p, err := strconv.Atoi(v); err == nil && p > 0 && p <= 65535 {
			cfg.Port = p
		}
	}
	if v := os.Getenv("MAX_QUEUE"); v != "" {
		if q, err := strconv.Atoi(v); err == nil && q > 0 {
			cfg.MaxQueue = q
		}
	}
	return cfg
}

// ---------------------------------------------------------------------------
// WebSocket upgrader
// ---------------------------------------------------------------------------

var upgrader = websocket.Upgrader{
	ReadBufferSize:  4096,
	WriteBufferSize: 4096,
	CheckOrigin:     func(r *http.Request) bool { return true },
}

// ---------------------------------------------------------------------------
// Data types
// ---------------------------------------------------------------------------

// Message is the envelope for relayed payloads (HTTP API).
type Message struct {
	To      string `json:"to"`
	From    string `json:"from,omitempty"`
	Payload string `json:"payload"` // base64-encoded encrypted blob
}

// Client represents one connected device.
type Client struct {
	DeviceID    string
	Fingerprint string          // hex-encoded SHA-256 of device certificate
	Conn        *websocket.Conn // owned by writePump
	Send        chan []byte     // buffered outbound channel
}

// Server is the relay core.  It owns the client registry and per-device
// message queues.
type Server struct {
	cfg Config

	mu       sync.RWMutex
	clients  map[string]*Client // device_id → active connection
	queues   map[string][][]byte // device_id → queued raw messages
	presence map[string]bool    // device_id → online

	register   chan *Client
	unregister chan *Client
}

// NewServer creates a Server from the given Config.
func NewServer(cfg Config) *Server {
	return &Server{
		cfg:        cfg,
		clients:    make(map[string]*Client),
		queues:     make(map[string][][]byte),
		presence:   make(map[string]bool),
		register:   make(chan *Client, 256),
		unregister: make(chan *Client, 256),
	}
}

// ---------------------------------------------------------------------------
// Event loop
// ---------------------------------------------------------------------------

// Run is the central event loop.  All register / unregister operations are
// serialised through this goroutine so the clients map can be updated safely
// without holding locks during I/O.
func (s *Server) Run(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case c := <-s.register:
			s.registerClient(c)
		case c := <-s.unregister:
			s.unregisterClient(c)
		}
	}
}

func (s *Server) registerClient(c *Client) {
	s.mu.Lock()

	// Kick any previous connection for the same device.
	if old, ok := s.clients[c.DeviceID]; ok {
		delete(s.clients, c.DeviceID)
		close(old.Send)   // wake writePump so it exits cleanly
		old.Conn.Close()  // wake readPump
	}

	s.clients[c.DeviceID] = c
	s.presence[c.DeviceID] = true

	// Drain queued messages into the new client's send buffer.
	if queue := s.queues[c.DeviceID]; len(queue) > 0 {
		for _, raw := range queue {
			select {
			case c.Send <- raw:
			default:
				// send buffer full — drop
			}
		}
		delete(s.queues, c.DeviceID)
	}
	s.mu.Unlock()

	s.broadcastPresence(c.DeviceID, "online")
	log.Printf("device connected    id=%-44s fp=%s", trunc(c.DeviceID, 44), trunc(c.Fingerprint, 16))
}

func (s *Server) unregisterClient(c *Client) {
	s.mu.Lock()
	// Only remove if it's still the same client (could have been replaced).
	if cur, ok := s.clients[c.DeviceID]; ok && cur == c {
		delete(s.clients, c.DeviceID)
		delete(s.presence, c.DeviceID)
		close(c.Send)
	}
	s.mu.Unlock()

	s.broadcastPresence(c.DeviceID, "offline")
	log.Printf("device disconnected id=%-44s fp=%s", trunc(c.DeviceID, 44), trunc(c.Fingerprint, 16))
}

func trunc(s string, n int) string {
	if len(s) > n {
		return s[:n]
	}
	return s
}

// ---------------------------------------------------------------------------
// Authentication
// ---------------------------------------------------------------------------

// authenticate extracts the device certificate fingerprint from the request.
// Accepts X-Device-Fingerprint header or ?fp= query parameter.
// Returns a normalised hex string or an error.
func authenticate(r *http.Request) (string, error) {
	fp := r.Header.Get("X-Device-Fingerprint")
	if fp == "" {
		fp = r.URL.Query().Get("fp")
	}
	if fp == "" {
		return "", fmt.Errorf("missing device fingerprint")
	}

	// Try hex decode; if that fails, hash the raw string for consistency.
	raw, err := hex.DecodeString(fp)
	if err != nil {
		h := sha256.Sum256([]byte(fp))
		return hex.EncodeToString(h[:]), nil
	}
	if len(raw) < 16 {
		return "", fmt.Errorf("fingerprint too short")
	}
	return hex.EncodeToString(raw), nil
}

// ---------------------------------------------------------------------------
// WebSocket handler
// ---------------------------------------------------------------------------

// handleWS upgrades the HTTP connection to WebSocket and handles the device
// lifecycle.  The first message MUST be an auth frame:
//
//	{"type":"auth","device_id":"<id>"}
func (s *Server) handleWS(w http.ResponseWriter, r *http.Request) {
	fingerprint, err := authenticate(r)
	if err != nil {
		writeJSON(w, http.StatusUnauthorized, map[string]string{"error": err.Error()})
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("ws upgrade error: %v", err)
		return
	}

	// Read auth frame with a deadline.
	conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	var auth struct {
		Type     string `json:"type"`
		DeviceID string `json:"device_id"`
	}
	if err := conn.ReadJSON(&auth); err != nil || auth.Type != "auth" || auth.DeviceID == "" {
		log.Printf("ws auth failed: %v", err)
		conn.Close()
		return
	}
	conn.SetReadDeadline(time.Time{})

	client := &Client{
		DeviceID:    auth.DeviceID,
		Fingerprint: fingerprint,
		Conn:        conn,
		Send:        make(chan []byte, 64),
	}

	s.register <- client

	go s.writePump(client) // write goroutine
	s.readPump(client)      // blocks until disconnect
}

// ---------------------------------------------------------------------------
// Write pump — single writer per connection (gorilla/websocket requirement)
// ---------------------------------------------------------------------------

func (s *Server) writePump(c *Client) {
	ticker := time.NewTicker(30 * time.Second)
	defer func() {
		ticker.Stop()
		c.Conn.Close()
	}()

	for {
		select {
		case msg, ok := <-c.Send:
			if !ok {
				// Channel closed — send close frame and exit.
				c.Conn.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
				return
			}
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.Conn.WriteMessage(websocket.TextMessage, msg); err != nil {
				return
			}
		case <-ticker.C:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// ---------------------------------------------------------------------------
// Read pump — blocks reading from the WebSocket until close / error
// ---------------------------------------------------------------------------

func (s *Server) readPump(c *Client) {
	defer func() {
		s.unregister <- c
		c.Conn.Close()
	}()

	c.Conn.SetReadLimit(65536) // 64 KiB max frame
	c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.Conn.SetPongHandler(func(string) error {
		c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, raw, err := c.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				log.Printf("ws read error from %s: %v", c.DeviceID, err)
			}
			break
		}

		// Parse the bare minimum to extract the target device.
		var envelope struct {
			To      string          `json:"to"`
			Payload string          `json:"payload,omitempty"`
			Data    json.RawMessage `json:"data,omitempty"`
		}
		if err := json.Unmarshal(raw, &envelope); err != nil {
			log.Printf("ws bad message from %s: %v", c.DeviceID, err)
			continue
		}
		if envelope.To == "" {
			log.Printf("ws message from %s missing 'to'", c.DeviceID)
			continue
		}

		// Rewrite the envelope to include the authenticated sender.
		out := map[string]interface{}{"to": envelope.To, "from": c.DeviceID}
		if envelope.Payload != "" {
			out["payload"] = envelope.Payload
		}
		if envelope.Data != nil {
			out["data"] = envelope.Data
		}
		routed, _ := json.Marshal(out)

		s.routeMessage(envelope.To, routed)
	}
}

// ---------------------------------------------------------------------------
// Message routing
// ---------------------------------------------------------------------------

// routeMessage delivers raw to the target device if online, otherwise queues it.
func (s *Server) routeMessage(to string, raw []byte) {
	s.mu.RLock()
	target, ok := s.clients[to]
	s.mu.RUnlock()

	if ok {
		select {
		case target.Send <- raw:
			return
		default:
			// Send buffer full — fall through to queue.
		}
	}
	s.queueMessage(to, raw)
}

// queueMessage appends raw to the per-device queue, respecting MaxQueue.
func (s *Server) queueMessage(deviceID string, raw []byte) {
	s.mu.Lock()
	defer s.mu.Unlock()

	q := s.queues[deviceID]
	if len(q) >= s.cfg.MaxQueue {
		q = q[1:] // drop oldest
	}
	q = append(q, raw)
	s.queues[deviceID] = q
}

// ---------------------------------------------------------------------------
// HTTP API: POST /api/send
// ---------------------------------------------------------------------------

// handleSend accepts messages from non-WebSocket senders (e.g. notification
// services, other backend components).
//
//	POST /api/send
//	Content-Type: application/json
//	{"to":"<device_id>", "from":"<sender_id>", "payload":"<base64>"}
func (s *Server) handleSend(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "method not allowed"})
		return
	}

	_, err := authenticate(r)
	if err != nil {
		writeJSON(w, http.StatusUnauthorized, map[string]string{"error": err.Error()})
		return
	}

	var msg Message
	if err := json.NewDecoder(r.Body).Decode(&msg); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON"})
		return
	}
	defer r.Body.Close()

	if msg.To == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "missing 'to' field"})
		return
	}
	if msg.Payload == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "missing 'payload' field"})
		return
	}

	envelope, _ := json.Marshal(map[string]string{
		"to":      msg.To,
		"from":    msg.From,
		"payload": msg.Payload,
	})

	s.mu.RLock()
	target, online := s.clients[msg.To]
	s.mu.RUnlock()

	delivered := false
	if online {
		select {
		case target.Send <- envelope:
			delivered = true
		default:
		}
	}
	if !delivered {
		s.queueMessage(msg.To, envelope)
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"status":    "ok",
		"delivered": delivered,
		"queued":    !delivered,
	})
}

// ---------------------------------------------------------------------------
// HTTP API: GET /health
// ---------------------------------------------------------------------------

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	clientCount := len(s.clients)
	presenceCount := len(s.presence)
	var queuedTotal int
	for _, q := range s.queues {
		queuedTotal += len(q)
	}
	s.mu.RUnlock()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"status":    "ok",
		"time":      time.Now().Unix(),
		"clients":   clientCount,
		"presence":  presenceCount,
		"queued":    queuedTotal,
		"max_queue": s.cfg.MaxQueue,
	})
}

// ---------------------------------------------------------------------------
// HTTP API: GET /api/presence
// ---------------------------------------------------------------------------

func (s *Server) handlePresence(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	devices := make([]string, 0, len(s.presence))
	for id := range s.presence {
		devices = append(devices, id)
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"online": devices,
		"count":  len(devices),
	})
}

// ---------------------------------------------------------------------------
// Presence broadcast
// ---------------------------------------------------------------------------

func (s *Server) broadcastPresence(deviceID, status string) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	payload, _ := json.Marshal(map[string]interface{}{
		"event": "presence",
		"data":  map[string]string{"peer_id": deviceID, "status": status},
	})

	for id, c := range s.clients {
		if id != deviceID {
			select {
			case c.Send <- payload:
			default:
			}
		}
	}
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

func main() {
	cfg := loadConfig()
	srv := NewServer(cfg)

	mux := http.NewServeMux()
	mux.HandleFunc("/ws", srv.handleWS)
	mux.HandleFunc("/health", srv.handleHealth)
	mux.HandleFunc("/api/send", srv.handleSend)
	mux.HandleFunc("/api/presence", srv.handlePresence)

	httpServer := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Port),
		Handler:      mux,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Central event loop.
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go srv.Run(ctx)

	// Graceful shutdown.
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-quit
		log.Println("shutting down ...")

		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer shutdownCancel()

		if err := httpServer.Shutdown(shutdownCtx); err != nil {
			log.Printf("http shutdown error: %v", err)
		}
		cancel() // stop srv.Run event loop
	}()

	log.Printf("ChitChat relay starting on :%d  (max_queue=%d)", cfg.Port, cfg.MaxQueue)
	if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("server error: %v", err)
	}
	log.Println("server stopped")
}
