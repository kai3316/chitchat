import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:chitchat/screens/chat_list_screen.dart';
import 'package:chitchat/services/daemon_service.dart';
import 'package:chitchat/services/settings_service.dart';

void main() {
  runApp(const ChitChatApp());
}

class ChitChatApp extends StatelessWidget {
  const ChitChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => DaemonService()..connect()),
        ChangeNotifierProvider(create: (_) => SettingsService()),
      ],
      child: const _AppShell(),
    );
  }
}

class _AppShell extends StatelessWidget {
  const _AppShell({super.key});

  @override
  Widget build(BuildContext context) {
    final daemon = context.watch<DaemonService>();
    final settings = context.watch<SettingsService>();

    return MaterialApp(
      title: 'ChitChat',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        colorSchemeSeed: const Color(0xFF6750A4),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorSchemeSeed: const Color(0xFF6750A4),
      ),
      themeMode: settings.themeMode,
      home: Stack(
        children: [
          const ChatListScreen(),
          if (!daemon.isConnected)
            Positioned(
              top: 0,
              left: 0,
              right: 0,
              child: Material(
                child: Container(
                  color: Colors.orange.shade800,
                  padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
                  child: const SafeArea(
                    bottom: false,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                        SizedBox(width: 10),
                        Text(
                          'Connecting to daemon...',
                          style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
