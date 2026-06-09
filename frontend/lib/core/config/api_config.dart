import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Flutter가 호출할 Spring Boot API 주소를 한 곳에서 관리한다.
class ApiConfig {
  const ApiConfig._();

  static const String _baseUrlKey = 'api_base_url';
  static const String _defaultAndroidEmulatorHost = 'http://192.168.137.1:8080';
  static const String _defaultLocalHost = 'http://localhost:8080';

  static String? _overrideBaseUrl;

  static String get baseUrl {
    final configured = _overrideBaseUrl;
    if (configured != null && configured.isNotEmpty) return configured;
    return defaultBaseUrl;
  }

  static String get defaultBaseUrl {
    if (defaultTargetPlatform == TargetPlatform.android) {
      return _defaultAndroidEmulatorHost;
    }
    return _defaultLocalHost;
  }

  static Uri uri(String path) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$baseUrl$normalizedPath');
  }

  static String fileUrl(String? value) {
    if (value == null || value.isEmpty) return '';
    if (value.startsWith('http://') || value.startsWith('https://')) {
      return value;
    }
    final normalizedPath = value.startsWith('/') ? value : '/$value';
    return '$baseUrl$normalizedPath';
  }

  static Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_baseUrlKey);
    if (saved != null && saved.trim().isNotEmpty) {
      _overrideBaseUrl = _trimTrailingSlash(saved.trim());
    }
  }

  static Future<void> updateBaseUrl(String value) async {
    final trimmed = value.trim();
    if (trimmed.isEmpty) {
      await resetBaseUrl();
      return;
    }
    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      throw const FormatException('서버 주소는 http:// 또는 https://로 시작해야 합니다.');
    }
    _overrideBaseUrl = _trimTrailingSlash(trimmed);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_baseUrlKey, _overrideBaseUrl!);
  }

  static Future<void> resetBaseUrl() async {
    _overrideBaseUrl = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_baseUrlKey);
  }

  static String _trimTrailingSlash(String value) {
    var current = value;
    while (current.endsWith('/')) {
      current = current.substring(0, current.length - 1);
    }
    return current;
  }
}
