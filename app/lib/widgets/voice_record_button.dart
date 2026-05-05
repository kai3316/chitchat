import 'dart:async';
import 'package:flutter/material.dart';

class VoiceRecordButton extends StatefulWidget {
  final void Function(String filePath, int durationMs) onRecordComplete;
  final void Function()? onCancel;

  const VoiceRecordButton({
    super.key,
    required this.onRecordComplete,
    this.onCancel,
  });

  @override
  State<VoiceRecordButton> createState() => _VoiceRecordButtonState();
}

class _VoiceRecordButtonState extends State<VoiceRecordButton>
    with SingleTickerProviderStateMixin {
  bool _isRecording = false;
  bool _willCancel = false;
  int _elapsedMs = 0;
  Timer? _timer;
  late AnimationController _pulseCtrl;
  Offset _startPos = Offset.zero;
  double _dragDistance = 0;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _timer?.cancel();
    super.dispose();
  }

  void _startRecording() {
    setState(() {
      _isRecording = true;
      _willCancel = false;
      _elapsedMs = 0;
      _dragDistance = 0;
    });
    _pulseCtrl.repeat(reverse: true);
    _timer = Timer.periodic(const Duration(milliseconds: 100), (_) {
      if (mounted) {
        setState(() {
          _elapsedMs += 100;
        });
      }
    });
  }

  void _stopRecording() {
    _timer?.cancel();
    _pulseCtrl.stop();
    _pulseCtrl.reset();

    if (!mounted) return;

    final durationMs = _elapsedMs;

    setState(() {
      _isRecording = false;
      _willCancel = false;
      _elapsedMs = 0;
    });

    if (_willCancel || durationMs < 500) {
      widget.onCancel?.call();
    } else {
      // Simulate recording: generate a dummy file path and duration
      final tempPath = '/tmp/voice_${DateTime.now().millisecondsSinceEpoch}.aac';
      widget.onRecordComplete(tempPath, durationMs);
    }
  }

  String get _formattedDuration {
    final seconds = _elapsedMs ~/ 1000;
    final minutes = seconds ~/ 60;
    final secs = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    if (_isRecording) {
      return GestureDetector(
        onVerticalDragUpdate: (details) {
          _dragDistance += details.delta.dy;
          setState(() {
            _willCancel = _dragDistance < -80;
          });
        },
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_willCancel)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                margin: const EdgeInsets.only(bottom: 8),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.delete, color: Colors.red, size: 18),
                    const SizedBox(width: 6),
                    Text(
                      'Release to cancel',
                      style: TextStyle(color: Colors.red.shade300, fontSize: 13),
                    ),
                  ],
                ),
              ),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Recording',
                  style: TextStyle(color: Colors.white38, fontSize: 13),
                ),
                const SizedBox(width: 8),
                Text(
                  _formattedDuration,
                  style: const TextStyle(
                    color: Colors.redAccent,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'monospace',
                  ),
                ),
                const SizedBox(width: 12),
                AnimatedBuilder(
                  animation: _pulseCtrl,
                  builder: (_, child) {
                    return Transform.scale(
                      scale: 1.0 + (_pulseCtrl.value * 0.25),
                      child: child,
                    );
                  },
                  child: GestureDetector(
                    onTap: _stopRecording,
                    child: Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: Colors.redAccent,
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Colors.redAccent.withOpacity(0.4),
                            blurRadius: 12,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: const Icon(Icons.stop, color: Colors.white, size: 28),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      );
    }

    return GestureDetector(
      onLongPressStart: (_) => _startRecording(),
      onLongPressEnd: (_) => _stopRecording(),
      onLongPressCancel: () {
        _timer?.cancel();
        _pulseCtrl.stop();
        _pulseCtrl.reset();
        if (mounted) {
          setState(() {
            _isRecording = false;
            _willCancel = false;
            _elapsedMs = 0;
          });
        }
      },
      child: Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
        ),
        child: Icon(
          Icons.mic,
          color: Theme.of(context).colorScheme.primary,
          size: 22,
        ),
      ),
    );
  }
}
