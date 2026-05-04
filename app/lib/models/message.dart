class Message {
  final String msgId;
  final String peerId;
  final String direction;
  final String msgType;
  final String body;
  final double timestamp;
  final bool delivered;
  final bool read;

  Message({
    required this.msgId, required this.peerId, required this.direction,
    required this.msgType, required this.body, required this.timestamp,
    this.delivered = false, this.read = false,
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
  );
}
