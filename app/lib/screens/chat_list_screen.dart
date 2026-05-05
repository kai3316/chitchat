import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:chitchat/services/daemon_service.dart';
import 'package:chitchat/screens/chat_screen.dart';
import 'package:chitchat/screens/settings_screen.dart';
import 'package:chitchat/screens/create_group_screen.dart';
import 'package:chitchat/widgets/connection_indicator.dart';

class ChatListScreen extends StatefulWidget {
  const ChatListScreen({super.key});

  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  bool _fabExpanded = false;

  void _toggleFab() {
    setState(() => _fabExpanded = !_fabExpanded);
  }

  void _closeFab() {
    if (_fabExpanded) {
      setState(() => _fabExpanded = false);
    }
  }

  void _openNewChat() {
    _closeFab();
    final daemon = context.read<DaemonService>();
    final contacts = daemon.contacts;

    showModalBottomSheet(
      context: context,
      backgroundColor:
          Theme.of(context).colorScheme.surfaceContainerHigh,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(2),
                  ),
                  alignment: Alignment.center,
                ),
                Text(
                  'New Chat',
                  style: Theme.of(ctx)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                if (contacts.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Center(
                      child: Text(
                        'No contacts available.\nDevices on your LAN will appear here.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.white54),
                      ),
                    ),
                  )
                else
                  ...contacts.map((contact) {
                    final name =
                        contact['device_name'] as String? ?? 'Unknown';
                    final deviceId = contact['device_id'] as String;
                    final online = contact['online'] as bool? ?? false;
                    return ListTile(
                      leading: Stack(
                        children: [
                          CircleAvatar(
                            backgroundColor:
                                Theme.of(ctx).colorScheme.primaryContainer,
                            child: Text(
                              name[0].toUpperCase(),
                              style: TextStyle(
                                color:
                                    Theme.of(ctx).colorScheme.onPrimaryContainer,
                              ),
                            ),
                          ),
                          if (online)
                            Positioned(
                              right: 0,
                              bottom: 0,
                              child: Container(
                                width: 10,
                                height: 10,
                                decoration: BoxDecoration(
                                  color: Colors.greenAccent,
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: Theme.of(ctx).scaffoldBackgroundColor,
                                    width: 2,
                                  ),
                                ),
                              ),
                            ),
                        ],
                      ),
                      title: Text(name),
                      subtitle: Text(
                        online ? 'Online' : 'Offline',
                        style: TextStyle(
                          color:
                              online ? Colors.greenAccent : Colors.white38,
                          fontSize: 12,
                        ),
                      ),
                      onTap: () {
                        Navigator.pop(ctx);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ChatScreen(
                              peerId: deviceId,
                              peerName: name,
                            ),
                          ),
                        );
                      },
                    );
                  }),
                const SizedBox(height: 8),
              ],
            ),
          ),
        );
      },
    );
  }

  void _openNewGroup() {
    _closeFab();
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const CreateGroupScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final daemon = context.watch<DaemonService>();
    final contacts = daemon.contacts;
    final groups = daemon.groups;

    // Build combined list: contacts + groups
    final List<Map<String, dynamic>> combinedList = [];
    for (final g in groups) {
      combinedList.add({
        'type': 'group',
        'group_id': g['group_id'] as String? ?? '',
        'name': g['name'] as String? ?? 'Group',
        'member_ids': g['member_ids'] as List<dynamic>? ?? [],
        'last_message': g['last_message'] as String? ?? '',
        'sender_name': g['sender_name'] as String? ?? '',
        'unread_count': g['unread_count'] as int? ?? 0,
        'online': false,
      });
    }
    for (final c in contacts) {
      combinedList.add({
        'type': 'contact',
        'device_id': c['device_id'] as String,
        'device_name': c['device_name'] as String? ?? 'Unknown',
        'last_message': c['last_message'] as String? ?? '',
        'online': c['online'] as bool? ?? false,
        'unread_count': c['unread_count'] as int? ?? 0,
      });
    }

    return GestureDetector(
      onTap: _closeFab,
      child: Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              _buildHeader(context, daemon),
              Expanded(
                child: combinedList.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.chat_bubble_outline,
                                size: 64, color: Colors.white24),
                            SizedBox(height: 16),
                            Text('No contacts yet',
                                style: TextStyle(
                                    color: Colors.white54, fontSize: 16)),
                            SizedBox(height: 8),
                            Text(
                              'Devices on your LAN will appear here',
                              style: TextStyle(
                                  color: Colors.white30, fontSize: 13),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        itemCount: combinedList.length,
                        itemBuilder: (_, i) =>
                            _buildTile(context, combinedList[i]),
                      ),
              ),
            ],
          ),
        ),
        floatingActionButton: _buildFab(context),
      ),
    );
  }

  Widget _buildFab(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (_fabExpanded) ...[
          _fabMiniButton(
            context,
            icon: Icons.person_add,
            label: 'New Chat',
            onPressed: _openNewChat,
          ),
          const SizedBox(height: 12),
          _fabMiniButton(
            context,
            icon: Icons.group_add,
            label: 'New Group',
            onPressed: _openNewGroup,
          ),
          const SizedBox(height: 12),
        ],
        FloatingActionButton(
          onPressed: _toggleFab,
          backgroundColor: theme.colorScheme.primary,
          child: AnimatedRotation(
            turns: _fabExpanded ? 0.125 : 0,
            duration: const Duration(milliseconds: 250),
            child: const Icon(Icons.add, color: Colors.white),
          ),
        ),
      ],
    );
  }

  Widget _fabMiniButton(
    BuildContext context, {
    required IconData icon,
    required String label,
    required VoidCallback onPressed,
  }) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHigh,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(label, style: const TextStyle(fontSize: 13)),
        ),
        const SizedBox(width: 8),
        FloatingActionButton.small(
          onPressed: onPressed,
          backgroundColor: theme.colorScheme.surfaceContainerHigh,
          child: Icon(icon, color: theme.colorScheme.primary),
        ),
      ],
    );
  }

  Widget _buildHeader(BuildContext context, DaemonService daemon) {
    final connectedPeers =
        daemon.status['peers_online'] as List<dynamic>? ?? [];
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'ChitChat',
                  style: Theme.of(context)
                      .textTheme
                      .headlineSmall
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  '${connectedPeers.length} online',
                  style: TextStyle(
                    color: connectedPeers.isNotEmpty
                        ? Colors.greenAccent
                        : Colors.white38,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 4),
                const ConnectionIndicator(),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) => const SettingsScreen()),
              );
            },
            tooltip: 'Settings',
          ),
        ],
      ),
    );
  }

  Widget _buildTile(BuildContext context, Map<String, dynamic> item) {
    final type = item['type'] as String? ?? 'contact';

    if (type == 'group') {
      return _buildGroupTile(context, item);
    }
    return _buildContactTile(context, item);
  }

  Widget _buildGroupTile(
      BuildContext context, Map<String, dynamic> group) {
    final name = group['name'] as String? ?? 'Group';
    final lastMsg = group['last_message'] as String? ?? '';
    final senderName = group['sender_name'] as String? ?? '';
    final groupId = group['group_id'] as String? ?? '';
    final memberIds = group['member_ids'] as List<dynamic>? ?? [];
    final unread = group['unread_count'] as int? ?? 0;
    final theme = Theme.of(context);

    final subtitle = lastMsg.isNotEmpty
        ? (senderName.isNotEmpty ? '$senderName: $lastMsg' : lastMsg)
        : 'Tap to chat';

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 3),
      child: ListTile(
        leading: Stack(
          children: [
            CircleAvatar(
              backgroundColor: theme.colorScheme.primaryContainer,
              child: const Icon(Icons.groups, size: 20),
            ),
          ],
        ),
        title: Text(name, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(
          subtitle,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '${memberIds.length}',
              style: const TextStyle(color: Colors.white38, fontSize: 12),
            ),
            const SizedBox(width: 6),
            if (unread > 0)
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary,
                  shape: BoxShape.circle,
                ),
                child: Text(
                  '$unread',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ChatScreen(
                peerId: groupId,
                peerName: name,
                isGroup: true,
                memberCount: memberIds.length,
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildContactTile(
      BuildContext context, Map<String, dynamic> contact) {
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
              backgroundColor:
                  Theme.of(context).colorScheme.primaryContainer,
              child: Text(
                name[0].toUpperCase(),
                style: TextStyle(
                  color:
                      Theme.of(context).colorScheme.onPrimaryContainer,
                ),
              ),
            ),
            if (online)
              Positioned(
                right: 0,
                bottom: 0,
                child: Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: Colors.greenAccent,
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: Theme.of(context).scaffoldBackgroundColor,
                      width: 2,
                    ),
                  ),
                ),
              ),
          ],
        ),
        title:
            Text(name, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(
          lastMsg.isNotEmpty ? lastMsg : 'Tap to chat',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: unread > 0
            ? Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primary,
                  shape: BoxShape.circle,
                ),
                child: Text('$unread',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold)),
              )
            : null,
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) =>
                  ChatScreen(peerId: deviceId, peerName: name),
            ),
          );
        },
      ),
    );
  }
}
