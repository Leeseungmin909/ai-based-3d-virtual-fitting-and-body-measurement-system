import '../../../core/services/api_client.dart';

/// ??? ? ???? Spring ??? API? ????.
class UserService {
  UserService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<void> updateMyHeight(double heightCm) async {
    await _apiClient.putJson('/api/users/me/body-info', {
      'heightCm': heightCm,
    }, authorized: true);
  }
}
