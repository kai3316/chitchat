import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:chitchat/services/daemon_service.dart';

class CreateGroupScreen extends StatefulWidget {
  const CreateGroupScreen({super.key});

  @override
  State<CreateGroupScreen> createState() => _CreateGroupScreenState();
}

class _CreateGroupScreenState extends State<CreateGroupScreen> {
  final _nameCtrl = TextEditingController();
  final Set<String> _selectedIds = {};
  String? _errorText;

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  Future<void> _createGroup() async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      setState(() => _errorText = 'Group name is required');
      return;
    }
    if (_selectedIds.isEmpty) {
      setState(() => _errorText = 'Select at least one member');
      return;
    }

    try {
      final daemon = context.read<DaemonService>();
      await daemon.createGroup(name, _selectedIds.toList());
      if (mounted) {
        Navigator.pop(context, true);
      }
    } catch (e) {
      setState(() => _errorText = 'Failed to create group: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final daemon = context.watch<DaemonService>();
    final contacts = daemon.contacts;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Group'),
        centerTitle: true,
        actions: [
          TextButton(
            onPressed: _createGroup,
            child: const Text('Create'),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: TextField(
              controller: _nameCtrl,
              decoration: InputDecoration(
                labelText: 'Group Name',
                hintText: 'Enter a group name',
                errorText: _errorText,
                prefixIcon: const Icon(Icons.group),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: theme.colorScheme.surfaceContainerHighest,
              ),
              onChanged: (_) {
                if (_errorText != null) {
                  setState(() => _errorText = null);
                }
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Text(
                  'Select Members',
                  style: theme.textTheme.titleSmall?.copyWith(
                    color: theme.colorScheme.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                Text(
                  '${_selectedIds.length} selected',
                  style: TextStyle(
                    color: Colors.white38,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: contacts.isEmpty
                ? const Center(
                    child: Text(
                      'No contacts available',
                      style: TextStyle(color: Colors.white38),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    itemCount: contacts.length,
                    itemBuilder: (_, i) {
                      final contact = contacts[i];
                      final name =
                          contact['device_name'] as String? ?? 'Unknown';
                      final deviceId = contact['device_id'] as String? ?? '';
                      final selected = _selectedIds.contains(deviceId);

                      return CheckboxListTile(
                        value: selected,
                        onChanged: (checked) {
                          setState(() {
                            if (checked == true) {
                              _selectedIds.add(deviceId);
                            } else {
                              _selectedIds.remove(deviceId);
                            }
                          });
                        },
                        title: Text(name),
                        subtitle: Text(
                          deviceId,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 11, fontFamily: 'monospace'),
                        ),
                        secondary: CircleAvatar(
                          backgroundColor: theme.colorScheme.primaryContainer,
                          child: Text(
                            name[0].toUpperCase(),
                            style: TextStyle(
                              color: theme.colorScheme.onPrimaryContainer,
                            ),
                          ),
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        activeColor: theme.colorScheme.primary,
                      );
                    },
                  ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _createGroup,
                child: const Text('Create Group'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
