import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class FileMessageBubble extends StatelessWidget {
  final String fileName;
  final int fileSize;
  final bool sent;
  final String? filePath;

  const FileMessageBubble({
    super.key,
    required this.fileName,
    required this.fileSize,
    this.sent = false,
    this.filePath,
  });

  String get _formattedSize {
    if (fileSize < 1024) return '$fileSize B';
    if (fileSize < 1024 * 1024) {
      return '${(fileSize / 1024).toStringAsFixed(1)} KB';
    }
    if (fileSize < 1024 * 1024 * 1024) {
      return '${(fileSize / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(fileSize / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }

  String get _extension {
    final dot = fileName.lastIndexOf('.');
    if (dot == -1) return '';
    return fileName.substring(dot + 1).toLowerCase();
  }

  IconData get _fileIcon {
    switch (_extension) {
      case 'pdf':
        return Icons.picture_as_pdf;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'webp':
      case 'bmp':
        return Icons.image;
      case 'mp4':
      case 'mov':
      case 'avi':
      case 'mkv':
      case 'webm':
        return Icons.videocam;
      case 'mp3':
      case 'wav':
      case 'aac':
      case 'ogg':
      case 'flac':
        return Icons.audiotrack;
      case 'zip':
      case 'rar':
      case '7z':
      case 'tar':
      case 'gz':
        return Icons.folder_zip;
      case 'doc':
      case 'docx':
        return Icons.description;
      case 'xls':
      case 'xlsx':
        return Icons.table_chart;
      case 'ppt':
      case 'pptx':
        return Icons.slideshow;
      default:
        return Icons.insert_drive_file;
    }
  }

  Color get _fileIconColor {
    switch (_extension) {
      case 'pdf':
        return Colors.red;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'webp':
        return Colors.green;
      case 'mp4':
      case 'mov':
      case 'avi':
        return Colors.blue;
      case 'mp3':
      case 'wav':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  void _copyFileName(BuildContext context) {
    Clipboard.setData(ClipboardData(text: fileName));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('File name copied: $fileName'),
        duration: const Duration(seconds: 1),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textColor = sent ? theme.colorScheme.onPrimary : null;

    return GestureDetector(
      onTap: () => _copyFileName(context),
      child: Container(
        width: 240,
        margin: const EdgeInsets.only(top: 4),
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: sent
              ? theme.colorScheme.primary.withOpacity(0.1)
              : Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: sent
                ? theme.colorScheme.primary.withOpacity(0.2)
                : Colors.white.withOpacity(0.08),
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: _fileIconColor.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(_fileIcon, color: _fileIconColor, size: 24),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    fileName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      color: textColor,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _formattedSize,
                    style: TextStyle(
                      fontSize: 11,
                      color: (textColor ?? Colors.white).withOpacity(0.5),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 4),
            IconButton(
              icon: Icon(
                Icons.download,
                size: 20,
                color: sent ? theme.colorScheme.onPrimary : theme.colorScheme.primary,
              ),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Download initiated'),
                    duration: Duration(seconds: 1),
                  ),
                );
              },
              tooltip: 'Download',
              visualDensity: VisualDensity.compact,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            ),
          ],
        ),
      ),
    );
  }
}
