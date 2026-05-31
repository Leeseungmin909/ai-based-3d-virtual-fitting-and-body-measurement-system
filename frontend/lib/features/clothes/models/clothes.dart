/// Spring 옷 응답을 파싱한 뒤 UI에서 사용하는 모델이다.
class Clothes {
  const Clothes({
    required this.id,
    required this.name,
    required this.category,
    required this.imageUrl,
    required this.base3dUrl,
    this.totalLengthCm,
    this.shoulderWidthCm,
    this.chestWidthCm,
    this.sleeveLengthCm,
    this.waistWidthCm,
    this.hipWidthCm,
    this.thighWidthCm,
    this.crotchCm,
    this.hemWidthCm,
  });

  final int? id;
  final String name;
  final String category;
  final String imageUrl;
  final String base3dUrl;
  final double? totalLengthCm;
  final double? shoulderWidthCm;
  final double? chestWidthCm;
  final double? sleeveLengthCm;
  final double? waistWidthCm;
  final double? hipWidthCm;
  final double? thighWidthCm;
  final double? crotchCm;
  final double? hemWidthCm;

  factory Clothes.fromJson(Map<String, dynamic> json) {
    return Clothes(
      id: _asInt(json['id']),
      name: json['name']?.toString() ?? '이름 없음',
      category: json['category']?.toString().toUpperCase() ?? 'UNKNOWN',
      imageUrl:
          json['imageUrl']?.toString() ?? json['image_url']?.toString() ?? '',
      base3dUrl:
          json['base3dUrl']?.toString() ??
          json['base_3d_url']?.toString() ??
          '',
      totalLengthCm: _asDouble(
        json['totalLengthCm'] ??
            json['total_length_cm'] ??
            json['totalLength'] ??
            json['total_length'],
      ),
      shoulderWidthCm: _asDouble(
        json['shoulderWidthCm'] ??
            json['shoulder_width_cm'] ??
            json['shoulderWidth'] ??
            json['shoulder_width'],
      ),
      chestWidthCm: _asDouble(
        json['chestWidthCm'] ??
            json['chest_width_cm'] ??
            json['chestWidth'] ??
            json['chest_width'],
      ),
      sleeveLengthCm: _asDouble(
        json['sleeveLengthCm'] ??
            json['sleeve_length_cm'] ??
            json['sleeveLength'] ??
            json['sleeve_length'],
      ),
      waistWidthCm: _asDouble(
        json['waistWidthCm'] ??
            json['waist_width_cm'] ??
            json['waistWidth'] ??
            json['waist_width'],
      ),
      hipWidthCm: _asDouble(
        json['hipWidthCm'] ??
            json['hip_width_cm'] ??
            json['hipWidth'] ??
            json['hip_width'],
      ),
      thighWidthCm: _asDouble(
        json['thighWidthCm'] ??
            json['thigh_width_cm'] ??
            json['thighWidth'] ??
            json['thigh_width'],
      ),
      crotchCm: _asDouble(
        json['crotchCm'] ?? json['crotch_cm'] ?? json['crotch'],
      ),
      hemWidthCm: _asDouble(
        json['hemWidthCm'] ??
            json['hem_width_cm'] ??
            json['hemWidth'] ??
            json['hem_width'],
      ),
    );
  }

  static int? _asInt(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    return int.tryParse(value.toString());
  }

  static double? _asDouble(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString());
  }
}
