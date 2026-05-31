import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import 'token_storage.dart';

/// 화면에서 적절한 실패 메시지를 보여줄 수 있도록 API 오류를 분류한다.
enum ApiExceptionKind {
  connection,
  loginRequired,
  notFound,
  validation,
  server,
  invalidResponse,
  unknown,
}

/// HTTP 상태 코드와 화면 표시용 오류 분류를 함께 담는 예외이다.
class ApiException implements Exception {
  const ApiException(
    this.message, {
    this.statusCode,
    this.kind = ApiExceptionKind.unknown,
  });

  final String message;
  final int? statusCode;
  final ApiExceptionKind kind;

  @override
  String toString() => statusCode == null ? message : '$message ($statusCode)';
}

/// Spring API 호출, JWT 헤더 추가, 응답 파싱을 처리한다.
class ApiClient {
  ApiClient({TokenStorage? tokenStorage})
    : _tokenStorage = tokenStorage ?? TokenStorage();

  static const Duration _timeout = Duration(seconds: 10);

  final TokenStorage _tokenStorage;

  /// JSON GET 요청을 보내고 파싱된 응답을 반환한다.
  Future<dynamic> getJson(String path, {bool authorized = false}) async {
    return _send(
      () async => http.get(
        ApiConfig.uri(path),
        headers: await _headers(authorized: authorized),
      ),
    );
  }

  /// JSON POST 요청을 보내고 파싱된 응답을 반환한다.
  Future<dynamic> postJson(
    String path,
    Map<String, dynamic> body, {
    bool authorized = false,
  }) async {
    return _send(
      () async => http.post(
        ApiConfig.uri(path),
        headers: await _headers(authorized: authorized),
        body: jsonEncode(body),
      ),
    );
  }

  /// JSON PUT 요청을 보내고 파싱된 응답을 반환한다.
  Future<dynamic> putJson(
    String path,
    Map<String, dynamic> body, {
    bool authorized = false,
  }) async {
    return _send(
      () async => http.put(
        ApiConfig.uri(path),
        headers: await _headers(authorized: authorized),
        body: jsonEncode(body),
      ),
    );
  }

  /// form-urlencoded POST 요청을 보낸다.
  Future<dynamic> postForm(String path, Map<String, String> body) async {
    return _send(() async => http.post(ApiConfig.uri(path), body: body));
  }

  /// 공통 timeout, 연결 실패, 서버 오류 처리를 적용한다.
  Future<dynamic> _send(Future<http.Response> Function() request) async {
    try {
      final response = await request().timeout(_timeout);
      return _decode(response);
    } on ApiException {
      rethrow;
    } on TimeoutException {
      throw const ApiException(
        'Server response timed out.',
        kind: ApiExceptionKind.connection,
      );
    } on http.ClientException catch (e) {
      throw ApiException(
        e.message.isEmpty ? 'Could not connect to server.' : e.message,
        kind: ApiExceptionKind.connection,
      );
    } catch (e) {
      throw ApiException(e.toString(), kind: ApiExceptionKind.unknown);
    }
  }

  /// 보호된 요청에 저장된 JWT 토큰을 Authorization 헤더로 추가한다.
  Future<Map<String, String>> _headers({required bool authorized}) async {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (authorized) {
      final token = await _tokenStorage.readToken();
      if (token == null || token.isEmpty) {
        throw const ApiException(
          'Login token is missing.',
          kind: ApiExceptionKind.loginRequired,
        );
      }
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  /// HTTP 성공 여부를 확인하고 JSON 또는 일반 텍스트 응답을 파싱한다.
  dynamic _decode(http.Response response) {
    if (response.statusCode == 204 || response.bodyBytes.isEmpty) {
      return null;
    }

    final decodedBody = utf8.decode(response.bodyBytes);
    final isSuccess = response.statusCode >= 200 && response.statusCode < 300;
    if (!isSuccess) {
      throw ApiException(
        decodedBody.isEmpty ? 'Server request failed.' : decodedBody,
        statusCode: response.statusCode,
        kind: _kindForStatus(response.statusCode),
      );
    }

    try {
      return jsonDecode(decodedBody);
    } on FormatException {
      return decodedBody;
    }
  }

  /// HTTP 상태 코드를 화면 표시용 오류 분류로 변환한다.
  ApiExceptionKind _kindForStatus(int statusCode) {
    if (statusCode == 401 || statusCode == 403) {
      return ApiExceptionKind.loginRequired;
    }
    if (statusCode == 404) {
      return ApiExceptionKind.notFound;
    }
    if (statusCode == 400 || statusCode == 422) {
      return ApiExceptionKind.validation;
    }
    if (statusCode >= 500) {
      return ApiExceptionKind.server;
    }
    return ApiExceptionKind.unknown;
  }
}
