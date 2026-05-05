import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:chitchat/services/daemon_service.dart';

class ChatScreen extends StatefulWidget {
  final String peerId;
  final String peerName;

  const ChatScreen({super.key, required this.peerId, required this.peerName});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _textCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  Timer? _typingTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DaemonService>().getHistory(widget.peerId);
      context.read<DaemonService>().markRead(widget.peerId);
    });
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    _scrollCtrl.dispose();
    _typingTimer?.cancel();
    super.dispose();
  }

  void _sendMessage() {
    final text = _textCtrl.text.trim();
    if (text.isEmpty) return;
    _textCtrl.clear();
    context.read<DaemonService>().sendMessage(widget.peerId, text);
  }

  void _onTyping() {
    _typingTimer?.cancel();
    context.read<DaemonService>().sendTyping(widget.peerId);
    _typingTimer = Timer(const Duration(seconds: 1), () {});
  }

  @override
  Widget build(BuildContext context) {
    final daemon = context.watch<DaemonService>();
    final messages = daemon.getMessages(widget.peerId);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              child: Text(widget.peerName[0].toUpperCase(), style: TextStyle(fontSize: 14, color: Theme.of(context).colorScheme.onPrimaryContainer)),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(widget.peerName, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const Text('Online', style: TextStyle(fontSize: 12, color: Colors.greenAccent)),
              ],
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: messages.isEmpty
                ? const Center(child: Text('No messages yet', style: TextStyle(color: Colors.white38)))
                : ListView.builder(
                    controller: _scrollCtrl,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    itemCount: messages.length,
                    reverse: true,
                    itemBuilder: (_, i) {
                      final msg = messages[messages.length - 1 - i];
                      return _buildBubble(context, msg);
                    },
                  ),
          ),
          _buildInputBar(context),
        ],
      ),
    );
  }

  Widget _buildBubble(BuildContext context, Map<String, dynamic> msg) {
    final isSent = msg['direction'] == 'sent';
    final body = msg['body'] as String? ?? '';
    final time = DateTime.fromMillisecondsSinceEpoch(((msg['timestamp'] as num?)?.toDouble() ?? 0).toInt() * 1000);
    final delivered = msg['delivered'] as bool? ?? false;
    final read = msg['read'] as bool? ?? false;

    return Align(
      alignment: isSent ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 3),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isSent ? Theme.of(context).colorScheme.primary : Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(18).copyWith(
            bottomRight: isSent ? const Radius.circular(4) : null,
            bottomLeft: isSent ? null : const Radius.circular(4),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(body, style: TextStyle(color: isSent ? Theme.of(context).colorScheme.onPrimary : null)),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${time.hour}:${time.minute.toString().padLeft(2, '0')}',
                  style: TextStyle(fontSize: 11, color: isSent ? Colors.white60 : Colors.white38),
                ),
                if (isSent) ...[
                  const SizedBox(width: 4),
                  Icon(delivered ? (read ? Icons.done_all : Icons.done) : Icons.access_time, size: 14, color: Colors.white60),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputBar(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(top: BorderSide(color: Colors.white.withOpacity(0.08))),
      ),
      child: Row(
        children: [
          IconButton(icon: const Icon(Icons.add_circle_outline), onPressed: () {}, tooltip: 'Attach'),
          Expanded(
            child: TextField(
              controller: _textCtrl,
              onChanged: (_) => _onTyping(),
              style: const TextStyle(fontSize: 15),
              decoration: InputDecoration(
                hintText: 'Message',
                hintStyle: const TextStyle(color: Colors.white38),
                filled: true,
                fillColor: Theme.of(context).colorScheme.surfaceContainerHighest,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          const SizedBox(width: 8),
          IconButton.filled(icon: const Icon(Icons.send_rounded), onPressed: _sendMessage, tooltip: 'Send'),
        ],
      ),
    );
  }
}
