import 'package:flutter/material.dart';

class EmojiPicker extends StatelessWidget {
  final void Function(String emoji) onEmojiSelected;

  static const List<String> emojis = [
    '😀', '😂', '❤️', '👍', '👎',
    '🎉', '🔥', '😍', '🤔', '😢',
    '😡', '👋', '💪', '🙏', '✅',
    '❌', '⭐',
  ];

  const EmojiPicker({super.key, required this.onEmojiSelected});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 12),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 6,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              childAspectRatio: 1.0,
            ),
            itemCount: emojis.length,
            itemBuilder: (_, index) {
              return _EmojiButton(
                emoji: emojis[index],
                onTap: () => onEmojiSelected(emojis[index]),
              );
            },
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _EmojiButton extends StatelessWidget {
  final String emoji;
  final VoidCallback onTap;

  const _EmojiButton({required this.emoji, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Center(
          child: Text(
            emoji,
            style: const TextStyle(fontSize: 28),
          ),
        ),
      ),
    );
  }
}
