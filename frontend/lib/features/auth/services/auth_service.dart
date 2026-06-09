import '../../../core/services/api_client.dart';
import '../../../core/services/token_storage.dart';
import '../../../core/state/user_profile_store.dart';

/// 이메일/비밀번호 회원가입·로그인 API를 호출하고 JWT를 저장한다.
class AuthService {
  AuthService({
    ApiClient? apiClient,
    TokenStorage? tokenStorage,
    UserProfileStore? profileStore,
  })  : _apiClient = apiClient ?? ApiClient(),
        _tokenStorage = tokenStorage ?? TokenStorage(),
        _profileStore = profileStore ?? UserProfileStore();

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;
  final UserProfileStore _profileStore;

  Future<void> signUp({
    required String email,
    required String name,
    required String password,
  }) async {
    final response = await _apiClient.postJson('/api/auth/signup', {
      'email': email,
      'name': name,
      'password': password,
    });
    await _saveTokenFrom(response);
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    final response = await _apiClient.postJson('/api/auth/login', {
      'email': email,
      'password': password,
    });
    await _saveTokenFrom(response);
  }

  Future<void> signOut() async {
    await _tokenStorage.clearToken();
    await _profileStore.clear();
  }

  Future<void> _saveTokenFrom(dynamic response) async {
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

    // 이전 계정의 키/사진/아바타가 남지 않도록 비운 뒤, 서버가 준 키만 복원한다.
    await _profileStore.clear();
    final heightCm = response['heightCm'];
    if (heightCm is num) {
      await _profileStore.saveHeight(heightCm.toDouble());
    }
  }
}
