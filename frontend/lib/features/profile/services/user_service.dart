import '../../../core/services/api_client.dart';
import '../../../core/state/user_profile_store.dart';

/// 사용자 키와 원본 전신 사진을 Spring API에 저장한다.
class UserService {
  UserService({ApiClient? apiClient, UserProfileStore? profileStore})
      : _apiClient = apiClient ?? ApiClient(),
        _profileStore = profileStore ?? UserProfileStore();

  final ApiClient _apiClient;
  final UserProfileStore _profileStore;

  Future<void> saveHeight(double heightCm) async {
    await _apiClient.putJson('/api/users/me/body-info', {'heightCm': heightCm});
    await _profileStore.saveHeight(heightCm);
  }

  Future<String> uploadSourceImage(String imagePath) async {
    final response = await _apiClient.postMultipart(
      path: '/api/users/me/source-image',
      fileFieldName: 'file',
      filePath: imagePath,
    );

    if (response is! Map<String, dynamic>) {
      throw const ApiException(
        'Source image upload response format is invalid.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }

    final sourceImageUrl =
        response['sourceImageUrl'] ??
        response['source_image_url'] ??
        response['url'] ??
        response['path'];
    if (sourceImageUrl is! String || sourceImageUrl.isEmpty) {
      throw const ApiException(
        'Source image upload response does not contain sourceImageUrl.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }

    await _profileStore.saveSourceImageUrl(sourceImageUrl);
    return sourceImageUrl;
  }

  /// 현재 사용자의 신체 치수를 조회한다. 측정값이 없거나 오류면 null을 반환한다.
  Future<BodyMeasurement?> fetchMyMeasurements() async {
    try {
      final res = await _apiClient.getJson('/api/users/me/measurements');
      if (res is! Map<String, dynamic>) return null;
      return BodyMeasurement.fromJson(res);
    } catch (_) {
      return null;
    }
  }
}

/// 착용 가능 여부 판단에 필요한 사용자 신체 치수다.
class BodyMeasurement {
  const BodyMeasurement({
    this.shoulderWidthCm,
    this.chestWidthCm,
    this.waistWidthCm,
    this.hipWidthCm,
  });

  final double? shoulderWidthCm;
  final double? chestWidthCm;
  final double? waistWidthCm;
  final double? hipWidthCm;

  bool get hasTopMeasurements => shoulderWidthCm != null && chestWidthCm != null;
  bool get hasBottomMeasurements => waistWidthCm != null && hipWidthCm != null;

  factory BodyMeasurement.fromJson(Map<String, dynamic> json) {
    double? read(String a, String b) => _asDouble(json[a] ?? json[b]);
    return BodyMeasurement(
      shoulderWidthCm: read('shoulderWidthCm', 'shoulder_width_cm'),
      chestWidthCm: read('chestWidthCm', 'chest_width_cm'),
      waistWidthCm: read('waistWidthCm', 'waist_width_cm'),
      hipWidthCm: read('hipWidthCm', 'hip_width_cm'),
    );
  }

  static double? _asDouble(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString());
  }
}