import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:chitchat/models/message.dart';

class ImageViewerScreen extends StatefulWidget {
  final String imagePath;
  final Message? message;
  final String? heroTag;

  const ImageViewerScreen({
    super.key,
    required this.imagePath,
    this.message,
    this.heroTag,
  });

  @override
  State<ImageViewerScreen> createState() => _ImageViewerScreenState();
}

class _ImageViewerScreenState extends State<ImageViewerScreen> {
  final TransformationController _transformCtrl = TransformationController();
  bool _showAppBar = true;

  @override
  void dispose() {
    _transformCtrl.dispose();
    super.dispose();
  }

  void _toggleAppBar() {
    setState(() {
      _showAppBar = !_showAppBar;
    });
  }

  void _shareImage() {
    Clipboard.setData(ClipboardData(text: widget.imagePath));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Image path copied to clipboard'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isFile = File(widget.imagePath).existsSync();
    final imageWidget = isFile
        ? Image.file(
            File(widget.imagePath),
            fit: BoxFit.contain,
            errorBuilder: (_, __, ___) => _buildErrorPlaceholder(),
          )
        : Image.network(
            widget.imagePath,
            fit: BoxFit.contain,
            errorBuilder: (_, __, ___) => _buildErrorPlaceholder(),
            loadingBuilder: (_, child, progress) {
              if (progress == null) return child;
              return Center(
                child: CircularProgressIndicator(
                  value: progress.expectedTotalBytes != null
                      ? progress.cumulativeBytesLoaded /
                          progress.expectedTotalBytes!
                      : null,
                ),
              );
            },
          );

    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTap: _toggleAppBar,
        child: Stack(
          children: [
            Center(
              child: InteractiveViewer(
                transformationController: _transformCtrl,
                minScale: 0.5,
                maxScale: 4.0,
                child: widget.heroTag != null
                    ? Hero(tag: widget.heroTag!, child: imageWidget)
                    : imageWidget,
              ),
            ),
            if (_showAppBar)
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: SafeArea(
                  bottom: false,
                  child: Container(
                    color: Colors.black54,
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Row(
                      children: [
                        IconButton(
                          icon: const Icon(Icons.close, color: Colors.white),
                          onPressed: () => Navigator.pop(context),
                          tooltip: 'Close',
                        ),
                        const Spacer(),
                        IconButton(
                          icon: const Icon(Icons.share, color: Colors.white),
                          onPressed: _shareImage,
                          tooltip: 'Copy path',
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorPlaceholder() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.broken_image, size: 64, color: Colors.white.withOpacity(0.4)),
          const SizedBox(height: 12),
          const Text(
            'Could not load image',
            style: TextStyle(color: Colors.white54, fontSize: 14),
          ),
        ],
      ),
    );
  }
}
