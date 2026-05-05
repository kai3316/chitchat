import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:chitchat/services/daemon_service.dart';
import 'package:chitchat/models/message.dart';

class ThreadScreen extends StatefulWidget {
  final Message originalMessage;
  final String peerId;
  final String peerName;

  const ThreadScreen({
    super.key,
    required this.originalMessage,
    required this.peerId,
    required this.peerName,
  });

  @override
  State<ThreadScreen> createState() => _ThreadScreenState();
}

class _ThreadScreenState extends State<ThreadScreen> {
  final _textCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final List<Map<String, dynamic>> _replies = [];
  Timer? _typingTimer;

  @override
  void initState() {
    super.initState();
    // Add the original message as the first item
    _replies.add(widget.originalMessage.toJson());
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    _scrollCtrl.dispose();
    _typingTimer?.cancel();
    super.dispose();
  }

  void _sendReply() {
    final text = _textCtrl.text.trim();
    if (text.isEmpty) return;
    _textCtrl.clear();

    final daemon = context.read<DaemonService>();
    daemon.sendMessage(widget.peerId, text,
        replyTo: widget.originalMessage.msgId);

    setState(() {
      _replies.add({
        'msg_id': 'local_${DateTime.now().millisecondsSinceEpoch}',
        'peer_id': widget.peerId,
        'direction': 'sent',
        'msg_type': 'chat_text',
        'body': text,
        'timestamp': DateTime.now().millisecondsSinceEpoch / 1000.0,
        'reply_to': widget.originalMessage.msgId,
        'reply_preview': widget.originalMessage.body,
      });
    });

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          0,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _onTyping() {
    _typingTimer?.cancel();
    context.read<DaemonService>().sendTyping(widget.peerId);
    _typingTimer = Timer(const Duration(seconds: 1), () {});
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text('Thread - ${widget.peerName}'),
        titleTextStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              itemCount: _replies.length,
              reverse: true,
              itemBuilder: (_, i) {
                final msg = _replies[_replies.length - 1 - i];
                return _buildThreadBubble(context, msg, i == 0);
              },
            ),
          ),
          _buildInputBar(context),
        ],
      ),
    );
  }

  Widget _buildThreadBubble(BuildContext context, Map<String, dynamic> msg, bool isOriginal) {
    final isSent = msg['direction'] == 'sent';
    final body = msg['body'] as String? ?? '';
    final time = DateTime.fromMillisecondsSinceEpoch(
      ((msg['timestamp'] as num?)?.toDouble() ?? 0).toInt() * 1000,
    );
    final theme = Theme.of(context);

    return Container(
      margin: EdgeInsets.symmetric(
        vertical: 3,
        horizontal: isOriginal ? 0 : (isSent ? 0 : 20),
      ),
      child: Column(
        crossAxisAlignment:
            isSent ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          if (isOriginal)
            Container(
              padding: const EdgeInsets.all(10),
              margin: const EdgeInsets.only(bottom: 4),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary.withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: theme.colorScheme.primary.withOpacity(0.2),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.reply,
                    size: 18,
                    color: theme.colorScheme.primary,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Thread started',
                      style: TextStyle(
                        fontSize: 12,
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          Align(
            alignment: isSent ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 2),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.7,
              ),
              decoration: BoxDecoration(
                color: isSent
                    ? theme.colorScheme.primary
                    : theme.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(16).copyWith(
                  bottomRight: isSent ? const Radius.circular(4) : null,
                  bottomLeft: isSent ? null : const Radius.circular(4),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (isOriginal)
                    Text(
                      body,
                      style: TextStyle(
                        color: isSent ? theme.colorScheme.onPrimary : null,
                        fontWeight: FontWeight.w500,
                      ),
                    )
                  else
                    Text(
                      body,
                      style: TextStyle(
                        color: isSent ? theme.colorScheme.onPrimary : null,
                      ),
                    ),
                  const SizedBox(height: 4),
                  Text(
                    '${time.hour}:${time.minute.toString().padLeft(2, '0')}',
                    style: TextStyle(
                      fontSize: 10,
                      color: isSent ? Colors.white54 : Colors.white30,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          top: BorderSide(color: Colors.white.withOpacity(0.08)),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _textCtrl,
              onChanged: (_) => _onTyping(),
              style: const TextStyle(fontSize: 15),
              decoration: InputDecoration(
                hintText: 'Reply in thread...',
                hintStyle: const TextStyle(color: Colors.white38),
                filled: true,
                fillColor: theme.colorScheme.surfaceContainerHighest,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 10,
                ),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _sendReply(),
            ),
          ),
          const SizedBox(width: 8),
          IconButton.filled(
            icon: const Icon(Icons.send_rounded),
            onPressed: _sendReply,
            tooltip: 'Send',
          ),
        ],
      ),
    );
  }
}
