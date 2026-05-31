import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import 'token_storage.dart';

/// Classifies API errors so screens can show the right failure message.
enum ApiExceptionKind {
  connection,
  loginRequired,
  notFound,
  validation,
  server,
  invalidResponse,
  unknown,
}

/// Exception that carries HTTP status and UI-facing error category.
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

/// Handles Spring API calls, JWT headers, and response parsing.
class ApiClient {
  ApiClient({TokenStorage? tokenStorage})
    : _tokenStorage = tokenStorage ?? TokenStorage();

  static const Duration _timeout = Duration(seconds: 10);

  final TokenStorage _tokenStorage;

  /// Sends a JSON GET request and returns the decoded response.
  Future<dynamic> getJson(String path, {bool authorized = false}) async {
    return _send(
      () async => http.get(
        ApiConfig.uri(path),
        headers: await _headers(authorized: authorized),
      ),
    );
  }

  /// Sends a JSON POST request and returns the decoded response.
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

  /// Sends a JSON PUT request and returns the decoded response.
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

  /// Sends a form-urlencoded POST request.
  Future<dynamic> postForm(String path, Map<String, String> body) async {
    return _send(() async => http.post(ApiConfig.uri(path), body: body));
  }

  /// Applies common timeout, connection, and server error handling.
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

  /// Adds the stored JWT token to Authorization for protected requests.
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

  /// Checks HTTP success and decodes JSON or plain text responses.
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

  /// Converts HTTP status codes into UI-facing error categories.
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
