package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

type Server struct {
	mu       sync.RWMutex
	clients  map[string]*websocket.Conn // device_id -> conn
	queues   map[string][]json.RawMessage
}

func NewServer() *Server {
	return &Server{
		clients: make(map[string]*websocket.Conn),
		queues:  make(map[string][]json.RawMessage),
	}
}

func (s *Server) handleWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("Upgrade error: %v", err)
		return
	}
	defer conn.Close()

	// First message must be auth with device_id
	var auth struct {
		Type     string `json:"type"`
		DeviceID string `json:"device_id"`
	}
	if err := conn.ReadJSON(&auth); err != nil || auth.Type != "auth" {
		log.Printf("Auth failed: %v", err)
		return
	}

	deviceID := auth.DeviceID
	s.mu.Lock()
	s.clients[deviceID] = conn
	// Deliver queued messages
	if queue, ok := s.queues[deviceID]; ok {
		for _, msg := range queue {
			conn.WriteMessage(websocket.TextMessage, msg)
		}
		delete(s.queues, deviceID)
	}
	s.mu.Unlock()

	log.Printf("Device connected: %s", deviceID[:12])

	// Send presence
	s.broadcast(deviceID, map[string]interface{}{
		"event": "presence", "data": map[string]string{
			"peer_id": deviceID, "status": "online",
		},
	})

	defer func() {
		s.mu.Lock()
		delete(s.clients, deviceID)
		s.mu.Unlock()
		s.broadcast(deviceID, map[string]interface{}{
			"event": "presence", "data": map[string]string{
				"peer_id": deviceID, "status": "offline",
			},
		})
		log.Printf("Device disconnected: %s", deviceID[:12])
	}()

	for {
		_, raw, err := conn.ReadMessage()
		if err != nil {
			break
		}

		var msg struct {
			To   string `json:"to"`
			Data json.RawMessage `json:"data"`
		}
		if err := json.Unmarshal(raw, &msg); err != nil {
			continue
		}

		s.mu.RLock()
		targetConn, ok := s.clients[msg.To]
		s.mu.RUnlock()

		if ok {
			targetConn.WriteMessage(websocket.TextMessage, raw)
		} else {
			// Queue for later delivery
			s.mu.Lock()
			s.queues[msg.To] = append(s.queues[msg.To], raw)
			s.mu.Unlock()
		}
	}
}

func (s *Server) broadcast(fromDeviceID string, data interface{}) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	raw, _ := json.Marshal(data)
	for id, conn := range s.clients {
		if id != fromDeviceID {
			conn.WriteMessage(websocket.TextMessage, raw)
		}
	}
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "ok", "time": time.Now().Unix(),
		"clients": len(s.clients),
	})
}

func main() {
	srv := NewServer()
	http.HandleFunc("/ws", srv.handleWS)
	http.HandleFunc("/health", srv.handleHealth)

	addr := ":9878"
	log.Printf("ChitChat relay server starting on %s", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatal(err)
	}
}
