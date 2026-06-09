class FittingCreateResult {
  const FittingCreateResult({
    required this.fittingId,
    required this.clothesId,
    required this.status,
    required this.message,
  });

  final int? fittingId;
  final int? clothesId;
  final String status;
  final String message;

  factory FittingCreateResult.fromJson(Map<String, dynamic> json) {
    return FittingCreateResult(
      fittingId: _asInt(json['fittingId'] ?? json['id']),
      clothesId: _asInt(json['clothesId']),
      status: json['status']?.toString() ?? 'PENDING',
      message: json['message']?.toString() ?? '피팅 요청이 생성되었습니다.',
    );
  }
}

class FittingResult {
  const FittingResult({
    required this.fittingId,
    required this.status,
    required this.ready,
    required this.message,
    this.aiJobId,
    this.avatarGlbUrl,
    this.renderImageUrl,
    this.resultJsonUrl,
  });

  final int? fittingId;
  final String status;
  final bool ready;
  final String message;
  final String? aiJobId;
  final String? avatarGlbUrl;
  final String? renderImageUrl;
  final String? resultJsonUrl;

  factory FittingResult.fromJson(Map<String, dynamic> json) {
    return FittingResult(
      fittingId: _asInt(json['fittingId'] ?? json['id']),
      status: json['status']?.toString() ?? 'PENDING',
      ready: json['ready'] == true,
      message: json['message']?.toString() ?? '피팅 결과를 확인하고 있습니다.',
      aiJobId: json['aiJobId']?.toString(),
      avatarGlbUrl: json['avatarGlbUrl']?.toString(),
      renderImageUrl: json['renderImageUrl']?.toString(),
      resultJsonUrl: json['resultJsonUrl']?.toString(),
    );
  }

  bool get isPending => status == 'PENDING' || status == 'PROCESSING';
  bool get isFailed => status == 'FAIL' || status == 'FAILED';
}

int? _asInt(dynamic value) {
  if (value == null) return null;
  if (value is int) return value;
  return int.tryParse(value.toString());
}