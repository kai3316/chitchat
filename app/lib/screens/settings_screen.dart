import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:chitchat/services/settings_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _nameCtrl;

  @override
  void initState() {
    super.initState();
    final settings = context.read<SettingsService>();
    _nameCtrl = TextEditingController(text: settings.deviceName);
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsService>();
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        centerTitle: true,
      ),
      body: ListView(
        children: [
          const SizedBox(height: 8),

          // ── Device Section ──────────────────────────────
          _sectionHeader('Device'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Device Name',
                      style: theme.textTheme.labelMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _nameCtrl,
                      decoration: const InputDecoration(
                        hintText: 'Enter device name',
                        isDense: true,
                        border: OutlineInputBorder(),
                      ),
                      onSubmitted: (value) =>
                          settings.setDeviceName(value),
                      onEditingComplete: () =>
                          settings.setDeviceName(_nameCtrl.text),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.tonal(
                        onPressed: () =>
                            settings.setDeviceName(_nameCtrl.text),
                        child: const Text('Save Name'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 16),

          // ── Appearance Section ──────────────────────────
          _sectionHeader('Appearance'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Card(
              child: SwitchListTile(
                title: const Text('Dark Theme'),
                subtitle: Text(
                  settings.isDarkMode ? 'Dark mode is on' : 'Light mode is on',
                ),
                secondary: Icon(
                  settings.isDarkMode ? Icons.dark_mode : Icons.light_mode,
                ),
                value: settings.isDarkMode,
                onChanged: (_) => settings.toggleTheme(),
              ),
            ),
          ),

          const SizedBox(height: 16),

          // ── Notifications Section ───────────────────────
          _sectionHeader('Notifications'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Card(
              child: SwitchListTile(
                title: const Text('Notification Sounds'),
                subtitle: Text(
                  settings.notificationSound
                      ? 'Sounds are enabled'
                      : 'Sounds are muted',
                ),
                secondary: Icon(
                  settings.notificationSound
                      ? Icons.volume_up
                      : Icons.volume_off,
                ),
                value: settings.notificationSound,
                onChanged: (_) => settings.toggleNotificationSound(),
              ),
            ),
          ),

          const SizedBox(height: 16),

          // ── Keyboard Shortcuts Section ──────────────────
          _sectionHeader('Keyboard Shortcuts'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.keyboard, size: 20),
                        const SizedBox(width: 8),
                        Text(
                          'Desktop Shortcuts',
                          style: theme.textTheme.titleSmall,
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    _shortcutRow('Enter', 'Send message'),
                    _shortcutRow('Shift + Enter', 'New line in message'),
                    _shortcutRow('Long press message', 'Emoji reactions / Reply / Copy'),
                    _shortcutRow('Swipe message', 'Reply to message'),
                    _shortcutRow('Tap image', 'Full-screen viewer'),
                    _shortcutRow('@', 'Mention member (group chats)'),
                    _shortcutRow('Tap reply preview', 'Open thread view'),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 16),

          // ── Server Section ──────────────────────────────
          _sectionHeader('Server'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.dns_outlined, size: 20),
                        const SizedBox(width: 8),
                        Text(
                          'Daemon WebSocket',
                          style: theme.textTheme.titleSmall,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Row(
                        children: [
                          Icon(
                            Icons.link,
                            size: 16,
                            color: Colors.greenAccent,
                          ),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'ws://127.0.0.1:9876',
                              style: TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 16),

          // ── About Section ───────────────────────────────
          _sectionHeader('About'),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.chat_bubble_rounded,
                          color: theme.colorScheme.primary,
                          size: 28,
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'ChitChat',
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              'P2P Chat Application',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    const Divider(),
                    const SizedBox(height: 8),
                    _aboutRow('Version', '1.0.0'),
                    _aboutRow('Platform', 'Windows / Android / Linux'),
                    _aboutRow('Protocol', 'WebSocket JSON-RPC'),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _sectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
              color: Theme.of(context).colorScheme.primary,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
            ),
      ),
    );
  }

  Widget _aboutRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ),
          Expanded(
            child: Text(value, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
      ),
    );
  }

  Widget _shortcutRow(String keys, String description) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: Theme.of(context)
                  .colorScheme
                  .primaryContainer
                  .withOpacity(0.3),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(
                color: Theme.of(context)
                    .colorScheme
                    .primary
                    .withOpacity(0.3),
              ),
            ),
            child: Text(
              keys,
              style: TextStyle(
                fontSize: 12,
                fontFamily: 'monospace',
                fontWeight: FontWeight.w600,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              description,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontSize: 13,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}
