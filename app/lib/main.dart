import 'package:flutter/material.dart';
import 'screens/chat_list_screen.dart';
import 'services/daemon_service.dart';
import 'package:provider/provider.dart';

void main() {
  runApp(const ChitChatApp());
}

class ChitChatApp extends StatelessWidget {
  const ChitChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => DaemonService()..connect(),
      child: MaterialApp(
        title: 'ChitChat',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          brightness: Brightness.dark,
          colorSchemeSeed: const Color(0xFF6750A4),
          fontFamily: 'GoogleSans',
        ),
        darkTheme: ThemeData(
          useMaterial3: true,
          brightness: Brightness.dark,
          colorSchemeSeed: const Color(0xFF6750A4),
          fontFamily: 'GoogleSans',
        ),
        themeMode: ThemeMode.dark,
        home: const ChatListScreen(),
      ),
    );
  }
}
