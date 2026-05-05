class Group {
  final String groupId;
  final String name;
  final List<String> memberIds;
  final String avatarUrl;
  final DateTime createdAt;
  final String createdBy;

  Group({
    required this.groupId,
    required this.name,
    required this.memberIds,
    this.avatarUrl = '',
    required this.createdAt,
    required this.createdBy,
  });

  factory Group.fromJson(Map<String, dynamic> json) => Group(
        groupId: json['group_id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        memberIds:
            (json['member_ids'] as List<dynamic>?)?.cast<String>() ?? [],
        avatarUrl: json['avatar_url'] as String? ?? '',
        createdAt: DateTime.tryParse(
                json['created_at'] as String? ?? '') ??
            DateTime.now(),
        createdBy: json['created_by'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
        'group_id': groupId,
        'name': name,
        'member_ids': memberIds,
        'avatar_url': avatarUrl,
        'created_at': createdAt.toIso8601String(),
        'created_by': createdBy,
      };
}
