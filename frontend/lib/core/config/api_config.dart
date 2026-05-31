import 'package:shared_preferences/shared_preferences.dart';

/// Spring 서버 baseUrl을 저장하고 API 요청 URI를 만든다.
class ApiConfig {
  const ApiConfig._();

  static const String defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8080',
  );
  static const String _storageKey = 'api_base_url';

  static String _baseUrl = defaultBaseUrl;

  static String get baseUrl => _baseUrl;

  static Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_storageKey);
    _baseUrl = normalizeBaseUrl(
      saved == null || saved.trim().isEmpty ? defaultBaseUrl : saved,
    );
  }

  static Future<void> updateBaseUrl(String value) async {
    final normalized = normalizeBaseUrl(value);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, normalized);
    _baseUrl = normalized;
  }

  static Future<void> resetBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
    _baseUrl = normalizeBaseUrl(defaultBaseUrl);
  }

  static String normalizeBaseUrl(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) {
      throw const FormatException('서버 주소를 입력해 주세요.');
    }

    final uri = Uri.tryParse(trimmed);
    if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
      throw const FormatException(
        '올바른 서버 주소가 아닙니다. 예: http://192.168.0.10:8080',
      );
    }
    if (uri.scheme != 'http' && uri.scheme != 'https') {
      throw const FormatException('서버 주소는 http 또는 https로 시작해야 합니다.');
    }

    var normalized = trimmed;
    while (normalized.endsWith('/')) {
      normalized = normalized.substring(0, normalized.length - 1);
    }
    return normalized;
  }

  static Uri uri(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return Uri.parse(path);
    }
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$baseUrl$normalizedPath');
  }

  static String fileUrl(String value) {
    if (value.isEmpty ||
        value.startsWith('http://') ||
        value.startsWith('https://')) {
      return value;
    }
    return uri(value).toString();
  }
}
