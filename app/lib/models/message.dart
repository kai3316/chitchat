class Message {
  final String msgId;
  final String peerId;
  final String direction;
  final String msgType;
  final String body;
  final double timestamp;
  final bool delivered;
  final bool read;

  // Phase 3: Rich media fields
  final String? imageUrl;
  final String? fileName;
  final int? fileSize;
  final int? voiceDuration;
  final String? linkUrl;
  final String? linkTitle;
  final String? linkDescription;
  final String? linkThumbnail;
  final String? replyTo;
  final String? replyPreview;

  Message({
    required this.msgId,
    required this.peerId,
    required this.direction,
    required this.msgType,
    required this.body,
    required this.timestamp,
    this.delivered = false,
    this.read = false,
    this.imageUrl,
    this.fileName,
    this.fileSize,
    this.voiceDuration,
    this.linkUrl,
    this.linkTitle,
    this.linkDescription,
    this.linkThumbnail,
    this.replyTo,
    this.replyPreview,
  });

  factory Message.fromJson(Map<String, dynamic> json) => Message(
        msgId: json['msg_id'] as String? ?? '',
        peerId: json['peer_id'] as String? ?? '',
        direction: json['direction'] as String? ?? 'received',
        msgType: json['msg_type'] as String? ?? 'chat_text',
        body: json['body'] as String? ?? '',
        timestamp: (json['timestamp'] as num?)?.toDouble() ?? 0.0,
        delivered: json['delivered'] as bool? ?? false,
        read: json['read'] as bool? ?? false,
        imageUrl: json['image_url'] as String?,
        fileName: json['file_name'] as String?,
        fileSize: json['file_size'] as int?,
        voiceDuration: json['voice_duration'] as int?,
        linkUrl: json['link_url'] as String?,
        linkTitle: json['link_title'] as String?,
        linkDescription: json['link_description'] as String?,
        linkThumbnail: json['link_thumbnail'] as String?,
        replyTo: json['reply_to'] as String?,
        replyPreview: json['reply_preview'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'msg_id': msgId,
        'peer_id': peerId,
        'direction': direction,
        'msg_type': msgType,
        'body': body,
        'timestamp': timestamp,
        'delivered': delivered,
        'read': read,
        'image_url': imageUrl,
        'file_name': fileName,
        'file_size': fileSize,
        'voice_duration': voiceDuration,
        'link_url': linkUrl,
        'link_title': linkTitle,
        'link_description': linkDescription,
        'link_thumbnail': linkThumbnail,
        'reply_to': replyTo,
        'reply_preview': replyPreview,
      };
}
