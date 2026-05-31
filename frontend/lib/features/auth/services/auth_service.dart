import '../../../core/services/api_client.dart';
import '../../../core/services/token_storage.dart';

/// Calls the Spring mock login API instead of a real Google login flow.
class AuthService {
  AuthService({ApiClient? apiClient, TokenStorage? tokenStorage})
    : _apiClient = apiClient ?? ApiClient(),
      _tokenStorage = tokenStorage ?? TokenStorage();

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  /// Logs in with a test account and stores the returned JWT.
  Future<void> signInWithGoogleMock() async {
    final response = await _apiClient.postForm('/api/auth/google', {
      'email': 'capstone_tester@gmail.com',
      'name': 'Capstone Tester',
    });

    if (response is! Map<String, dynamic>) {
      throw const ApiException(
        'Login response format is invalid.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }

    final token = response['token'] ?? response['accessToken'];
    if (token is! String || token.isEmpty) {
      throw const ApiException(
        'Login response does not contain a token.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }

    await _tokenStorage.saveToken(token);
  }

  /// Clears the stored JWT token.
  Future<void> signOut() => _tokenStorage.clearToken();
}
