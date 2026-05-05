import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:chitchat/services/daemon_service.dart';

class ConnectionIndicator extends StatelessWidget {
  final bool showLabel;

  const ConnectionIndicator({super.key, this.showLabel = true});

  @override
  Widget build(BuildContext context) {
    final daemon = context.watch<DaemonService>();
    final connected = daemon.isConnected;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: connected
            ? Colors.green.withOpacity(0.15)
            : Colors.red.withOpacity(0.15),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: connected ? Colors.greenAccent : Colors.redAccent,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: (connected ? Colors.greenAccent : Colors.redAccent).withOpacity(0.5),
                  blurRadius: 4,
                  spreadRadius: 1,
                ),
              ],
            ),
          ),
          if (showLabel) ...[
            const SizedBox(width: 6),
            Text(
              connected ? 'Connected' : 'Disconnected',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: connected ? Colors.greenAccent : Colors.redAccent,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
