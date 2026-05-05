# ChitChat Web UI — embedded SPA served by the daemon
WEB_UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>ChitChat</title>
<style>
:root {
  --bg-primary: #121212;
  --bg-secondary: #1e1e1e;
  --bg-tertiary: #2c2c2c;
  --bg-surface: #1a1a2e;
  --bg-card: #252536;
  --bg-input: #2a2a3e;
  --accent: #6750A4;
  --accent-light: #7c67c4;
  --accent-dark: #523b8e;
  --accent-glow: rgba(103, 80, 164, 0.3);
  --text-primary: #e8e8f0;
  --text-secondary: #b0b0c0;
  --text-muted: #6c6c80;
  --border: #383850;
  --success: #4caf50;
  --danger: #ef5350;
  --unread: #6750A4;
  --bubble-sent: #6750A4;
  --bubble-sent-text: #ffffff;
  --bubble-received: #2c2c3e;
  --bubble-received-text: #e0e0e8;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.5);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --radius-xl: 24px;
  --radius-bubble: 18px;
  --sidebar-width: 280px;
  --header-height: 64px;
  --input-height: 56px;
  --transition: 0.2s ease;
}

*, *::before, *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

/* ── App Container ── */
.app {
  display: flex;
  height: 100vh;
  height: 100dvh;
  position: relative;
  overflow: hidden;
}

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  height: 100%;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 10;
  transition: transform var(--transition);
}

.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  height: var(--header-height);
}

.sidebar-header h1 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, var(--accent-light), #b39ddb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.connection-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--danger);
  flex-shrink: 0;
  transition: background 0.3s ease;
  box-shadow: 0 0 6px rgba(239, 83, 80, 0.5);
}

.connection-dot.connected {
  background: var(--success);
  box-shadow: 0 0 6px rgba(76, 175, 80, 0.5);
}

.connection-dot.reconnecting {
  background: #ff9800;
  box-shadow: 0 0 6px rgba(255, 152, 0, 0.5);
  animation: blink 1s ease infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.contact-search {
  padding: 12px 16px;
  flex-shrink: 0;
}

.contact-search input {
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color var(--transition);
}

.contact-search input:focus {
  border-color: var(--accent);
}

.contact-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

.contact-list::-webkit-scrollbar {
  width: 4px;
}

.contact-list::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}

.contact-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background var(--transition);
  border-bottom: 1px solid rgba(56, 56, 80, 0.4);
  position: relative;
}

.contact-item:hover {
  background: var(--bg-tertiary);
}

.contact-item.active {
  background: rgba(103, 80, 164, 0.15);
  border-left: 3px solid var(--accent);
}

.contact-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
  position: relative;
}

.contact-online-dot {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--success);
  border: 2px solid var(--bg-secondary);
  display: none;
}

.contact-item.online .contact-online-dot {
  display: block;
}

.contact-info {
  margin-left: 12px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.contact-name {
  font-size: 15px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.contact-preview {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.contact-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
  margin-left: 8px;
}

.contact-time {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.contact-unread {
  margin-top: 4px;
  background: var(--unread);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

/* ── Chat Area ── */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
}

.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  gap: 12px;
}

.chat-empty-icon {
  font-size: 64px;
  opacity: 0.3;
}

.chat-empty-text {
  font-size: 16px;
}

.chat-empty-sub {
  font-size: 13px;
  color: var(--text-muted);
  opacity: 0.7;
}

/* ── Chat Header ── */
.chat-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: rgba(30, 30, 30, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  gap: 12px;
  z-index: 5;
}

.chat-header .back-btn {
  display: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: none;
  color: var(--text-primary);
  font-size: 18px;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background var(--transition);
}

.chat-header .back-btn:hover {
  background: var(--border);
}

.chat-header .contact-avatar {
  width: 40px;
  height: 40px;
  font-size: 16px;
}

.chat-header-info {
  flex: 1;
  min-width: 0;
}

.chat-header-name {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-header-status {
  font-size: 12px;
  color: var(--text-secondary);
}

.chat-header-status.online {
  color: var(--success);
}

/* ── Messages ── */
.messages-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px 20px;
  scroll-behavior: smooth;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.messages-container::-webkit-scrollbar {
  width: 4px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}

.message-row {
  display: flex;
  margin-bottom: 4px;
  animation: fadeInUp 0.2s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.message-row.sent {
  justify-content: flex-end;
}

.message-row.received {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: var(--radius-bubble);
  position: relative;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.45;
  font-size: 14px;
}

.message-row.sent .message-bubble {
  background: var(--bubble-sent);
  color: var(--bubble-sent-text);
  border-bottom-right-radius: 6px;
}

.message-row.received .message-bubble {
  background: var(--bubble-received);
  color: var(--bubble-received-text);
  border-bottom-left-radius: 6px;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 11px;
}

.message-row.sent .message-meta {
  justify-content: flex-end;
  color: rgba(255,255,255,0.7);
}

.message-row.received .message-meta {
  color: var(--text-muted);
}

.message-checkmarks {
  display: inline-flex;
  gap: 1px;
}

.message-checkmarks .ck {
  font-size: 10px;
}

.message-checkmarks.read .ck {
  color: #64b5f6;
}

/* ── Typing Indicator ── */
.typing-indicator {
  display: none;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.typing-indicator.visible {
  display: flex;
}

.typing-dots {
  display: flex;
  gap: 3px;
  align-items: center;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: bounce 1.2s infinite ease;
}

.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

/* ── No Messages ── */
.no-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  gap: 8px;
  padding: 40px;
}

.no-messages-icon {
  font-size: 48px;
  opacity: 0.3;
}

.no-messages-text {
  font-size: 15px;
}

/* ── Input Area ── */
.input-area {
  padding: 10px 16px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
  background: var(--bg-secondary);
}

.input-area textarea {
  flex: 1;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  line-height: 1.4;
  outline: none;
  resize: none;
  min-height: 40px;
  max-height: 120px;
  transition: border-color var(--transition);
  overflow-y: auto;
}

.input-area textarea:focus {
  border-color: var(--accent);
}

.input-area textarea::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background var(--transition), transform 0.1s ease;
  box-shadow: 0 2px 8px var(--accent-glow);
}

.send-btn:hover {
  background: var(--accent-light);
}

.send-btn:active {
  transform: scale(0.95);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── Connection Overlay ── */
.connection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 8px 16px;
  background: rgba(239, 83, 80, 0.9);
  color: #fff;
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  z-index: 100;
  display: none;
  animation: slideDown 0.3s ease;
}

.connection-overlay.visible {
  display: block;
}

.connection-overlay.reconnecting {
  background: rgba(255, 152, 0, 0.9);
}

@keyframes slideDown {
  from { transform: translateY(-100%); }
  to   { transform: translateY(0); }
}

/* ── Sound Toggle ── */
.sound-toggle {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  transition: background var(--transition);
}

.sound-toggle:hover {
  background: var(--border);
}

/* ── Mobile Responsive ── */
@media (max-width: 767px) {
  .sidebar {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    min-width: 100%;
    z-index: 20;
    transform: translateX(0);
  }

  .sidebar.hidden {
    transform: translateX(-100%);
  }

  .chat-area {
    width: 100%;
  }

  .chat-header .back-btn {
    display: flex;
  }

  .message-bubble {
    max-width: 85%;
  }

  .connection-overlay {
    padding: 6px 12px;
    font-size: 12px;
  }
}

/* ── Utility ── */
.hidden {
  display: none !important;
}
</style>
</head>
<body>

<div class="app" id="app">
  <!-- Connection overlay -->
  <div class="connection-overlay" id="connectionOverlay">Connecting...</div>

  <!-- Sidebar -->
  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <h1>ChitChat</h1>
      <div class="connection-dot" id="connectionDot" title="Disconnected"></div>
    </div>
    <div class="contact-search">
      <input type="text" id="contactSearch" placeholder="Search contacts..." autocomplete="off">
    </div>
    <div class="contact-list" id="contactList"></div>
  </div>

  <!-- Chat Area -->
  <div class="chat-area" id="chatArea">
    <!-- Empty state -->
    <div class="chat-empty" id="chatEmpty">
      <div class="chat-empty-icon">&#9998;</div>
      <div class="chat-empty-text">Select a contact to start chatting</div>
      <div class="chat-empty-sub">Your conversations are end-to-end encrypted</div>
    </div>

    <!-- Active chat -->
    <div class="chat-header hidden" id="chatHeader">
      <button class="back-btn" id="backBtn" title="Back to contacts">&#8592;</button>
      <div class="contact-avatar" id="chatAvatar">?</div>
      <div class="chat-header-info">
        <div class="chat-header-name" id="chatName"></div>
        <div class="chat-header-status" id="chatStatus">Offline</div>
      </div>
    </div>

    <div class="messages-container hidden" id="messagesContainer"></div>
    <div class="no-messages hidden" id="noMessages">
      <div class="no-messages-icon">&#128172;</div>
      <div class="no-messages-text">No messages yet</div>
    </div>

    <div class="typing-indicator" id="typingIndicator">
      <span id="typingLabel"></span>
      <div class="typing-dots"><span></span><span></span><span></span></div>
    </div>

    <div class="input-area hidden" id="inputArea">
      <textarea id="messageInput" placeholder="Type a message..." rows="1"></textarea>
      <button class="send-btn" id="sendBtn" title="Send message" disabled>&#8593;</button>
    </div>
  </div>

  <!-- Sound toggle -->
  <button class="sound-toggle" id="soundToggle" title="Sound off">&#128264;</button>
</div>

<script>
(function () {
  'use strict';

  // ═══════════════════════════════════════════════════════════════
  // State
  // ═══════════════════════════════════════════════════════════════
  const state = {
    contacts: [],           // Array of contact objects from get_contacts
    activePeer: null,       // Currently selected peer_id (string) or null
    messages: {},           // { [peer_id]: [message] }
    connected: false,       // WebSocket connected
    reconnectAttempt: 0,
    ws: null,
    pollTimer: null,        // setInterval handle for polling contacts
    typingTimers: {},       // { [peer_id]: setTimeout } for auto-hide typing
    soundEnabled: false,
    reconnectDelay: 1000,   // Current backoff delay
    typingSentAt: 0,        // Last time we sent a typing indicator
  };

  // ═══════════════════════════════════════════════════════════════
  // DOM refs
  // ═══════════════════════════════════════════════════════════════
  const $ = (sel) => document.querySelector(sel);
  const dom = {
    sidebar:          $('#sidebar'),
    contactList:      $('#contactList'),
    contactSearch:    $('#contactSearch'),
    connectionDot:    $('#connectionDot'),
    connectionOverlay:$('#connectionOverlay'),
    chatArea:         $('#chatArea'),
    chatEmpty:        $('#chatEmpty'),
    chatHeader:       $('#chatHeader'),
    chatAvatar:       $('#chatAvatar'),
    chatName:         $('#chatName'),
    chatStatus:       $('#chatStatus'),
    messagesContainer:$('#messagesContainer'),
    noMessages:       $('#noMessages'),
    typingIndicator:  $('#typingIndicator'),
    typingLabel:      $('#typingLabel'),
    inputArea:        $('#inputArea'),
    messageInput:     $('#messageInput'),
    sendBtn:          $('#sendBtn'),
    backBtn:          $('#backBtn'),
    soundToggle:      $('#soundToggle'),
  };

  // ═══════════════════════════════════════════════════════════════
  // WebSocket
  // ═══════════════════════════════════════════════════════════════
  let requestId = 0;
  const pendingRequests = new Map();

  function connectWebSocket() {
    if (state.ws && (state.ws.readyState === WebSocket.CONNECTING ||
                     state.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    const wsUrl = 'ws://' + location.hostname + ':9876';
    const ws = new WebSocket(wsUrl);
    state.ws = ws;

    ws.onopen = function () {
      state.connected = true;
      state.reconnectAttempt = 0;
      state.reconnectDelay = 1000;
      updateConnectionUI(true);

      // Poll contacts immediately and start interval
      fetchContacts();
      startPolling();

      // If we have an active peer, reload history
      if (state.activePeer) {
        loadHistory(state.activePeer);
      }
    };

    ws.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        // Ignore parse errors
      }
    };

    ws.onclose = function () {
      state.connected = false;
      updateConnectionUI(false);
      stopPolling();
      scheduleReconnect();
    };

    ws.onerror = function () {
      // onclose will fire after this
    };
  }

  function scheduleReconnect() {
    state.reconnectAttempt++;
    const delay = Math.min(state.reconnectDelay, 30000);
    state.reconnectDelay = Math.min(state.reconnectDelay * 2, 30000);
    updateConnectionUI(false);

    setTimeout(function () {
      if (!state.connected) {
        connectWebSocket();
      }
    }, delay);
  }

  function sendRPC(method, params, expectResponse) {
    return new Promise(function (resolve, reject) {
      if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('Not connected'));
        return;
      }

      var id = ++requestId;
      var msg = { method: method, params: params || {} };
      if (expectResponse !== false) {
        msg.id = id;
        pendingRequests.set(id, { resolve: resolve, reject: reject, ts: Date.now() });
        // Timeout after 15s
        setTimeout(function () {
          if (pendingRequests.has(id)) {
            pendingRequests.delete(id);
            reject(new Error('Request timeout'));
          }
        }, 15000);
      }

      try {
        state.ws.send(JSON.stringify(msg));
        if (expectResponse === false) {
          resolve(null);
        }
      } catch (e) {
        if (expectResponse !== false) {
          pendingRequests.delete(id);
        }
        reject(e);
      }
    });
  }

  function handleMessage(data) {
    // Check if it's a response to a pending request
    if (data.id !== undefined && data.result !== undefined) {
      var pending = pendingRequests.get(data.id);
      if (pending) {
        pendingRequests.delete(data.id);
        pending.resolve(data.result);
      }
      return;
    }

    // Check for error response
    if (data.id !== undefined && data.error !== undefined) {
      var p = pendingRequests.get(data.id);
      if (p) {
        pendingRequests.delete(data.id);
        p.reject(new Error(data.error));
      }
      return;
    }

    // It's a server-pushed event
    if (data.event === undefined || data.data === undefined) {
      return;
    }

    handleEvent(data.event, data.data);
  }

  // ═══════════════════════════════════════════════════════════════
  // Event Handlers
  // ═══════════════════════════════════════════════════════════════
  function handleEvent(event, payload) {
    switch (event) {
      case 'message_received':
        handleMessageReceived(payload);
        break;
      case 'peer_online':
        handlePeerOnline(payload.peer_id);
        break;
      case 'peer_offline':
        handlePeerOffline(payload.peer_id);
        break;
      case 'typing':
        handleTyping(payload.peer_id);
        break;
      case 'message_delivered':
        handleMessageDelivered(payload.msg_id);
        break;
      case 'read_receipt':
        handleReadReceipt(payload.peer_id);
        break;
    }
  }

  function handleMessageReceived(msg) {
    var peerId = msg.peer_id;
    if (!state.messages[peerId]) {
      state.messages[peerId] = [];
    }

    // Avoid duplicates
    var exists = state.messages[peerId].some(function (m) { return m.msg_id === msg.msg_id; });
    if (!exists) {
      state.messages[peerId].push(msg);
    }

    // Update contacts list (refresh)
    fetchContacts();

    // If this peer is active, render messages
    if (state.activePeer === peerId) {
      renderMessages(peerId);
      // Mark as read
      sendRPC('mark_read', { peer_id: peerId }, false).catch(function () {});
    }

    // Play sound if enabled
    if (state.soundEnabled) {
      playMessageSound();
    }
  }

  function handlePeerOnline(peerId) {
    updateContactOnlineStatus(peerId, true);
    if (state.activePeer === peerId) {
      dom.chatStatus.textContent = 'Online';
      dom.chatStatus.className = 'chat-header-status online';
    }
  }

  function handlePeerOffline(peerId) {
    updateContactOnlineStatus(peerId, false);
    if (state.activePeer === peerId) {
      dom.chatStatus.textContent = 'Offline';
      dom.chatStatus.className = 'chat-header-status';
    }
  }

  function handleTyping(peerId) {
    if (state.activePeer !== peerId) return;

    // Show typing indicator
    var contact = state.contacts.find(function (c) { return c.device_id === peerId; });
    var name = contact ? contact.device_name : 'Someone';
    dom.typingLabel.textContent = name + ' is typing';
    dom.typingIndicator.classList.add('visible');

    // Auto-hide after 3 seconds
    if (state.typingTimers[peerId]) {
      clearTimeout(state.typingTimers[peerId]);
    }
    state.typingTimers[peerId] = setTimeout(function () {
      dom.typingIndicator.classList.remove('visible');
      delete state.typingTimers[peerId];
    }, 3000);

    scrollToBottom();
  }

  function handleMessageDelivered(msgId) {
    // Update delivered status in all message arrays
    Object.keys(state.messages).forEach(function (peerId) {
      var msgs = state.messages[peerId];
      for (var i = 0; i < msgs.length; i++) {
        if (msgs[i].msg_id === msgId) {
          msgs[i].delivered = true;
          if (state.activePeer === peerId) {
            renderMessages(peerId);
          }
          break;
        }
      }
    });
  }

  function handleReadReceipt(peerId) {
    var msgs = state.messages[peerId];
    if (!msgs) return;
    var changed = false;
    for (var i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].direction === 'sent' && msgs[i].delivered) {
        msgs[i].read = true;
        changed = true;
      }
    }
    if (changed && state.activePeer === peerId) {
      renderMessages(peerId);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // API Calls
  // ═══════════════════════════════════════════════════════════════
  function fetchContacts() {
    sendRPC('get_contacts', {}).then(function (result) {
      state.contacts = result.contacts || [];
      renderContactList();
    }).catch(function () {
      // Will retry on next poll
    });
  }

  function loadHistory(peerId) {
    sendRPC('get_history', { peer_id: peerId, limit: 50 }).then(function (result) {
      state.messages[peerId] = result.messages || [];
      renderMessages(peerId);

      // Mark as read
      sendRPC('mark_read', { peer_id: peerId }, false).catch(function () {});

      // Refresh contacts to update unread counts
      fetchContacts();
    }).catch(function () {
      // Show empty if load fails
      renderMessages(peerId);
    });
  }

  function sendMessage(body) {
    if (!state.activePeer || !body.trim()) return;

    var peerId = state.activePeer;
    sendRPC('send_message', {
      peer_id: peerId,
      type: 'chat_text',
      body: body.trim()
    }).then(function (result) {
      // Add locally if not already added from event
      if (!state.messages[peerId]) {
        state.messages[peerId] = [];
      }
      var exists = state.messages[peerId].some(function (m) { return m.msg_id === result.msg_id; });
      if (!exists) {
        state.messages[peerId].push({
          msg_id: result.msg_id,
          peer_id: peerId,
          direction: 'sent',
          msg_type: 'chat_text',
          body: body.trim(),
          timestamp: result.timestamp,
          delivered: result.sent,
          read: false
        });
      }
      renderMessages(peerId);
      fetchContacts();
    }).catch(function (err) {
      // Show error inline or retry
      console.error('Failed to send:', err);
    });
  }

  function sendTypingIndicator() {
    if (!state.activePeer) return;
    var now = Date.now();
    if (now - state.typingSentAt < 2000) return; // debounce: max once per 2s
    state.typingSentAt = now;
    sendRPC('send_typing', { peer_id: state.activePeer }, false).catch(function () {});
  }

  function startPolling() {
    stopPolling();
    state.pollTimer = setInterval(function () {
      fetchContacts();
    }, 5000);
  }

  function stopPolling() {
    if (state.pollTimer) {
      clearInterval(state.pollTimer);
      state.pollTimer = null;
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // Rendering
  // ═══════════════════════════════════════════════════════════════
  function escapeHTML(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function formatTime(ts) {
    var d = new Date(ts * 1000);
    var h = d.getHours();
    var m = d.getMinutes();
    return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m;
  }

  function getInitials(name) {
    if (!name) return '?';
    var parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }

  function renderContactList() {
    var search = (dom.contactSearch.value || '').toLowerCase();
    var filtered = state.contacts;
    if (search) {
      filtered = state.contacts.filter(function (c) {
        return (c.device_name || '').toLowerCase().indexOf(search) !== -1;
      });
    }

    // Sort: online first, then by last_time descending
    filtered.sort(function (a, b) {
      if (a.online && !b.online) return -1;
      if (!a.online && b.online) return 1;
      return (b.last_time || 0) - (a.last_time || 0);
    });

    var html = '';
    for (var i = 0; i < filtered.length; i++) {
      var c = filtered[i];
      var activeClass = state.activePeer === c.device_id ? ' active' : '';
      var onlineClass = c.online ? ' online' : '';
      var initials = getInitials(c.device_name);
      var preview = escapeHTML(c.last_message || '');
      var time = c.last_time ? formatTime(c.last_time) : '';
      var unread = c.unread_count > 0 ? '<span class="contact-unread">' + (c.unread_count > 99 ? '99+' : c.unread_count) + '</span>' : '';

      html +=
        '<div class="contact-item' + activeClass + onlineClass + '" data-peer-id="' + escapeHTML(c.device_id) + '">' +
          '<div class="contact-avatar">' +
            '<span style="position:relative;z-index:1">' + escapeHTML(initials) + '</span>' +
            '<div class="contact-online-dot"></div>' +
          '</div>' +
          '<div class="contact-info">' +
            '<div class="contact-name">' + escapeHTML(c.device_name || 'Unknown') + '</div>' +
            '<div class="contact-preview">' + preview + '</div>' +
          '</div>' +
          '<div class="contact-meta">' +
            '<span class="contact-time">' + time + '</span>' +
            unread +
          '</div>' +
        '</div>';
    }

    dom.contactList.innerHTML = html;

    // Attach click handlers
    var items = dom.contactList.querySelectorAll('.contact-item');
    for (var j = 0; j < items.length; j++) {
      items[j].addEventListener('click', function () {
        var peerId = this.getAttribute('data-peer-id');
        selectContact(peerId);
      });
    }
  }

  function renderMessages(peerId) {
    var msgs = state.messages[peerId] || [];

    if (msgs.length === 0) {
      dom.messagesContainer.classList.add('hidden');
      dom.noMessages.classList.remove('hidden');
      return;
    }

    dom.messagesContainer.classList.remove('hidden');
    dom.noMessages.classList.add('hidden');

    var html = '';
    // Add a spacer div at top to maintain scroll position
    html += '<div class="messages-spacer" style="flex:1;min-height:0"></div>';

    for (var i = 0; i < msgs.length; i++) {
      var m = msgs[i];
      var isSent = m.direction === 'sent';
      var text = escapeHTML(m.body || '');

      // Checkmarks
      var checks = '';
      if (isSent) {
        if (m.read) {
          checks = '<span class="message-checkmarks read"><span class="ck">&#10003;</span><span class="ck">&#10003;</span></span>';
        } else if (m.delivered) {
          checks = '<span class="message-checkmarks"><span class="ck">&#10003;</span><span class="ck">&#10003;</span></span>';
        } else {
          checks = '<span class="message-checkmarks"><span class="ck">&#10003;</span></span>';
        }
      }

      html +=
        '<div class="message-row ' + (isSent ? 'sent' : 'received') + '">' +
          '<div>' +
            '<div class="message-bubble">' + text + '</div>' +
            '<div class="message-meta">' +
              '<span>' + formatTime(m.timestamp) + '</span>' +
              checks +
            '</div>' +
          '</div>' +
        '</div>';
    }

    dom.messagesContainer.innerHTML = html;
    scrollToBottom('smooth');
  }

  function scrollToBottom(behavior) {
    if (!dom.messagesContainer) return;

    // Wait a frame for DOM to settle
    requestAnimationFrame(function () {
      // Need to scroll the spacer to push content up
      var spacer = dom.messagesContainer.querySelector('.messages-spacer');
      if (!spacer) {
        dom.messagesContainer.scrollTop = dom.messagesContainer.scrollHeight;
      }
      dom.messagesContainer.scrollTop = dom.messagesContainer.scrollHeight;
    });
  }

  function updateContactOnlineStatus(peerId, online) {
    var contact = state.contacts.find(function (c) { return c.device_id === peerId; });
    if (contact) {
      contact.online = online;
    }
    renderContactList();
  }

  function updateConnectionUI(connected) {
    dom.connectionDot.classList.toggle('connected', connected);
    dom.connectionDot.classList.toggle('reconnecting', !connected && state.reconnectAttempt > 0);
    dom.connectionDot.title = connected ? 'Connected' : (state.reconnectAttempt > 0 ? 'Reconnecting...' : 'Disconnected');

    if (connected) {
      dom.connectionOverlay.classList.remove('visible', 'reconnecting');
    } else {
      dom.connectionOverlay.classList.add('visible');
      if (state.reconnectAttempt > 0) {
        dom.connectionOverlay.classList.add('reconnecting');
        dom.connectionOverlay.textContent = 'Reconnecting' + ' .'.repeat(Math.min(state.reconnectAttempt, 5)) + '...';
      } else {
        dom.connectionOverlay.classList.remove('reconnecting');
        dom.connectionOverlay.textContent = 'Connecting...';
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // Contact Selection
  // ═══════════════════════════════════════════════════════════════
  function selectContact(peerId) {
    state.activePeer = peerId;

    var contact = state.contacts.find(function (c) { return c.device_id === peerId; });
    var name = contact ? contact.device_name : 'Unknown';

    // Update header
    dom.chatAvatar.textContent = getInitials(name);
    dom.chatName.textContent = name;
    dom.chatStatus.textContent = contact && contact.online ? 'Online' : 'Offline';
    dom.chatStatus.className = contact && contact.online ? 'chat-header-status online' : 'chat-header-status';

    // Show chat, hide empty
    dom.chatEmpty.classList.add('hidden');
    dom.chatHeader.classList.remove('hidden');
    dom.inputArea.classList.remove('hidden');

    // Load history
    loadHistory(peerId);

    // Update contact list active state
    renderContactList();

    // On mobile, hide sidebar
    if (window.innerWidth < 768) {
      dom.sidebar.classList.add('hidden');
    }

    // Focus input
    setTimeout(function () {
      dom.messageInput.focus();
    }, 100);
  }

  function deselectContact() {
    state.activePeer = null;
    dom.chatHeader.classList.add('hidden');
    dom.messagesContainer.classList.add('hidden');
    dom.noMessages.classList.add('hidden');
    dom.inputArea.classList.add('hidden');
    dom.typingIndicator.classList.remove('visible');
    dom.chatEmpty.classList.remove('hidden');
    renderContactList();

    // On mobile, show sidebar
    if (window.innerWidth < 768) {
      dom.sidebar.classList.remove('hidden');
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // Sound
  // ═══════════════════════════════════════════════════════════════
  function playMessageSound() {
    try {
      // Use Web Audio API for a simple ping
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.setValueAtTime(1100, ctx.currentTime + 0.08);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.3);
      setTimeout(function () { ctx.close(); }, 400);
    } catch (e) {
      // Audio not available
    }
  }

  function toggleSound() {
    state.soundEnabled = !state.soundEnabled;
    dom.soundToggle.innerHTML = state.soundEnabled ? '&#128266;' : '&#128264;';
    dom.soundToggle.title = state.soundEnabled ? 'Sound on' : 'Sound off';
  }

  // ═══════════════════════════════════════════════════════════════
  // Event Listeners
  // ═══════════════════════════════════════════════════════════════
  dom.contactSearch.addEventListener('input', function () {
    renderContactList();
  });

  dom.backBtn.addEventListener('click', function () {
    deselectContact();
  });

  dom.sendBtn.addEventListener('click', function () {
    var body = dom.messageInput.value;
    if (!body.trim() || !state.activePeer) return;
    sendMessage(body);
    dom.messageInput.value = '';
    dom.messageInput.style.height = 'auto';
    updateSendButton();
    state.typingSentAt = 0; // reset debounce
  });

  dom.messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      var body = dom.messageInput.value;
      if (!body.trim() || !state.activePeer) return;
      sendMessage(body);
      dom.messageInput.value = '';
      dom.messageInput.style.height = 'auto';
      updateSendButton();
      state.typingSentAt = 0; // reset debounce
    }
  });

  dom.messageInput.addEventListener('input', function () {
    updateSendButton();
    // Auto-resize textarea
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    // Send typing indicator
    if (this.value.trim() && state.activePeer) {
      sendTypingIndicator();
    }
  });

  function updateSendButton() {
    var hasText = dom.messageInput.value.trim().length > 0;
    dom.sendBtn.disabled = !hasText;
  }

  dom.soundToggle.addEventListener('click', toggleSound);

  // Auto-scroll on resize
  window.addEventListener('resize', function () {
    if (state.activePeer) {
      scrollToBottom('auto');
    }
  });

  // Handle visibility change — reconnect when tab becomes visible
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && !state.connected) {
      state.reconnectDelay = 1000;
      state.reconnectAttempt = 0;
      connectWebSocket();
    }
  });

  // ═══════════════════════════════════════════════════════════════
  // Bootstrap
  // ═══════════════════════════════════════════════════════════════
  connectWebSocket();

})();
</script>
</body>
</html>"""
