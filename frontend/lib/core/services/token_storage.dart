import 'package:shared_preferences/shared_preferences.dart';

/// JWT 토큰을 로컬 저장소에 저장하고 읽는다.
class TokenStorage {
  static const _tokenKey = 'jwt_token';

  Future<String?> readToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }
}
