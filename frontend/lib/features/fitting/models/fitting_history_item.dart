class FittingHistoryItem {
  const FittingHistoryItem({
    required this.id,
    required this.clothesName,
    required this.status,
    this.createdAt,
    this.aiJobId,
    this.avatarGlbUrl,
    this.renderImageUrl,
    this.resultJsonUrl,
  });

  final int? id;
  final String clothesName;
  final String status;
  final String? createdAt;
  final String? aiJobId;
  final String? avatarGlbUrl;
  final String? renderImageUrl;
  final String? resultJsonUrl;

  factory FittingHistoryItem.fromJson(Map<String, dynamic> json) {
    return FittingHistoryItem(
      id: _asInt(json['id'] ?? json['fittingId']),
      clothesName: json['clothesName']?.toString() ?? json['name']?.toString() ?? '선택한 옷',
      status: json['status']?.toString() ?? 'PENDING',
      createdAt: json['createdAt']?.toString() ?? json['fittingDate']?.toString(),
      aiJobId: json['aiJobId']?.toString(),
      avatarGlbUrl: json['avatarGlbUrl']?.toString(),
      renderImageUrl: json['renderImageUrl']?.toString(),
      resultJsonUrl: json['resultJsonUrl']?.toString(),
    );
  }

  bool get hasResult => avatarGlbUrl != null || renderImageUrl != null;

  static int? _asInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    return int.tryParse(value.toString());
  }
}