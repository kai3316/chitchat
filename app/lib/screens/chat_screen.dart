import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:chitchat/services/daemon_service.dart';
import 'package:chitchat/screens/image_viewer_screen.dart';
import 'package:chitchat/screens/thread_screen.dart';
import 'package:chitchat/widgets/voice_record_button.dart';
import 'package:chitchat/widgets/link_preview_card.dart';
import 'package:chitchat/widgets/file_message_bubble.dart';
import 'package:chitchat/widgets/emoji_picker.dart';
import 'package:chitchat/models/message.dart';

class ChatScreen extends StatefulWidget {
  final String peerId;
  final String peerName;
  final bool isGroup;
  final int memberCount;

  const ChatScreen({
    super.key,
    required this.peerId,
    required this.peerName,
    this.isGroup = false,
    this.memberCount = 0,
  });

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _textCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  Timer? _typingTimer;
  Map<String, dynamic>? _replyTo;
  bool _showEmojiPicker = false;
  bool _showMemberPicker = false;
  String _mentionFilter = '';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final daemon = context.read<DaemonService>();
      if (widget.isGroup) {
        daemon.getGroupHistory(widget.peerId);
      } else {
        daemon.getHistory(widget.peerId);
        daemon.markRead(widget.peerId);
      }
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

    final daemon = context.read<DaemonService>();
    if (widget.isGroup) {
      daemon.sendGroupMessage(widget.peerId, text);
    } else {
      daemon.sendMessage(
        widget.peerId,
        text,
        replyTo: _replyTo?['msg_id'] as String? ?? '',
      );
    }

    setState(() {
      _replyTo = null;
    });
  }

  void _onTyping() {
    if (widget.isGroup) return;
    _typingTimer?.cancel();
    context.read<DaemonService>().sendTyping(widget.peerId);
    _typingTimer = Timer(const Duration(seconds: 1), () {});
  }

  void _startReply(Map<String, dynamic> msg) {
    setState(() {
      _replyTo = msg;
      _showEmojiPicker = false;
    });
    FocusScope.of(context).requestFocus();
  }

  void _cancelReply() {
    setState(() => _replyTo = null);
  }

  void _onEmojiReacted(String emoji) {
    if (_replyTo != null) {
      final daemon = context.read<DaemonService>();
      daemon.sendReaction(
        widget.peerId,
        _replyTo!['msg_id'] as String? ?? '',
        emoji,
      );
      setState(() {
        _replyTo = null;
        _showEmojiPicker = false;
      });
    }
  }

  void _showAttachmentSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).colorScheme.surfaceContainerHigh,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _attachOption(ctx, Icons.image, 'Image', _pickImage),
                    _attachOption(ctx, Icons.attach_file, 'File', _pickFile),
                    _attachOption(ctx, Icons.link, 'Link', _sendLink),
                    _VoiceRecordOption(onRecordComplete: (path, duration) {
                      Navigator.pop(ctx);
                      final daemon = context.read<DaemonService>();
                      daemon.sendVoice(widget.peerId, path, duration);
                    }),
                  ],
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _attachOption(
      BuildContext ctx, IconData icon, String label, VoidCallback onTap) {
    return GestureDetector(
      onTap: () {
        Navigator.pop(ctx);
        onTap();
      },
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: Theme.of(ctx).colorScheme.primaryContainer,
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: Theme.of(ctx).colorScheme.onPrimaryContainer),
          ),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(fontSize: 12)),
        ],
      ),
    );
  }

  Future<void> _pickImage() async {
    try {
      final picker = ImagePicker();
      final picked = await picker.pickImage(source: ImageSource.gallery);
      if (picked != null && mounted) {
        final daemon = context.read<DaemonService>();
        await daemon.sendImage(widget.peerId, picked.path);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not pick image: $e')),
        );
      }
    }
  }

  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles();
      if (result != null && result.files.single.path != null && mounted) {
        final daemon = context.read<DaemonService>();
        await daemon.sendFile(widget.peerId, result.files.single.path!);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not pick file: $e')),
        );
      }
    }
  }

  void _sendLink() {
    final urlCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Send Link'),
          content: TextField(
            controller: urlCtrl,
            decoration: const InputDecoration(
              hintText: 'https://...',
              border: OutlineInputBorder(),
            ),
            textInputAction: TextInputAction.done,
            onSubmitted: (value) {
              if (value.trim().isNotEmpty) {
                Navigator.pop(ctx);
                final daemon = context.read<DaemonService>();
                daemon.sendLinkPreview(widget.peerId, value.trim());
              }
            },
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                final url = urlCtrl.text.trim();
                if (url.isNotEmpty) {
                  Navigator.pop(ctx);
                  final daemon = context.read<DaemonService>();
                  daemon.sendLinkPreview(widget.peerId, url);
                }
              },
              child: const Text('Send'),
            ),
          ],
        );
      },
    );
  }

  void _showMessageContextMenu(BuildContext context, Map<String, dynamic> msg) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).colorScheme.surfaceContainerHigh,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                // Emoji picker in context menu
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: EmojiPicker(
                    onEmojiSelected: (emoji) {
                      Navigator.pop(ctx);
                      final daemon = context.read<DaemonService>();
                      daemon.sendReaction(
                        widget.peerId,
                        msg['msg_id'] as String? ?? '',
                        emoji,
                      );
                    },
                  ),
                ),
                const Divider(),
                ListTile(
                  leading: const Icon(Icons.reply),
                  title: const Text('Reply'),
                  onTap: () {
                    Navigator.pop(ctx);
                    _startReply(msg);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.copy),
                  title: const Text('Copy'),
                  onTap: () {
                    Navigator.pop(ctx);
                    final body = msg['body'] as String? ?? '';
                    Clipboard.setData(ClipboardData(text: body));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Copied to clipboard'),
                        duration: Duration(seconds: 1),
                      ),
                    );
                  },
                ),
                if (msg['link_url'] != null)
                  ListTile(
                    leading: const Icon(Icons.open_in_browser),
                    title: const Text('Open Link'),
                    onTap: () {
                      Navigator.pop(ctx);
                    },
                  ),
                const SizedBox(height: 8),
              ],
            ),
          ),
        );
      },
    );
  }

  void _onMentionTyped(String text) {
    if (!widget.isGroup) return;
    final lastAt = text.lastIndexOf('@');
    if (lastAt >= 0) {
      final filter = text.substring(lastAt + 1);
      if (!filter.contains(' ') && filter.isNotEmpty) {
        setState(() {
          _showMemberPicker = true;
          _mentionFilter = filter.toLowerCase();
        });
        return;
      }
    }
    if (_showMemberPicker) {
      setState(() => _showMemberPicker = false);
    }
  }

  void _insertMention(String name) {
    final text = _textCtrl.text;
    final lastAt = text.lastIndexOf('@');
    if (lastAt >= 0) {
      final newText = '${text.substring(0, lastAt)}@$name ';
      _textCtrl.text = newText;
      _textCtrl.selection = TextSelection.collapsed(offset: newText.length);
    }
    setState(() => _showMemberPicker = false);
  }

  @override
  Widget build(BuildContext context) {
    final daemon = context.watch<DaemonService>();
    final messages = widget.isGroup
        ? daemon.getGroupMessages(widget.peerId)
        : daemon.getMessages(widget.peerId);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Text(
                widget.peerName[0].toUpperCase(),
                style: TextStyle(
                  fontSize: 14,
                  color: theme.colorScheme.onPrimaryContainer,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.peerName,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                Text(
                  widget.isGroup
                      ? '${widget.memberCount > 0 ? widget.memberCount : 'Group'} members'
                      : 'Online',
                  style: TextStyle(
                    fontSize: 12,
                    color: widget.isGroup ? Colors.white38 : Colors.greenAccent,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: messages.isEmpty
                ? const Center(
                    child: Text(
                      'No messages yet',
                      style: TextStyle(color: Colors.white38),
                    ),
                  )
                : GestureDetector(
                    onTap: () {
                      if (_showMemberPicker) {
                        setState(() => _showMemberPicker = false);
                      }
                    },
                    child: ListView.builder(
                      controller: _scrollCtrl,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 8),
                      itemCount: messages.length,
                      reverse: true,
                      itemBuilder: (_, i) {
                        final msg = messages[messages.length - 1 - i];
                        return _buildMessageBubble(context, msg);
                      },
                    ),
                  ),
          ),
          if (_replyTo != null) _buildReplyPreview(context),
          if (_showMemberPicker && widget.isGroup)
            _buildMentionOverlay(daemon),
          _buildInputBar(context),
          if (_showEmojiPicker)
            EmojiPicker(
              onEmojiSelected: (emoji) {
                _textCtrl.text += emoji;
                _textCtrl.selection = TextSelection.collapsed(
                    offset: _textCtrl.text.length);
                setState(() => _showEmojiPicker = false);
              },
            ),
        ],
      ),
    );
  }

  Widget _buildReplyPreview(BuildContext context) {
    if (_replyTo == null) return const SizedBox.shrink();
    final body = _replyTo!['body'] as String? ?? '';
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        border: Border(
          top: BorderSide(color: theme.colorScheme.primary.withOpacity(0.3)),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 3,
            height: 32,
            decoration: BoxDecoration(
              color: theme.colorScheme.primary,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Replying to',
                  style: TextStyle(
                    fontSize: 11,
                    color: theme.colorScheme.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  body.length > 80 ? '${body.substring(0, 80)}...' : body,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 13, color: Colors.white70),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, size: 18),
            onPressed: _cancelReply,
            visualDensity: VisualDensity.compact,
          ),
        ],
      ),
    );
  }

  Widget _buildMentionOverlay(DaemonService daemon) {
    final contacts = daemon.contacts
        .where((c) =>
            (c['device_name'] as String? ?? '')
                .toLowerCase()
                .contains(_mentionFilter))
        .toList();

    if (contacts.isEmpty) return const SizedBox.shrink();

    return Container(
      constraints: const BoxConstraints(maxHeight: 160),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHigh,
        border: Border(
          top: BorderSide(color: Colors.white.withOpacity(0.08)),
        ),
      ),
      child: ListView.separated(
        shrinkWrap: true,
        padding: const EdgeInsets.symmetric(vertical: 4),
        itemCount: contacts.length,
        separatorBuilder: (_, __) => Divider(
            height: 1, color: Colors.white.withOpacity(0.05)),
        itemBuilder: (_, i) {
          final c = contacts[i];
          final name = c['device_name'] as String? ?? 'Unknown';
          return ListTile(
            dense: true,
            leading: CircleAvatar(
              radius: 14,
              backgroundColor:
                  Theme.of(context).colorScheme.primaryContainer,
              child: Text(
                name[0].toUpperCase(),
                style: const TextStyle(fontSize: 12),
              ),
            ),
            title: Text(name, style: const TextStyle(fontSize: 14)),
            onTap: () => _insertMention(name),
          );
        },
      ),
    );
  }

  Widget _buildMessageBubble(BuildContext context, Map<String, dynamic> msg) {
    final msgType = msg['msg_type'] as String? ?? 'chat_text';
    final isSent = msg['direction'] == 'sent';
    final body = msg['body'] as String? ?? '';
    final time = DateTime.fromMillisecondsSinceEpoch(
      ((msg['timestamp'] as num?)?.toDouble() ?? 0).toInt() * 1000,
    );
    final delivered = msg['delivered'] as bool? ?? false;
    final read = msg['read'] as bool? ?? false;
    final senderName = msg['sender_name'] as String? ?? '';
    final replyPreview = msg['reply_preview'] as String?;
    final replyTo = msg['reply_to'] as String?;
    // Check for message type
    if (msgType == 'chat_image' && msg['image_url'] != null) {
      return _buildImageBubble(context, msg, isSent, time, delivered, read,
          senderName, replyPreview, replyTo);
    }

    if (msgType == 'chat_file' && msg['file_name'] != null) {
      return _buildFileBubble(context, msg, isSent, time, delivered, read,
          senderName, replyPreview, replyTo);
    }

    if (msgType == 'chat_voice') {
      return _buildVoiceBubble(context, msg, isSent, time, delivered, read,
          senderName, replyPreview, replyTo);
    }

    if (msgType == 'chat_link' || msg['link_url'] != null) {
      return _buildLinkBubble(context, msg, isSent, time, delivered, read,
          senderName, replyPreview, replyTo);
    }

    // Default text message bubble
    return _buildTextBubble(context, msg, isSent, body, time, delivered, read,
        senderName, replyPreview, replyTo);
  }

  Widget _wrapBubble({
    required BuildContext context,
    required bool isSent,
    required Widget child,
    required String senderName,
  }) {
    return Align(
      alignment: isSent ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 3),
        child: Column(
          crossAxisAlignment:
              isSent ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (widget.isGroup && !isSent && senderName.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(left: 4, bottom: 2),
                child: Text(
                  senderName,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
              ),
            child,
          ],
        ),
      ),
    );
  }

  Widget _buildTextBubble(
      BuildContext context,
      Map<String, dynamic> msg,
      bool isSent,
      String body,
      DateTime time,
      bool delivered,
      bool read,
      String senderName,
      String? replyPreview,
      String? replyTo) {
    final theme = Theme.of(context);
    final hasReply = replyPreview != null && replyPreview.isNotEmpty;

    final bubble = GestureDetector(
      onLongPress: () => _showMessageContextMenu(context, msg),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isSent
              ? theme.colorScheme.primary
              : theme.colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(18).copyWith(
            bottomRight: isSent ? const Radius.circular(4) : null,
            bottomLeft: isSent ? null : const Radius.circular(4),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (hasReply)
              GestureDetector(
                onTap: () {
                  if (replyTo != null && replyTo.isNotEmpty) {
                    final origMsg = Message(
                      msgId: replyTo,
                      peerId: msg['peer_id'] as String? ?? '',
                      direction: msg['direction'] as String? ?? '',
                      msgType: msg['msg_type'] as String? ?? '',
                      body: replyPreview,
                      timestamp: msg['timestamp'] as double? ?? 0,
                    );
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ThreadScreen(
                          originalMessage: origMsg,
                          peerId: widget.peerId,
                          peerName: widget.peerName,
                        ),
                      ),
                    );
                  }
                },
                child: Container(
                  padding: const EdgeInsets.all(8),
                  margin: const EdgeInsets.only(bottom: 6),
                  decoration: BoxDecoration(
                    color: isSent
                        ? theme.colorScheme.onPrimary.withOpacity(0.1)
                        : Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(8),
                    border: Border(
                      left: BorderSide(
                        color: isSent
                            ? theme.colorScheme.onPrimary.withOpacity(0.4)
                            : theme.colorScheme.primary,
                        width: 3,
                      ),
                    ),
                  ),
                  child: Text(
                    replyPreview.length > 100
                        ? '${replyPreview.substring(0, 100)}...'
                        : replyPreview,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 12,
                      color: isSent
                          ? theme.colorScheme.onPrimary.withOpacity(0.7)
                          : Colors.white54,
                    ),
                  ),
                ),
              ),
            if (body.contains(RegExp(r'https?://\S+')))
              _buildInlineLinkPreview(context, body, isSent),
            Text(
              body,
              style: TextStyle(
                color: isSent ? theme.colorScheme.onPrimary : null,
              ),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${time.hour}:${time.minute.toString().padLeft(2, '0')}',
                  style: TextStyle(
                    fontSize: 11,
                    color: isSent ? Colors.white60 : Colors.white38,
                  ),
                ),
                if (isSent) ...[
                  const SizedBox(width: 4),
                  Icon(
                    delivered
                        ? (read ? Icons.done_all : Icons.done)
                        : Icons.access_time,
                    size: 14,
                    color: Colors.white60,
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );

    if (isSent) {
      return Dismissible(
        key: Key(msg['msg_id'] as String? ?? ''),
        direction: DismissDirection.startToEnd,
        confirmDismiss: (direction) async {
          _startReply(msg);
          return false;
        },
        background: Container(
          alignment: Alignment.centerLeft,
          padding: const EdgeInsets.only(left: 20),
          color: Colors.transparent,
          child: Icon(Icons.reply, color: theme.colorScheme.primary, size: 24),
        ),
        child: _wrapBubble(
          context: context,
          isSent: isSent,
          senderName: senderName,
          child: bubble,
        ),
      );
    }

    return Dismissible(
      key: Key(msg['msg_id'] as String? ?? ''),
      direction: DismissDirection.endToStart,
      confirmDismiss: (direction) async {
        _startReply(msg);
        return false;
      },
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        color: Colors.transparent,
        child: Icon(Icons.reply, color: theme.colorScheme.primary, size: 24),
      ),
      child: _wrapBubble(
        context: context,
        isSent: isSent,
        senderName: senderName,
        child: bubble,
      ),
    );
  }

  Widget _buildImageBubble(
      BuildContext context,
      Map<String, dynamic> msg,
      bool isSent,
      DateTime time,
      bool delivered,
      bool read,
      String senderName,
      String? replyPreview,
      String? replyTo) {
    final theme = Theme.of(context);
    final imageUrl = msg['image_url'] as String? ?? '';
    final heroTag = 'img_${msg['msg_id']}';
    final isFile = File(imageUrl).existsSync();

    return _wrapBubble(
      context: context,
      isSent: isSent,
      senderName: senderName,
      child: GestureDetector(
        onLongPress: () => _showMessageContextMenu(context, msg),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ImageViewerScreen(
                imagePath: imageUrl,
                heroTag: heroTag,
              ),
            ),
          );
        },
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 3),
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.65,
            maxHeight: 250,
          ),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18).copyWith(
              bottomRight: isSent ? const Radius.circular(4) : null,
              bottomLeft: isSent ? null : const Radius.circular(4),
            ),
          ),
          clipBehavior: Clip.antiAlias,
          child: Stack(
            children: [
              Hero(
                tag: heroTag,
                child: isFile
                    ? Image.file(
                        File(imageUrl),
                        fit: BoxFit.cover,
                        width: double.infinity,
                        height: 250,
                        errorBuilder: (_, __, ___) => _imagePlaceholder(),
                      )
                    : Image.network(
                        imageUrl,
                        fit: BoxFit.cover,
                        width: double.infinity,
                        height: 250,
                        errorBuilder: (_, __, ___) => _imagePlaceholder(),
                      ),
              ),
              Positioned(
                bottom: 6,
                right: 8,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '${time.hour}:${time.minute.toString().padLeft(2, '0')}',
                        style:
                            const TextStyle(fontSize: 10, color: Colors.white70),
                      ),
                      if (isSent) ...[
                        const SizedBox(width: 3),
                        Icon(
                          delivered
                              ? (read ? Icons.done_all : Icons.done)
                              : Icons.access_time,
                          size: 12,
                          color: Colors.white70,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _imagePlaceholder() {
    return Container(
      height: 200,
      color: Colors.white.withOpacity(0.05),
      child: const Center(
        child: Icon(Icons.broken_image, size: 48, color: Colors.white24),
      ),
    );
  }

  Widget _buildFileBubble(
      BuildContext context,
      Map<String, dynamic> msg,
      bool isSent,
      DateTime time,
      bool delivered,
      bool read,
      String senderName,
      String? replyPreview,
      String? replyTo) {
    final fileName = msg['file_name'] as String? ?? 'file';
    final fileSize = msg['file_size'] as int? ?? 0;
    final filePath = msg['file_path'] as String?;

    return _wrapBubble(
      context: context,
      isSent: isSent,
      senderName: senderName,
      child: GestureDetector(
        onLongPress: () => _showMessageContextMenu(context, msg),
        child: Column(
          crossAxisAlignment:
              isSent ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            FileMessageBubble(
              fileName: fileName,
              fileSize: fileSize,
              sent: isSent,
              filePath: filePath,
            ),
            Padding(
              padding: const EdgeInsets.only(top: 2, left: 4, right: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${time.hour}:${time.minute.toString().padLeft(2, '0')}',
                    style:
                        const TextStyle(fontSize: 11, color: Colors.white38),
                  ),
                  if (isSent) ...[
                    const SizedBox(width: 4),
                    Icon(
                      delivered
                          ? (read ? Icons.done_all : Icons.done)
                          : Icons.access_time,
                      size: 13,
                      color: Colors.white38,
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVoiceBubble(
      BuildContext context,
      Map<String, dynamic> msg,
      bool isSent,
      DateTime time,
      bool delivered,
      bool read,
      String senderName,
      String? replyPreview,
      String? replyTo) {
    final duration = msg['voice_duration'] as int? ?? 0;
    final seconds = duration ~/ 1000;
    final mins = seconds ~/ 60;
    final secs = seconds % 60;
    final durationText = '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
    final theme = Theme.of(context);

    return _wrapBubble(
      context: context,
      isSent: isSent,
      senderName: senderName,
      child: GestureDetector(
        onLongPress: () => _showMessageContextMenu(context, msg),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.6),
          decoration: BoxDecoration(
            color: isSent
                ? theme.colorScheme.primary
                : theme.colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(18).copyWith(
              bottomRight: isSent ? const Radius.circular(4) : null,
              bottomLeft: isSent ? null : const Radius.circular(4),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.mic,
                size: 20,
                color: isSent ? theme.colorScheme.onPrimary : Colors.white70,
              ),
              const SizedBox(width: 8),
              // Audio waveform bars (decorative)
              ...List.generate(4, (i) {
                final heights = [14.0, 22.0, 10.0, 16.0];
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 1.5),
                  child: Container(
                    width: 3,
                    height: heights[i],
                    decoration: BoxDecoration(
                      color: (isSent
                              ? theme.colorScheme.onPrimary
                              : theme.colorScheme.primary)
                          .withOpacity(0.6),
                      borderRadius: BorderRadius.circular(1.5),
                    ),
                  ),
                );
              }),
              const SizedBox(width: 10),
              Text(
                durationText,
                style: TextStyle(
                  fontSize: 13,
                  fontFamily: 'monospace',
                  color: isSent ? theme.colorScheme.onPrimary : Colors.white70,
                ),
              ),
              const SizedBox(width: 8),
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
    );
  }

  Widget _buildLinkBubble(
      BuildContext context,
      Map<String, dynamic> msg,
      bool isSent,
      DateTime time,
      bool delivered,
      bool read,
      String senderName,
      String? replyPreview,
      String? replyTo) {
    final linkUrl = msg['link_url'] as String? ?? '';
    final linkTitle = msg['link_title'] as String?;
    final linkDescription = msg['link_description'] as String?;
    final linkThumbnail = msg['link_thumbnail'] as String?;
    final body = msg['body'] as String? ?? '';

    return _wrapBubble(
      context: context,
      isSent: isSent,
      senderName: senderName,
      child: GestureDetector(
        onLongPress: () => _showMessageContextMenu(context, msg),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.75),
          decoration: BoxDecoration(
            color: isSent
                ? Theme.of(context).colorScheme.primary
                : Theme.of(context).colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(18).copyWith(
              bottomRight: isSent ? const Radius.circular(4) : null,
              bottomLeft: isSent ? null : const Radius.circular(4),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              if (body.isNotEmpty && body != linkUrl)
                Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Text(
                    body,
                    style: TextStyle(
                      color: isSent
                          ? Theme.of(context).colorScheme.onPrimary
                          : null,
                    ),
                  ),
                ),
              LinkPreviewCard(
                url: linkUrl,
                title: linkTitle,
                description: linkDescription,
                thumbnailUrl: linkThumbnail,
                sent: isSent,
              ),
              const SizedBox(height: 4),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${time.hour}:${time.minute.toString().padLeft(2, '0')}',
                    style: TextStyle(
                      fontSize: 11,
                      color: isSent ? Colors.white60 : Colors.white38,
                    ),
                  ),
                  if (isSent) ...[
                    const SizedBox(width: 4),
                    Icon(
                      delivered
                          ? (read ? Icons.done_all : Icons.done)
                          : Icons.access_time,
                      size: 13,
                      color: Colors.white60,
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInlineLinkPreview(
      BuildContext context, String body, bool isSent) {
    final urlRegex = RegExp(r'(https?://\S+)');
    final match = urlRegex.firstMatch(body);
    if (match == null) return const SizedBox.shrink();

    final url = match.group(1)!;
    return LinkPreviewCard(
      url: url,
      sent: isSent,
    );
  }

  Widget _buildInputBar(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
            top: BorderSide(color: Colors.white.withOpacity(0.08))),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.attach_file),
            onPressed: _showAttachmentSheet,
            tooltip: 'Attach',
          ),
          Expanded(
            child: TextField(
              controller: _textCtrl,
              onChanged: (text) {
                _onTyping();
                _onMentionTyped(text);
              },
              maxLines: 5,
              minLines: 1,
              style: const TextStyle(fontSize: 15),
              decoration: InputDecoration(
                hintText: widget.isGroup ? 'Message group...' : 'Message',
                hintStyle: const TextStyle(color: Colors.white38),
                filled: true,
                fillColor: theme.colorScheme.surfaceContainerHighest,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          const SizedBox(width: 4),
          if (widget.isGroup)
            IconButton(
              icon: const Icon(Icons.emoji_emotions_outlined),
              onPressed: () {
                setState(() => _showEmojiPicker = !_showEmojiPicker);
              },
              tooltip: 'Emoji',
              visualDensity: VisualDensity.compact,
            ),
          IconButton.filled(
            icon: const Icon(Icons.send_rounded),
            onPressed: _sendMessage,
            tooltip: 'Send',
          ),
        ],
      ),
    );
  }
}

class _VoiceRecordOption extends StatelessWidget {
  final void Function(String filePath, int durationMs) onRecordComplete;

  const _VoiceRecordOption({required this.onRecordComplete});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        VoiceRecordButton(
          onRecordComplete: onRecordComplete,
          onCancel: () {},
        ),
        const SizedBox(height: 8),
        const Text('Voice', style: TextStyle(fontSize: 12)),
      ],
    );
  }
}
