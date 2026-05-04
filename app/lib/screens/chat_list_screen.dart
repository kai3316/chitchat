import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/daemon_service.dart';
import 'chat_screen.dart';

class ChatListScreen extends StatelessWidget {
  const ChatListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final daemon = context.watch<DaemonService>();
    final contacts = daemon.contacts;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context, daemon),
            Expanded(
              child: contacts.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.chat_bubble_outline, size: 64, color: Colors.white24),
                          SizedBox(height: 16),
                          Text('No contacts yet', style: TextStyle(color: Colors.white54, fontSize: 16)),
                          SizedBox(height: 8),
                          Text('Devices on your LAN will appear here', style: TextStyle(color: Colors.white30, fontSize: 13)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: contacts.length,
                      itemBuilder: (_, i) => _buildContactTile(context, contacts[i]),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, DaemonService daemon) {
    final connectedPeers = daemon.status['peers_online'] as List<dynamic>? ?? [];
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('ChitChat', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(
                  '${connectedPeers.length} online',
                  style: TextStyle(color: connectedPeers.isNotEmpty ? Colors.greenAccent : Colors.white38, fontSize: 13),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () {},
            tooltip: 'Settings',
          ),
        ],
      ),
    );
  }

  Widget _buildContactTile(BuildContext context, Map<String, dynamic> contact) {
    final name = contact['device_name'] as String? ?? 'Unknown';
    final lastMsg = contact['last_message'] as String? ?? '';
    final online = contact['online'] as bool? ?? false;
    final unread = contact['unread_count'] as int? ?? 0;
    final deviceId = contact['device_id'] as String;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 3),
      child: ListTile(
        leading: Stack(
          children: [
            CircleAvatar(
              backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              child: Text(name[0].toUpperCase(), style: TextStyle(color: Theme.of(context).colorScheme.onPrimaryContainer)),
            ),
            if (online)
              Positioned(
                right: 0, bottom: 0,
                child: Container(
                  width: 12, height: 12,
                  decoration: BoxDecoration(
                    color: Colors.greenAccent,
                    shape: BoxShape.circle,
                    border: Border.all(color: Theme.of(context).scaffoldBackgroundColor, width: 2),
                  ),
                ),
              ),
          ],
        ),
        title: Text(name, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(lastMsg.isNotEmpty ? lastMsg : 'Tap to chat', maxLines: 1, overflow: TextOverflow.ellipsis),
        trailing: unread > 0
            ? Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(color: Theme.of(context).colorScheme.primary, shape: BoxShape.circle),
                child: Text('$unread', style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
              )
            : null,
        onTap: () {
          Navigator.push(context, MaterialPageRoute(builder: (_) => ChatScreen(peerId: deviceId, peerName: name)));
        },
      ),
    );
  }
}
