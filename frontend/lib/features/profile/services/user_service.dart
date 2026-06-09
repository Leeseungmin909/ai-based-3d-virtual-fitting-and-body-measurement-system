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
}