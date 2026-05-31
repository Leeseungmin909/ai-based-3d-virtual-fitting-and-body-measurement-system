/// Model used by the UI after parsing fitting history responses.
class FittingHistoryItem {
  const FittingHistoryItem({
    required this.id,
    required this.clothesName,
    required this.status,
    this.createdAt,
    this.resultSplatUrl,
  });

  final int? id;
  final String clothesName;
  final String status;
  final String? createdAt;
  final String? resultSplatUrl;

  factory FittingHistoryItem.fromJson(Map<String, dynamic> json) {
    return FittingHistoryItem(
      id: _asInt(json['id'] ?? json['fittingId']),
      clothesName:
          json['clothesName']?.toString() ??
          json['name']?.toString() ??
          '옷 이름 없음',
      status: json['status']?.toString() ?? 'PENDING',
      createdAt:
          json['createdAt']?.toString() ?? json['fittingDate']?.toString(),
      resultSplatUrl:
          json['resultSplatUrl']?.toString() ??
          json['result_splat_url']?.toString(),
    );
  }

  static int? _asInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    return int.tryParse(value.toString());
  }
}
