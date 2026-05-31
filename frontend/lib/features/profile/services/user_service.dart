import '../../../core/services/api_client.dart';

/// Saves the user height through the Spring user API.
class UserService {
  UserService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<void> updateMyHeight(double heightCm) async {
    await _apiClient.putJson('/api/users/me/body-info', {
      'heightCm': heightCm,
    }, authorized: true);
  }
}
