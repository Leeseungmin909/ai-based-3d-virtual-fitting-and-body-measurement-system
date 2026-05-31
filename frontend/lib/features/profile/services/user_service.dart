import '../../../core/services/api_client.dart';

/// Spring 사용자 API를 통해 사용자의 키 정보를 저장한다.
class UserService {
  UserService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<void> updateMyHeight(double heightCm) async {
    await _apiClient.putJson('/api/users/me/body-info', {
      'heightCm': heightCm,
    }, authorized: true);
  }
}
