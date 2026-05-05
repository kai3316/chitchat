import 'dart:io';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class LinkPreviewCard extends StatelessWidget {
  final String url;
  final String? title;
  final String? description;
  final String? thumbnailUrl;
  final bool sent;

  const LinkPreviewCard({
    super.key,
    required this.url,
    this.title,
    this.description,
    this.thumbnailUrl,
    this.sent = false,
  });

  String get _domain {
    try {
      final uri = Uri.parse(url);
      return uri.host.replaceFirst('www.', '');
    } catch (_) {
      return url;
    }
  }

  Future<void> _openUrl(BuildContext context) async {
    final uri = Uri.tryParse(url);
    if (uri != null) {
      try {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } catch (_) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Could not open link')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textColor = sent ? theme.colorScheme.onPrimary : null;

    return GestureDetector(
      onTap: () => _openUrl(context),
      child: Container(
        width: 260,
        margin: const EdgeInsets.only(top: 6),
        decoration: BoxDecoration(
          color: sent
              ? theme.colorScheme.primary.withOpacity(0.08)
              : theme.colorScheme.surfaceContainerHighest.withOpacity(0.5),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: sent
                ? theme.colorScheme.primary.withOpacity(0.2)
                : Colors.white.withOpacity(0.08),
          ),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (thumbnailUrl != null && thumbnailUrl!.isNotEmpty)
              _buildThumbnail(),
            Padding(
              padding: const EdgeInsets.all(10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (title != null && title!.isNotEmpty)
                    Text(
                      title!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                        color: textColor,
                      ),
                    ),
                  if (description != null && description!.isNotEmpty) ...[
                    if (title != null && title!.isNotEmpty)
                      const SizedBox(height: 4),
                    Text(
                      description!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 12,
                        color: (textColor ?? Colors.white).withOpacity(0.6),
                      ),
                    ),
                  ],
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Icon(
                        Icons.link,
                        size: 14,
                        color: (textColor ?? Colors.white).withOpacity(0.5),
                      ),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          _domain,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 11,
                            color: (textColor ?? Colors.white).withOpacity(0.4),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildThumbnail() {
    if (thumbnailUrl == null || thumbnailUrl!.isEmpty) {
      return const SizedBox.shrink();
    }
    final isFile = File(thumbnailUrl!).existsSync();
    return SizedBox(
      height: 140,
      width: double.infinity,
      child: isFile
          ? Image.file(
              File(thumbnailUrl!),
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => _placeholderThumbnail(),
            )
          : Image.network(
              thumbnailUrl!,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => _placeholderThumbnail(),
            ),
    );
  }

  Widget _placeholderThumbnail() {
    return Container(
      height: 140,
      color: Colors.white.withOpacity(0.05),
      child: const Center(
        child: Icon(Icons.image, size: 32, color: Colors.white24),
      ),
    );
  }
}
