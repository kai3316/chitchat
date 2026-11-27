# ChitChat Web UI — embedded SPA served by the daemon
WEB_UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>ChitChat</title>
<link rel="manifest" href="/manifest.json">
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
  gap: 8px;
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

.contact-avatar.group-avatar {
  background: linear-gradient(135deg, #4a90d9, #357abd);
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

/* ═══════════════════════════════════════════════════════════════
   Phase 3: Rich Media
   ═══════════════════════════════════════════════════════════════ */

/* Image message */
.msg-image {
  max-width: 250px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: block;
  transition: opacity 0.15s ease;
}
.msg-image:hover {
  opacity: 0.9;
}

/* Lightbox */
.lightbox {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.92);
  z-index: 1000;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.lightbox.open {
  display: flex;
}
.lightbox img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}
.lightbox-close {
  position: absolute;
  top: 20px;
  right: 24px;
  color: #fff;
  font-size: 36px;
  cursor: pointer;
  background: none;
  border: none;
  z-index: 1001;
  line-height: 1;
}

/* File card */
.file-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255,255,255,0.06);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  margin-top: 4px;
}
.file-card-icon {
  font-size: 28px;
  flex-shrink: 0;
}
.file-card-info {
  flex: 1;
  min-width: 0;
}
.file-card-name {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-card-btn {
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent-light);
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background var(--transition);
}
.file-card-btn:hover {
  background: rgba(103,80,164,0.2);
}

/* Link preview card */
.link-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  margin-top: 6px;
  background: rgba(0,0,0,0.15);
  cursor: pointer;
  transition: border-color var(--transition);
}
.link-card:hover {
  border-color: var(--accent-light);
}
.link-card-domain {
  font-size: 11px;
  color: var(--text-muted);
}
.link-card-title {
  font-size: 13px;
  font-weight: 600;
  margin-top: 2px;
}
.link-card-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Voice message */
.voice-msg {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 180px;
}
.voice-play-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background var(--transition);
}
.voice-play-btn:hover {
  background: var(--accent-light);
}
.voice-play-btn.playing {
  background: var(--danger);
}
.voice-wave {
  flex: 1;
  height: 24px;
  display: flex;
  align-items: flex-end;
  gap: 2px;
}
.voice-wave-bar {
  flex: 1;
  background: var(--accent-light);
  border-radius: 2px;
  min-height: 3px;
  transition: opacity 0.15s;
}
.voice-duration {
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
  min-width: 32px;
  text-align: right;
}

/* ═══════════════════════════════════════════════════════════════
   Phase 5: Group Chat
   ═══════════════════════════════════════════════════════════════ */

/* Sidebar add button */
.sidebar-add-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background var(--transition);
  line-height: 1;
}
.sidebar-add-btn:hover {
  background: var(--accent-light);
}

/* Sender name in group */
.msg-sender {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-light);
  margin-bottom: 3px;
}

/* Mention popup */
.mention-popup {
  display: none;
  position: absolute;
  bottom: 100%;
  left: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  max-height: 200px;
  overflow-y: auto;
  z-index: 50;
  min-width: 180px;
  box-shadow: var(--shadow-md);
}
.mention-popup.open {
  display: block;
}
.mention-item {
  padding: 8px 14px;
  cursor: pointer;
  font-size: 13px;
  transition: background var(--transition);
}
.mention-item:hover,
.mention-item.active {
  background: rgba(103,80,164,0.2);
}

/* Mention highlight in messages */
.mention-highlight {
  color: #7cb8ff;
  background: rgba(103,80,164,0.2);
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 500;
}

/* Reply quote in message bubble */
.reply-quote {
  border-left: 3px solid var(--accent);
  padding: 4px 10px;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(103,80,164,0.08);
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.reply-quote-sender {
  font-weight: 600;
  color: var(--accent-light);
}

/* Reply bar above input */
.reply-bar {
  display: none;
  padding: 8px 14px;
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border);
  font-size: 12px;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.reply-bar.active {
  display: flex;
}
.reply-bar-text {
  flex: 1;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.reply-bar-close {
  cursor: pointer;
  color: var(--text-muted);
  background: none;
  border: none;
  font-size: 18px;
  padding: 0 2px;
  line-height: 1;
}

/* Reply button on message */
.msg-reply-btn {
  display: none;
  position: absolute;
  right: 6px;
  top: 6px;
  background: var(--bg-tertiary);
  border: none;
  color: var(--text-muted);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  padding: 2px 8px;
  line-height: 1.4;
  z-index: 2;
  transition: background var(--transition);
}
.msg-reply-btn:hover {
  background: var(--border);
}
.message-bubble:hover .msg-reply-btn {
  display: block;
}

/* Message action button (for reactions) */
.msg-actions-btn {
  display: none;
  position: absolute;
  right: 6px;
  top: 30px;
  background: var(--bg-tertiary);
  border: none;
  color: var(--text-muted);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  padding: 2px 8px;
  line-height: 1.4;
  z-index: 2;
  transition: background var(--transition);
}
.msg-actions-btn:hover {
  background: var(--border);
}
.message-bubble:hover .msg-actions-btn {
  display: block;
}

/* Emoji picker */
.emoji-picker {
  display: none;
  position: fixed;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px;
  z-index: 200;
  box-shadow: var(--shadow-md);
}
.emoji-picker.open {
  display: flex;
  gap: 6px;
}
.emoji-picker-btn {
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: background var(--transition);
  line-height: 1;
}
.emoji-picker-btn:hover {
  background: rgba(103,80,164,0.25);
}

/* Reaction chips */
.reaction-chips {
  display: flex;
  gap: 4px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.reaction-chip {
  font-size: 12px;
  padding: 2px 7px;
  border-radius: 10px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: background var(--transition), border-color var(--transition);
}
.reaction-chip:hover {
  border-color: var(--accent-light);
}
.reaction-chip.active {
  border-color: var(--accent);
  background: rgba(103,80,164,0.25);
}

/* ═══════════════════════════════════════════════════════════════
   Phase 6: Polish
   ═══════════════════════════════════════════════════════════════ */

/* Modal */
.modal-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  z-index: 250;
  align-items: center;
  justify-content: center;
}
.modal-overlay.open {
  display: flex;
}
.modal {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 24px;
  min-width: 320px;
  max-width: 480px;
  width: 90%;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.2s ease;
}
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
.modal h3 {
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 600;
}
.modal-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  margin-bottom: 14px;
}
.modal-input:focus {
  border-color: var(--accent);
}
.modal-checkboxes {
  max-height: 220px;
  overflow-y: auto;
  margin-bottom: 16px;
}
.modal-checkboxes::-webkit-scrollbar {
  width: 4px;
}
.modal-checkboxes::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}
.modal-check-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 4px;
  font-size: 14px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background var(--transition);
}
.modal-check-item:hover {
  background: var(--bg-tertiary);
}
.modal-check-item input {
  accent-color: var(--accent);
  width: 16px;
  height: 16px;
}
.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.btn {
  padding: 8px 22px;
  border-radius: var(--radius-sm);
  border: none;
  font-size: 14px;
  cursor: pointer;
  font-weight: 500;
  transition: background var(--transition);
}
.btn-primary {
  background: var(--accent);
  color: #fff;
}
.btn-primary:hover {
  background: var(--accent-light);
}
.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border);
}
.btn-secondary:hover {
  background: var(--border);
}

/* Keyboard shortcuts panel */
.shortcuts-panel {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  z-index: 300;
  align-items: center;
  justify-content: center;
}
.shortcuts-panel.open {
  display: flex;
}
.shortcuts-content {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 24px;
  max-width: 420px;
  width: 90%;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.2s ease;
}
.shortcuts-content h3 {
  margin-bottom: 16px;
  font-size: 18px;
}
.shortcuts-list {
  list-style: none;
}
.shortcuts-list li {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
  border-bottom: 1px solid rgba(56,56,80,0.3);
}
.shortcuts-list li:last-child {
  border-bottom: none;
}
.shortcuts-list kbd {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  font-family: inherit;
  color: var(--text-primary);
}

/* Command palette */
.command-palette {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 280;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
}
.command-palette.open {
  display: flex;
}
.command-palette-box {
  background: var(--bg-secondary);
  border-radius: 12px;
  width: 90%;
  max-width: 480px;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  animation: modalIn 0.15s ease;
}
.command-palette-input {
  width: 100%;
  padding: 14px 18px;
  border: none;
  border-bottom: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 16px;
  outline: none;
}
.command-palette-input::placeholder {
  color: var(--text-muted);
}
.command-palette-results {
  max-height: 320px;
  overflow-y: auto;
}
.command-palette-results::-webkit-scrollbar {
  width: 4px;
}
.command-palette-results::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}
.command-palette-item {
  padding: 10px 18px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background var(--transition);
}
.command-palette-item:hover,
.command-palette-item.active {
  background: rgba(103,80,164,0.2);
}
.command-palette-item-icon {
  font-size: 20px;
  flex-shrink: 0;
}
.command-palette-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}

/* Toast */
.toast {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  padding: 10px 20px;
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  z-index: 500;
  transform: translateY(-100%);
  transition: transform 0.3s ease;
}
.toast.show {
  transform: translateY(0);
}
.toast.error {
  background: rgba(239,83,80,0.95);
  color: #fff;
}
.toast.info {
  background: rgba(103,80,164,0.95);
  color: #fff;
}
.toast.success {
  background: rgba(76,175,80,0.95);
  color: #fff;
}
</style>
</head>
<body>

<div class="app" id="app">
  <!-- Toast notification -->
  <div class="toast" id="toast"></div>

  <!-- Connection overlay -->
  <div class="connection-overlay" id="connectionOverlay">Connecting...</div>

  <!-- Sidebar -->
  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <h1>ChitChat</h1>
      <button class="sidebar-add-btn" id="sidebarAddBtn" title="Create group">+</button>
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

    <!-- Reply bar -->
    <div class="reply-bar" id="replyBar">
      <span style="font-size:16px;">&#8617;</span>
      <span class="reply-bar-text" id="replyBarText"></span>
      <button class="reply-bar-close" id="replyBarClose">&times;</button>
    </div>

    <!-- Mention popup -->
    <div class="mention-popup" id="mentionPopup"></div>

    <div class="input-area hidden" id="inputArea">
      <textarea id="messageInput" placeholder="Type a message..." rows="1"></textarea>
      <button class="send-btn" id="sendBtn" title="Send message" disabled>&#8593;</button>
    </div>
  </div>

  <!-- Emoji picker (positioned by JS) -->
  <div class="emoji-picker" id="emojiPicker">
    <button class="emoji-picker-btn" data-emoji="&#128077;">&#128077;</button>
    <button class="emoji-picker-btn" data-emoji="&#10084;&#65039;">&#10084;&#65039;</button>
    <button class="emoji-picker-btn" data-emoji="&#128514;">&#128514;</button>
    <button class="emoji-picker-btn" data-emoji="&#128558;">&#128558;</button>
    <button class="emoji-picker-btn" data-emoji="&#128546;">&#128546;</button>
    <button class="emoji-picker-btn" data-emoji="&#128545;">&#128545;</button>
  </div>

  <!-- Lightbox -->
  <div class="lightbox" id="lightbox">
    <button class="lightbox-close" id="lightboxClose">&times;</button>
    <img id="lightboxImg" src="" alt="Image preview">
  </div>

  <!-- Group Create Modal -->
  <div class="modal-overlay" id="groupModal">
    <div class="modal">
      <h3>Create Group</h3>
      <input class="modal-input" id="groupNameInput" placeholder="Group name...">
      <div class="modal-checkboxes" id="groupMemberCheckboxes"></div>
      <div class="modal-actions">
        <button class="btn btn-secondary" id="groupModalCancel">Cancel</button>
        <button class="btn btn-primary" id="groupModalCreate">Create Group</button>
      </div>
    </div>
  </div>

  <!-- Keyboard shortcuts panel -->
  <div class="shortcuts-panel" id="shortcutsPanel">
    <div class="shortcuts-content">
      <h3>Keyboard Shortcuts</h3>
      <ul class="shortcuts-list">
        <li><span>New chat / Create group</span><kbd>Ctrl+N</kbd></li>
        <li><span>Command palette</span><kbd>Ctrl+K</kbd></li>
        <li><span>Send message</span><kbd>Ctrl+Enter</kbd></li>
        <li><span>Close modals / panels</span><kbd>Esc</kbd></li>
        <li><span>Toggle shortcuts help</span><kbd>?</kbd></li>
      </ul>
    </div>
  </div>

  <!-- Command palette -->
  <div class="command-palette" id="commandPalette">
    <div class="command-palette-box">
      <input class="command-palette-input" id="commandPaletteInput" placeholder="Search contacts and groups..." autocomplete="off">
      <div class="command-palette-results" id="commandPaletteResults"></div>
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
    replyTo: null,          // { msg_id, body, sender_name } or null
    notificationPermission: false,
    voiceAudioCtx: null,    // AudioContext for voice playback
    voiceSource: null,      // Current voice source node
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
    // Phase 3: Rich Media
    lightbox:         $('#lightbox'),
    lightboxImg:      $('#lightboxImg'),
    lightboxClose:    $('#lightboxClose'),
    // Phase 5: Group Chat
    sidebarAddBtn:    $('#sidebarAddBtn'),
    groupModal:       $('#groupModal'),
    groupNameInput:   $('#groupNameInput'),
    groupMemberChecks:$('#groupMemberCheckboxes'),
    groupModalCancel: $('#groupModalCancel'),
    groupModalCreate: $('#groupModalCreate'),
    mentionPopup:     $('#mentionPopup'),
    emojiPicker:      $('#emojiPicker'),
    replyBar:         $('#replyBar'),
    replyBarText:     $('#replyBarText'),
    replyBarClose:    $('#replyBarClose'),
    // Phase 6: Polish
    shortcutsPanel:   $('#shortcutsPanel'),
    commandPalette:   $('#commandPalette'),
    commandPaletteInput: $('#commandPaletteInput'),
    commandPaletteResults: $('#commandPaletteResults'),
    toast:            $('#toast'),
  };

  // ═══════════════════════════════════════════════════════════════
  // Helpers
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

  function getContactByPeerId(peerId) {
    for (var i = 0; i < state.contacts.length; i++) {
      if (state.contacts[i].device_id === peerId || state.contacts[i].group_id === peerId) {
        return state.contacts[i];
      }
    }
    return null;
  }

  function isActiveGroup() {
    if (!state.activePeer) return false;
    var c = getContactByPeerId(state.activePeer);
    return c && c.is_group;
  }

  function getFileEmoji(fileName) {
    var ext = (fileName || '').split('.').pop().toLowerCase();
    var imageExts = ['png','jpg','jpeg','gif','svg','webp','bmp'];
    var audioExts = ['mp3','wav','ogg','flac','aac','m4a'];
    var videoExts = ['mp4','webm','mov','avi','mkv'];
    if (imageExts.indexOf(ext) !== -1) return '🖼️';
    if (audioExts.indexOf(ext) !== -1) return '🎵';
    if (videoExts.indexOf(ext) !== -1) return '🎬';
    return '📄';
  }

  function detectURLs(text) {
    var urlRe = /https?:\/\/[^\s<>"{}|\\^`\[\]]+/gi;
    var matches = text.match(urlRe);
    return matches ? matches[0] : null;
  }

  function parseLinkBody(text) {
    // Returns { textWithoutURL, url } or { textWithoutURL: text, url: null }
    var url = detectURLs(text);
    if (!url) return { textWithoutURL: text, url: null };
    var cleaned = text.replace(url, '').trim();
    return { textWithoutURL: cleaned || text, url: url };
  }

  function highlightMentions(text) {
    // Replace @name with highlighted spans
    return text.replace(/@(\w+)/g, '<span class="mention-highlight">@$1</span>');
  }

  function getGroupMembers(contact) {
    if (!contact || !contact.is_group) return [];
    return contact.member_ids || [];
  }

  function getGroupMemberNames(contact) {
    if (!contact || !contact.is_group) return [];
    return contact.member_names || [];
  }

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

    const wsUrl = 'ws://' + location.hostname + ':' +
                  ((window.CHITCHAT_CONFIG && window.CHITCHAT_CONFIG.wsPort) || 9876);
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
      case 'reaction_added':
        handleReactionAdded(payload);
        break;
      case 'reaction_removed':
        handleReactionRemoved(payload);
        break;
      case 'group_created':
        handleGroupCreated(payload);
        break;
      case 'group_message_received':
        handleMessageReceived(payload);
        break;
      case 'contact_updated':
        fetchContacts();
        break;
      case 'security_alert':
        handleSecurityAlert(payload);
        break;
    }
  }

  // A peer's certificate changed, which is what a man-in-the-middle looks
  // like. Never swallow this one silently.
  function handleSecurityAlert(payload) {
    var name = payload.peer_name || 'A peer';
    showToast('Security warning: the certificate for ' + name +
              ' changed. Verify the device before trusting it.', 'error');
    if (window.console && console.warn) {
      console.warn('ChitChat security alert', payload);
    }
  }

  function handleMessageReceived(msg) {
    var peerId = msg.peer_id || msg.group_id;
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

    // Browser notification if tab hidden
    if (document.hidden && state.notificationPermission) {
      var contact = getContactByPeerId(peerId);
      var title = contact ? contact.device_name || contact.name : 'New message';
      var body = msg.body || '';
      if (typeof body === 'string' && body.length > 80) body = body.substring(0, 80) + '...';
      showBrowserNotification(title, body);
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
    var contact = getContactByPeerId(peerId);
    var name = contact ? (contact.device_name || contact.name) : 'Someone';
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

  function handleReactionAdded(payload) {
    var peerId = payload.peer_id || payload.group_id;
    var msgs = state.messages[peerId];
    if (!msgs) return;
    for (var i = 0; i < msgs.length; i++) {
      if (msgs[i].msg_id === payload.msg_id) {
        if (!msgs[i].reactions) msgs[i].reactions = [];
        // Avoid duplicate
        var dup = msgs[i].reactions.some(function (r) { return r.emoji === payload.emoji && r.peer_id === payload.sender_id; });
        if (!dup) {
          msgs[i].reactions.push({ emoji: payload.emoji, peer_id: payload.sender_id });
        }
        if (state.activePeer === peerId) {
          renderMessages(peerId);
        }
        break;
      }
    }
  }

  function handleReactionRemoved(payload) {
    var peerId = payload.peer_id || payload.group_id;
    var msgs = state.messages[peerId];
    if (!msgs) return;
    for (var i = 0; i < msgs.length; i++) {
      if (msgs[i].msg_id === payload.msg_id && msgs[i].reactions) {
        msgs[i].reactions = msgs[i].reactions.filter(function (r) {
          return !(r.emoji === payload.emoji && r.peer_id === payload.sender_id);
        });
        if (state.activePeer === peerId) {
          renderMessages(peerId);
        }
        break;
      }
    }
  }

  function handleGroupCreated(payload) {
    // Refresh contacts to show new group
    fetchContacts();
    showToast('Group "' + (payload.name || '') + '" created', 'success');
    // Select the new group
    if (payload.group_id) {
      setTimeout(function () {
        selectContact(payload.group_id);
      }, 500);
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
    var contact = getContactByPeerId(peerId);
    var params = { limit: 50 };
    if (contact && contact.is_group) {
      params.group_id = peerId;
    } else {
      params.peer_id = peerId;
    }
    sendRPC('get_history', params).then(function (result) {
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
    var contact = getContactByPeerId(peerId);
    var isGroup = contact && contact.is_group;

    var params = {
      type: 'chat_text',
      body: body.trim()
    };

    if (isGroup) {
      params.group_id = peerId;
    } else {
      params.peer_id = peerId;
    }

    // Include reply_to if replying
    if (state.replyTo) {
      params.reply_to = state.replyTo.msg_id;
    }

    var method = isGroup ? 'send_group_message' : 'send_message';

    sendRPC(method, params).then(function (result) {
      // Add locally if not already added from event
      if (!state.messages[peerId]) {
        state.messages[peerId] = [];
      }
      var exists = state.messages[peerId].some(function (m) { return m.msg_id === result.msg_id; });
      if (!exists) {
        var newMsg = {
          msg_id: result.msg_id,
          peer_id: peerId,
          direction: 'sent',
          msg_type: 'chat_text',
          body: body.trim(),
          timestamp: result.timestamp,
          delivered: result.sent,
          read: false
        };
        if (state.replyTo) {
          newMsg.reply_to = state.replyTo.msg_id;
          newMsg.reply_body = state.replyTo.body;
          newMsg.reply_sender = state.replyTo.sender_name;
        }
        state.messages[peerId].push(newMsg);
      }
      // Clear reply
      cancelReply();
      renderMessages(peerId);
      fetchContacts();
    }).catch(function (err) {
      console.error('Failed to send:', err);
      showToast('Failed to send message', 'error');
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
  function renderContactList() {
    var search = (dom.contactSearch.value || '').toLowerCase();
    var filtered = state.contacts;
    if (search) {
      filtered = state.contacts.filter(function (c) {
        var name = c.device_name || c.name || '';
        return name.toLowerCase().indexOf(search) !== -1;
      });
    }

    // Sort: online first, then by last_time descending (groups interspersed)
    filtered.sort(function (a, b) {
      if (a.online && !b.online) return -1;
      if (!a.online && b.online) return 1;
      return (b.last_time || 0) - (a.last_time || 0);
    });

    var html = '';
    for (var i = 0; i < filtered.length; i++) {
      var c = filtered[i];
      var peerId = c.device_id || c.group_id;
      var activeClass = state.activePeer === peerId ? ' active' : '';
      var onlineClass = c.online && !c.is_group ? ' online' : '';
      var isGroup = c.is_group;
      var avatarClass = isGroup ? ' group-avatar' : '';
      var initials = isGroup ? '👥' : getInitials(c.device_name || c.name);
      var displayName = c.device_name || c.name || 'Unknown';
      var preview = escapeHTML(c.last_message || '');
      var time = c.last_time ? formatTime(c.last_time) : '';
      var unread = c.unread_count > 0 ? '<span class="contact-unread">' + (c.unread_count > 99 ? '99+' : c.unread_count) + '</span>' : '';

      html +=
        '<div class="contact-item' + activeClass + onlineClass + '" data-peer-id="' + escapeHTML(peerId) + '">' +
          '<div class="contact-avatar' + avatarClass + '">' +
            '<span style="position:relative;z-index:1">' + initials + '</span>' +
            '<div class="contact-online-dot"></div>' +
          '</div>' +
          '<div class="contact-info">' +
            '<div class="contact-name">' + escapeHTML(displayName) + '</div>' +
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

  function renderReplyQuote(msg) {
    if (!msg.reply_to && !msg.reply_body) return '';
    var body = msg.reply_body || '';
    var sender = msg.reply_sender || '';
    // Truncate body
    if (body.length > 100) body = body.substring(0, 100) + '...';
    var senderHTML = sender ? '<span class="reply-quote-sender">' + escapeHTML(sender) + '</span> ' : '';
    return '<div class="reply-quote">' + senderHTML + escapeHTML(body) + '</div>';
  }

  function renderReactions(reactions) {
    if (!reactions || reactions.length === 0) return '';
    // Group by emoji
    var counts = {};
    for (var i = 0; i < reactions.length; i++) {
      var e = reactions[i].emoji;
      counts[e] = (counts[e] || 0) + 1;
    }
    var html = '<div class="reaction-chips">';
    var emojis = Object.keys(counts);
    for (var j = 0; j < emojis.length; j++) {
      html += '<span class="reaction-chip">' + emojis[j] + ' ' + counts[emojis[j]] + '</span>';
    }
    html += '</div>';
    return html;
  }

  function renderMessageBubbleContent(m, isSent) {
    var msgType = m.msg_type || 'chat_text';
    var body = m.body || '';
    var html = '';

    // Handle reply quote
    html += renderReplyQuote(m);

    switch (msgType) {
      case 'chat_image':
        try {
          var imgData = typeof body === 'string' ? JSON.parse(body) : body;
          var src = 'data:image/png;base64,' + imgData.data;
          html += '<img class="msg-image" src="' + src + '" data-full-src="' + src + '" alt="' + escapeHTML(imgData.file_name || 'Image') + '" title="Click to enlarge">';
        } catch (e) {
          html += escapeHTML('[Image]');
        }
        break;

      case 'chat_file':
        try {
          var fileData = typeof body === 'string' ? JSON.parse(body) : body;
          var fileName = fileData.file_name || 'file';
          var emoji = getFileEmoji(fileName);
          html += '<div class="file-card">' +
            '<span class="file-card-icon">' + emoji + '</span>' +
            '<div class="file-card-info">' +
              '<div class="file-card-name">' + escapeHTML(fileName) + '</div>' +
            '</div>' +
            '<button class="file-card-btn" data-file-name="' + escapeHTML(fileName) + '" data-file-data="' + (fileData.data || '') + '">Download</button>' +
          '</div>';
        } catch (e) {
          html += '<div class="file-card">' +
            '<span class="file-card-icon">📄</span>' +
            '<div class="file-card-info"><div class="file-card-name">' + escapeHTML(typeof body === 'string' ? body : 'File') + '</div></div>' +
            '<button class="file-card-btn">Download</button>' +
          '</div>';
        }
        break;

      case 'chat_voice':
        try {
          var voiceData = typeof body === 'string' ? JSON.parse(body) : body;
          var duration = voiceData.duration || 0;
          var durText = Math.floor(duration / 60) + ':' + (Math.floor(duration % 60) < 10 ? '0' : '') + Math.floor(duration % 60);
          var bars = 15;
          var waveHTML = '<div class="voice-wave">';
          for (var w = 0; w < bars; w++) {
            var h = 3 + Math.random() * 21;
            waveHTML += '<div class="voice-wave-bar" style="height:' + h + 'px"></div>';
          }
          waveHTML += '</div>';
          html += '<div class="voice-msg">' +
            '<button class="voice-play-btn" data-voice-data="' + (voiceData.data || '') + '">▶️</button>' +
            waveHTML +
            '<span class="voice-duration">' + durText + '</span>' +
          '</div>';
        } catch (e) {
          html += escapeHTML('[Voice message]');
        }
        break;

      case 'chat_link':
        try {
          var linkData = typeof body === 'string' ? JSON.parse(body) : body;
          var linkUrl = linkData.url || '';
          var linkTitle = linkData.title || '';
          var linkDesc = linkData.description || '';
          var linkDomain = linkData.domain || '';
          if (!linkDomain && linkUrl) {
            try { linkDomain = new URL(linkUrl).hostname; } catch (e2) {}
          }
          html += '<div class="link-card" data-url="' + escapeHTML(linkUrl) + '">' +
            '<div class="link-card-domain">' + escapeHTML(linkDomain || linkUrl) + '</div>';
          if (linkTitle) {
            html += '<div class="link-card-title">' + escapeHTML(linkTitle) + '</div>';
          }
          if (linkDesc) {
            html += '<div class="link-card-desc">' + escapeHTML(linkDesc) + '</div>';
          }
          html += '</div>';
        } catch (e) {
          html += escapeHTML('[Link]');
        }
        break;

      default:
        // chat_text or unknown
        var parsed = parseLinkBody(typeof body === 'string' ? body : '');
        var textHTML = highlightMentions(escapeHTML(parsed.textWithoutURL));
        html += textHTML;

        // Link preview card
        if (parsed.url) {
          var linkPreview = m.link_preview;
          var domain = '';
          try {
            domain = new URL(parsed.url).hostname;
          } catch (e2) { domain = parsed.url; }
          html += '<div class="link-card" data-url="' + escapeHTML(parsed.url) + '">' +
            '<div class="link-card-domain">' + escapeHTML(domain) + '</div>';
          if (linkPreview && linkPreview.title) {
            html += '<div class="link-card-title">' + escapeHTML(linkPreview.title) + '</div>';
          }
          if (linkPreview && linkPreview.description) {
            html += '<div class="link-card-desc">' + escapeHTML(linkPreview.description) + '</div>';
          }
          html += '</div>';
        }
        break;
    }

    return html;
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

    var isGroup = isActiveGroup();
    var html = '';
    // Add a spacer div at top to maintain scroll position
    html += '<div class="messages-spacer" style="flex:1;min-height:0"></div>';

    for (var i = 0; i < msgs.length; i++) {
      var m = msgs[i];
      var isSent = m.direction === 'sent';

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

      // Sender name for received group messages
      var senderHTML = '';
      if (isGroup && !isSent && m.sender_name) {
        senderHTML = '<div class="msg-sender">' + escapeHTML(m.sender_name) + '</div>';
      }

      // Reactions
      var reactionsHTML = renderReactions(m.reactions);

      html +=
        '<div class="message-row ' + (isSent ? 'sent' : 'received') + '">' +
          '<div>' +
            '<div class="message-bubble" data-msg-id="' + escapeHTML(m.msg_id || '') + '">' +
              senderHTML +
              renderMessageBubbleContent(m, isSent) +
              '<button class="msg-reply-btn" data-msg-id="' + escapeHTML(m.msg_id || '') + '" title="Reply">&#8617;</button>' +
              '<button class="msg-actions-btn" data-msg-id="' + escapeHTML(m.msg_id || '') + '" title="React">...</button>' +
            '</div>' +
            reactionsHTML +
            '<div class="message-meta">' +
              '<span>' + formatTime(m.timestamp) + '</span>' +
              checks +
            '</div>' +
          '</div>' +
        '</div>';
    }

    dom.messagesContainer.innerHTML = html;

    // Attach image click handlers
    var images = dom.messagesContainer.querySelectorAll('.msg-image');
    for (var imgI = 0; imgI < images.length; imgI++) {
      images[imgI].addEventListener('click', function (e) {
        e.stopPropagation();
        openLightbox(this.getAttribute('data-full-src') || this.src);
      });
    }

    // Attach file download handlers
    var fileBtns = dom.messagesContainer.querySelectorAll('.file-card-btn');
    for (var fbI = 0; fbI < fileBtns.length; fbI++) {
      fileBtns[fbI].addEventListener('click', function (e) {
        e.stopPropagation();
        var fName = this.getAttribute('data-file-name') || 'file';
        var fData = this.getAttribute('data-file-data') || '';
        downloadFile(fData, fName);
      });
    }

    // Attach voice play handlers
    var voiceBtns = dom.messagesContainer.querySelectorAll('.voice-play-btn');
    for (var vbI = 0; vbI < voiceBtns.length; vbI++) {
      voiceBtns[vbI].addEventListener('click', function (e) {
        e.stopPropagation();
        playVoice(this);
      });
    }

    // Attach link card click handlers
    var linkCards = dom.messagesContainer.querySelectorAll('.link-card');
    for (var lcI = 0; lcI < linkCards.length; lcI++) {
      linkCards[lcI].addEventListener('click', function (e) {
        e.stopPropagation();
        var url = this.getAttribute('data-url');
        if (url) window.open(url, '_blank');
      });
    }

    // Attach reply button handlers
    var replyBtns = dom.messagesContainer.querySelectorAll('.msg-reply-btn');
    for (var rpI = 0; rpI < replyBtns.length; rpI++) {
      replyBtns[rpI].addEventListener('click', function (e) {
        e.stopPropagation();
        var msgId = this.getAttribute('data-msg-id');
        var msg = findMessage(msgId);
        if (msg) {
          var sender = msg.sender_name || (msg.direction === 'sent' ? 'You' : (getContactByPeerId(state.activePeer) ? (getContactByPeerId(state.activePeer).device_name || getContactByPeerId(state.activePeer).name) : ''));
          startReply(msgId, typeof msg.body === 'string' ? msg.body : '[Media]', sender);
        }
      });
    }

    // Attach actions button (reactions) handlers
    var actionsBtns = dom.messagesContainer.querySelectorAll('.msg-actions-btn');
    for (var abI = 0; abI < actionsBtns.length; abI++) {
      actionsBtns[abI].addEventListener('click', function (e) {
        e.stopPropagation();
        var msgId = this.getAttribute('data-msg-id');
        var peerId = state.activePeer;
        openEmojiPicker(msgId, peerId, e);
      });
    }

    scrollToBottom('smooth');
  }

  function scrollToBottom(behavior) {
    if (!dom.messagesContainer) return;

    // Wait a frame for DOM to settle
    requestAnimationFrame(function () {
      var spacer = dom.messagesContainer.querySelector('.messages-spacer');
      if (!spacer) {
        dom.messagesContainer.scrollTop = dom.messagesContainer.scrollHeight;
      }
      dom.messagesContainer.scrollTop = dom.messagesContainer.scrollHeight;
    });
  }

  function findMessage(msgId) {
    if (!state.activePeer) return null;
    var msgs = state.messages[state.activePeer] || [];
    for (var i = 0; i < msgs.length; i++) {
      if (msgs[i].msg_id === msgId) return msgs[i];
    }
    return null;
  }

  function updateContactOnlineStatus(peerId, online) {
    var contact = getContactByPeerId(peerId);
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
      if (state.reconnectAttempt > 0) {
        showToast('Connected', 'success');
      }
    } else {
      dom.connectionOverlay.classList.add('visible');
      if (state.reconnectAttempt > 0) {
        dom.connectionOverlay.classList.add('reconnecting');
        dom.connectionOverlay.textContent = 'Reconnecting' + ' .'.repeat(Math.min(state.reconnectAttempt, 5)) + '...';
        if (state.reconnectAttempt === 1) {
          showToast('Connection lost — reconnecting...', 'error');
        }
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

    var contact = getContactByPeerId(peerId);
    var name = contact ? (contact.device_name || contact.name || 'Unknown') : 'Unknown';

    // Update header
    var isGroup = contact && contact.is_group;
    dom.chatAvatar.textContent = isGroup ? '👥' : getInitials(name);
    if (isGroup) {
      dom.chatAvatar.classList.add('group-avatar');
    } else {
      dom.chatAvatar.classList.remove('group-avatar');
    }
    dom.chatName.textContent = name;
    if (isGroup) {
      var memberCount = (contact.member_ids || []).length;
      dom.chatStatus.textContent = memberCount + ' member' + (memberCount !== 1 ? 's' : '');
      dom.chatStatus.className = 'chat-header-status';
    } else {
      dom.chatStatus.textContent = contact && contact.online ? 'Online' : 'Offline';
      dom.chatStatus.className = contact && contact.online ? 'chat-header-status online' : 'chat-header-status';
    }

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
    cancelReply();
    closeEmojiPicker();
    renderContactList();

    // On mobile, show sidebar
    if (window.innerWidth < 768) {
      dom.sidebar.classList.remove('hidden');
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // Sound & Notifications
  // ═══════════════════════════════════════════════════════════════
  function playMessageSound() {
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var osc1 = ctx.createOscillator();
      var osc2 = ctx.createOscillator();
      var gain = ctx.createGain();
      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);
      osc1.type = 'sine';
      osc2.type = 'sine';
      osc1.frequency.setValueAtTime(1047, ctx.currentTime);
      osc2.frequency.setValueAtTime(1319, ctx.currentTime + 0.07);
      gain.gain.setValueAtTime(0.18, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
      osc1.start(ctx.currentTime);
      osc1.stop(ctx.currentTime + 0.15);
      osc2.start(ctx.currentTime + 0.07);
      osc2.stop(ctx.currentTime + 0.35);
      setTimeout(function () { ctx.close(); }, 500);
    } catch (e) {
      // Audio not available
    }
  }

  function toggleSound() {
    state.soundEnabled = !state.soundEnabled;
    dom.soundToggle.innerHTML = state.soundEnabled ? '&#128266;' : '&#128264;';
    dom.soundToggle.title = state.soundEnabled ? 'Sound on' : 'Sound off';
    if (state.soundEnabled && !state.notificationPermission && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(function (perm) {
        state.notificationPermission = perm === 'granted';
      });
    }
  }

  function showBrowserNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
      try {
        new Notification(title, { body: body, icon: '/favicon.ico' });
      } catch (e) {
        // Ignore notification errors
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // Phase 3: Rich Media Handlers
  // ═══════════════════════════════════════════════════════════════
  function openLightbox(src) {
    dom.lightboxImg.src = src;
    dom.lightbox.classList.add('open');
  }

  function closeLightbox() {
    dom.lightbox.classList.remove('open');
  }

  function downloadFile(base64Data, fileName) {
    try {
      var byteChars = atob(base64Data);
      var byteNums = new Array(byteChars.length);
      for (var i = 0; i < byteChars.length; i++) {
        byteNums[i] = byteChars.charCodeAt(i);
      }
      var byteArr = new Uint8Array(byteNums);
      var blob = new Blob([byteArr], { type: 'application/octet-stream' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      showToast('Download failed', 'error');
    }
  }

  function playVoice(btn) {
    var base64Data = btn.getAttribute('data-voice-data');
    if (!base64Data) return;

    // Toggle stop
    if (btn.classList.contains('playing')) {
      stopVoice();
      return;
    }

    // Stop any existing playback
    stopVoice();

    try {
      var byteChars = atob(base64Data);
      var byteNums = new Array(byteChars.length);
      for (var i = 0; i < byteChars.length; i++) {
        byteNums[i] = byteChars.charCodeAt(i);
      }
      var byteArr = new Uint8Array(byteNums);

      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      state.voiceAudioCtx = ctx;

      ctx.decodeAudioData(byteArr.buffer.slice(0), function (audioBuffer) {
        var source = ctx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(ctx.destination);
        source.onended = function () {
          btn.classList.remove('playing');
          btn.textContent = '▶️';
          state.voiceSource = null;
        };
        state.voiceSource = source;
        source.start(0);
        btn.classList.add('playing');
        btn.textContent = '⏹️';
      }, function () {
        showToast('Cannot play audio', 'error');
      });
    } catch (e) {
      showToast('Cannot play audio', 'error');
    }
  }

  function stopVoice() {
    if (state.voiceSource) {
      try { state.voiceSource.stop(); } catch (e) {}
      state.voiceSource = null;
    }
    // Reset all playing buttons
    var allBtns = document.querySelectorAll('.voice-play-btn.playing');
    for (var i = 0; i < allBtns.length; i++) {
      allBtns[i].classList.remove('playing');
      allBtns[i].textContent = '▶️';
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // Phase 5: Group Chat Handlers
  // ═══════════════════════════════════════════════════════════════
  function openGroupModal() {
    // Populate checkboxes with non-group contacts
    var html = '';
    for (var i = 0; i < state.contacts.length; i++) {
      var c = state.contacts[i];
      if (c.is_group) continue;
      var name = c.device_name || c.name || 'Unknown';
      html += '<label class="modal-check-item">' +
        '<input type="checkbox" value="' + escapeHTML(c.device_id) + '">' +
        '<span>' + escapeHTML(name) + '</span>' +
      '</label>';
    }
    if (!html) {
      html = '<div style="color:var(--text-muted);padding:12px 0;text-align:center;">No contacts available</div>';
    }
    dom.groupMemberChecks.innerHTML = html;
    dom.groupNameInput.value = '';
    dom.groupModal.classList.add('open');
    setTimeout(function () { dom.groupNameInput.focus(); }, 100);
  }

  function closeGroupModal() {
    dom.groupModal.classList.remove('open');
  }

  function createGroup() {
    var name = dom.groupNameInput.value.trim();
    if (!name) {
      showToast('Please enter a group name', 'error');
      return;
    }

    var checkboxes = dom.groupMemberChecks.querySelectorAll('input[type="checkbox"]:checked');
    var memberIds = [];
    for (var i = 0; i < checkboxes.length; i++) {
      memberIds.push(checkboxes[i].value);
    }
    if (memberIds.length === 0) {
      showToast('Please select at least one member', 'error');
      return;
    }

    sendRPC('create_group', { name: name, member_ids: memberIds }).then(function (result) {
      closeGroupModal();
      showToast('Group created', 'success');
      fetchContacts();
      if (result && result.group_id) {
        setTimeout(function () { selectContact(result.group_id); }, 300);
      }
    }).catch(function (err) {
      showToast('Failed to create group: ' + (err.message || 'Unknown error'), 'error');
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // Reply
  // ═══════════════════════════════════════════════════════════════
  function startReply(msgId, body, senderName) {
    state.replyTo = { msg_id: msgId, body: body, sender_name: senderName };
    var preview = body;
    if (preview.length > 80) preview = preview.substring(0, 80) + '...';
    dom.replyBarText.textContent = 'Replying to ' + escapeHTML(senderName || 'message') + ': ' + preview;
    dom.replyBar.classList.add('active');
    dom.messageInput.focus();
  }

  function cancelReply() {
    state.replyTo = null;
    dom.replyBar.classList.remove('active');
  }

  // ═══════════════════════════════════════════════════════════════
  // Emoji Picker & Reactions
  // ═══════════════════════════════════════════════════════════════
  function openEmojiPicker(msgId, peerId, event) {
    state.activeEmojiMsgId = msgId;
    state.activeEmojiPeerId = peerId;
    var picker = dom.emojiPicker;
    // Position near the click
    var rect = event.target.getBoundingClientRect();
    var top = rect.bottom + 4;
    var left = rect.left - 60;
    if (left < 8) left = 8;
    if (top + 50 > window.innerHeight) top = rect.top - 50;
    picker.style.top = top + 'px';
    picker.style.left = left + 'px';
    picker.classList.add('open');
  }

  function closeEmojiPicker() {
    dom.emojiPicker.classList.remove('open');
    state.activeEmojiMsgId = null;
    state.activeEmojiPeerId = null;
  }

  function sendReaction(emoji) {
    if (!state.activeEmojiMsgId || !state.activeEmojiPeerId) return;
    sendRPC('react', {
      msg_id: state.activeEmojiMsgId,
      peer_id: state.activeEmojiPeerId,
      emoji: emoji
    }, false).then(function () {
      // Optimistically add reaction locally
      var msgs = state.messages[state.activeEmojiPeerId];
      if (msgs) {
        for (var i = 0; i < msgs.length; i++) {
          if (msgs[i].msg_id === state.activeEmojiMsgId) {
            if (!msgs[i].reactions) msgs[i].reactions = [];
            msgs[i].reactions.push({ emoji: emoji, peer_id: 'me' });
            renderMessages(state.activeEmojiPeerId);
            break;
          }
        }
      }
    }).catch(function () {
      showToast('Failed to add reaction', 'error');
    });
    closeEmojiPicker();
  }

  // ═══════════════════════════════════════════════════════════════
  // @Mentions
  // ═══════════════════════════════════════════════════════════════
  function handleMentionInput() {
    if (!isActiveGroup()) {
      dom.mentionPopup.classList.remove('open');
      return;
    }

    var input = dom.messageInput;
    var text = input.value;
    var cursorPos = input.selectionStart;

    // Find @ before cursor
    var atIdx = -1;
    for (var i = cursorPos - 1; i >= 0; i--) {
      if (text[i] === '@') {
        // Check that @ is at start or preceded by space
        if (i === 0 || text[i - 1] === ' ' || text[i - 1] === '\n') {
          atIdx = i;
        }
        break;
      }
      if (text[i] === ' ') break;
    }

    if (atIdx === -1) {
      dom.mentionPopup.classList.remove('open');
      return;
    }

    var query = text.substring(atIdx + 1, cursorPos).toLowerCase();
    var contact = getContactByPeerId(state.activePeer);
    var memberNames = getGroupMemberNames(contact);

    if (memberNames.length === 0) {
      dom.mentionPopup.classList.remove('open');
      return;
    }

    var filtered = memberNames;
    if (query) {
      filtered = memberNames.filter(function (n) { return n.toLowerCase().indexOf(query) !== -1; });
    }

    if (filtered.length === 0) {
      dom.mentionPopup.classList.remove('open');
      return;
    }

    var html = '';
    for (var j = 0; j < filtered.length; j++) {
      html += '<div class="mention-item" data-name="' + escapeHTML(filtered[j]) + '">@' + escapeHTML(filtered[j]) + '</div>';
    }
    dom.mentionPopup.innerHTML = html;
    dom.mentionPopup.classList.add('open');

    // Attach click handlers
    var items = dom.mentionPopup.querySelectorAll('.mention-item');
    for (var k = 0; k < items.length; k++) {
      items[k].addEventListener('click', function () {
        var name = this.getAttribute('data-name');
        insertMention(atIdx, cursorPos, name);
      });
    }
  }

  function insertMention(atIdx, endIdx, name) {
    var input = dom.messageInput;
    var text = input.value;
    var before = text.substring(0, atIdx);
    var after = text.substring(endIdx);
    input.value = before + '@' + name + ' ' + after;
    dom.mentionPopup.classList.remove('open');
    input.focus();
    var newPos = atIdx + name.length + 2;
    input.setSelectionRange(newPos, newPos);
    updateSendButton();
  }

  // ═══════════════════════════════════════════════════════════════
  // Phase 6: Keyboard Shortcuts
  // ═══════════════════════════════════════════════════════════════
  function toggleShortcuts() {
    dom.shortcutsPanel.classList.toggle('open');
  }

  function openCommandPalette() {
    dom.commandPalette.classList.add('open');
    dom.commandPaletteInput.value = '';
    dom.commandPaletteResults.innerHTML = '';
    setTimeout(function () { dom.commandPaletteInput.focus(); }, 50);
    renderCommandPalette('');
  }

  function closeCommandPalette() {
    dom.commandPalette.classList.remove('open');
  }

  function renderCommandPalette(query) {
    var q = (query || '').toLowerCase();
    var results = [];

    for (var i = 0; i < state.contacts.length; i++) {
      var c = state.contacts[i];
      var name = c.device_name || c.name || '';
      if (q && name.toLowerCase().indexOf(q) === -1) continue;
      var peerId = c.device_id || c.group_id;
      var isGroup = c.is_group;
      results.push({
        id: peerId,
        name: name,
        isGroup: isGroup,
        icon: isGroup ? '👥' : '👤'
      });
    }

    if (results.length === 0) {
      dom.commandPaletteResults.innerHTML = '<div class="command-palette-empty">No results</div>';
      return;
    }

    var html = '';
    for (var j = 0; j < results.length; j++) {
      var r = results[j];
      html += '<div class="command-palette-item" data-peer-id="' + escapeHTML(r.id) + '">' +
        '<span class="command-palette-item-icon">' + r.icon + '</span>' +
        '<span>' + escapeHTML(r.name) + '</span>' +
      '</div>';
    }
    dom.commandPaletteResults.innerHTML = html;

    // Attach click handlers
    var items = dom.commandPaletteResults.querySelectorAll('.command-palette-item');
    for (var k = 0; k < items.length; k++) {
      items[k].addEventListener('click', function () {
        var pid = this.getAttribute('data-peer-id');
        closeCommandPalette();
        selectContact(pid);
      });
    }
  }

  function closeAllModals() {
    closeLightbox();
    closeGroupModal();
    closeEmojiPicker();
    cancelReply();
    dom.mentionPopup.classList.remove('open');
    dom.shortcutsPanel.classList.remove('open');
    closeCommandPalette();
  }

  // ═══════════════════════════════════════════════════════════════
  // Toast
  // ═══════════════════════════════════════════════════════════════
  let toastTimer = null;
  function showToast(message, type) {
    if (!dom.toast) return;
    dom.toast.textContent = message;
    dom.toast.className = 'toast ' + (type || 'info');
    dom.toast.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      dom.toast.classList.remove('show');
    }, 3000);
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
    // Ctrl+Enter / Cmd+Enter to send
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      var body = dom.messageInput.value;
      if (!body.trim() || !state.activePeer) return;
      sendMessage(body);
      dom.messageInput.value = '';
      dom.messageInput.style.height = 'auto';
      updateSendButton();
      state.typingSentAt = 0;
      return;
    }

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
    // Handle @mentions
    handleMentionInput();
  });

  function updateSendButton() {
    var hasText = dom.messageInput.value.trim().length > 0;
    dom.sendBtn.disabled = !hasText;
  }

  dom.soundToggle.addEventListener('click', toggleSound);

  // Lightbox close
  dom.lightbox.addEventListener('click', function (e) {
    if (e.target === dom.lightbox) {
      closeLightbox();
    }
  });
  dom.lightboxClose.addEventListener('click', closeLightbox);

  // Group modal
  dom.sidebarAddBtn.addEventListener('click', openGroupModal);
  dom.groupModalCancel.addEventListener('click', closeGroupModal);
  dom.groupModal.addEventListener('click', function (e) {
    if (e.target === dom.groupModal) closeGroupModal();
  });
  dom.groupModalCreate.addEventListener('click', createGroup);

  // Reply bar
  dom.replyBarClose.addEventListener('click', cancelReply);

  // Emoji picker buttons
  var emojiBtns = dom.emojiPicker.querySelectorAll('.emoji-picker-btn');
  for (var ebi = 0; ebi < emojiBtns.length; ebi++) {
    emojiBtns[ebi].addEventListener('click', function () {
      sendReaction(this.getAttribute('data-emoji'));
    });
  }

  // Command palette
  dom.commandPaletteInput.addEventListener('input', function () {
    renderCommandPalette(this.value);
  });
  dom.commandPalette.addEventListener('click', function (e) {
    if (e.target === dom.commandPalette) closeCommandPalette();
  });
  dom.commandPaletteInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      var first = dom.commandPaletteResults.querySelector('.command-palette-item');
      if (first) {
        var pid = first.getAttribute('data-peer-id');
        closeCommandPalette();
        selectContact(pid);
      }
    }
    if (e.key === 'Escape') {
      closeCommandPalette();
    }
  });

  // Shortcuts panel close on click outside
  dom.shortcutsPanel.addEventListener('click', function (e) {
    if (e.target === dom.shortcutsPanel) {
      dom.shortcutsPanel.classList.remove('open');
    }
  });

  // Global keyboard shortcuts
  document.addEventListener('keydown', function (e) {
    // Ignore if typing in an input (except for global shortcuts)
    var tag = document.activeElement ? document.activeElement.tagName : '';
    var isInput = tag === 'INPUT' || tag === 'TEXTAREA';

    // ? to toggle shortcuts help
    if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey && !isInput) {
      e.preventDefault();
      toggleShortcuts();
      return;
    }

    // Escape to close all modals
    if (e.key === 'Escape') {
      if (dom.shortcutsPanel.classList.contains('open') ||
          dom.commandPalette.classList.contains('open') ||
          dom.groupModal.classList.contains('open') ||
          dom.lightbox.classList.contains('open') ||
          dom.emojiPicker.classList.contains('open') ||
          dom.mentionPopup.classList.contains('open') ||
          dom.replyBar.classList.contains('active')) {
        closeAllModals();
        return;
      }
    }

    // Ctrl+K / Cmd+K for command palette
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      if (dom.commandPalette.classList.contains('open')) {
        closeCommandPalette();
      } else {
        openCommandPalette();
      }
      return;
    }

    // Ctrl+N / Cmd+N for new chat (open group modal as new chat)
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
      e.preventDefault();
      openGroupModal();
      return;
    }
  });

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
  // PWA - Register Service Worker
  // ═══════════════════════════════════════════════════════════════
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').then(function (reg) {
        // Service worker registered
      }).catch(function () {
        // Service worker registration failed (non-critical)
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // Bootstrap
  // ═══════════════════════════════════════════════════════════════
  connectWebSocket();

})();
</script>
</body>
</html>"""
