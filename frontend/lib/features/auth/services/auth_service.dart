import '../../../core/services/api_client.dart';
import '../../../core/services/token_storage.dart';

/// 실제 Google 로그인 대신 Spring mock 로그인 API를 호출한다.
class AuthService {
  AuthService({ApiClient? apiClient, TokenStorage? tokenStorage})
    : _apiClient = apiClient ?? ApiClient(),
      _tokenStorage = tokenStorage ?? TokenStorage();

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  /// 테스트 계정으로 로그인하고 반환된 JWT를 저장한다.
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

  /// 저장된 JWT 토큰을 삭제한다.
  Future<void> signOut() => _tokenStorage.clearToken();
}
