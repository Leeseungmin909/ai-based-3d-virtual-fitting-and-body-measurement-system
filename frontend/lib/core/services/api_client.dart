import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import 'token_storage.dart';

enum ApiExceptionKind {
  network,
  unauthorized,
  notFound,
  server,
  invalidResponse,
  unknown,
}

class ApiException implements Exception {
  const ApiException(this.message, {this.kind = ApiExceptionKind.unknown});

  final String message;
  final ApiExceptionKind kind;

  @override
  String toString() => message;
}

/// Spring Boot API 호출을 담당하는 공통 HTTP 클라이언트다.
class ApiClient {
  ApiClient({http.Client? httpClient, TokenStorage? tokenStorage})
      : _httpClient = httpClient ?? http.Client(),
        _tokenStorage = tokenStorage ?? TokenStorage();

  final http.Client _httpClient;
  final TokenStorage _tokenStorage;

  Future<dynamic> getJson(String path) async {
    return _sendJson(() async {
      return _httpClient.get(ApiConfig.uri(path), headers: await _headers());
    });
  }

  Future<dynamic> postJson(String path, Map<String, dynamic> body) async {
    return _sendJson(() async {
      return _httpClient.post(
        ApiConfig.uri(path),
        headers: await _headers(jsonBody: true),
        body: jsonEncode(body),
      );
    });
  }

  Future<dynamic> putJson(String path, Map<String, dynamic> body) async {
    return _sendJson(() async {
      return _httpClient.put(
        ApiConfig.uri(path),
        headers: await _headers(jsonBody: true),
        body: jsonEncode(body),
      );
    });
  }

  Future<dynamic> postForm(String path, Map<String, String> fields) async {
    return _sendJson(() async {
      return _httpClient.post(
        ApiConfig.uri(path),
        headers: await _headers(),
        body: fields,
      );
    });
  }

  Future<dynamic> postMultipart({
    required String path,
    required String fileFieldName,
    required String filePath,
    Map<String, String> fields = const {},
  }) async {
    try {
      final request = http.MultipartRequest('POST', ApiConfig.uri(path));
      request.headers.addAll(await _headers());
      request.fields.addAll(fields);
      request.files.add(await http.MultipartFile.fromPath(fileFieldName, filePath));

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);
      return _parseResponse(response);
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(
        '서버에 연결할 수 없습니다. 주소와 네트워크 상태를 확인해 주세요. ($e)',
        kind: ApiExceptionKind.network,
      );
    }
  }

  Future<Map<String, String>> _headers({bool jsonBody = false}) async {
    final headers = <String, String>{};
    final token = await _tokenStorage.readToken();
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    if (jsonBody) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  }

  Future<dynamic> _sendJson(Future<http.Response> Function() request) async {
    try {
      final response = await request();
      return _parseResponse(response);
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(
        '서버에 연결할 수 없습니다. 주소와 네트워크 상태를 확인해 주세요. ($e)',
        kind: ApiExceptionKind.network,
      );
    }
  }

  dynamic _parseResponse(http.Response response) {
    if (response.statusCode == 401 || response.statusCode == 403) {
      throw const ApiException('로그인이 필요합니다.', kind: ApiExceptionKind.unauthorized);
    }
    if (response.statusCode == 404) {
      throw const ApiException('요청한 데이터를 찾을 수 없습니다.', kind: ApiExceptionKind.notFound);
    }
    if (response.statusCode >= 500) {
      throw ApiException(
        '서버 오류가 발생했습니다. (${response.statusCode})',
        kind: ApiExceptionKind.server,
      );
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        _extractErrorMessage(response),
        kind: ApiExceptionKind.unknown,
      );
    }
    if (response.body.trim().isEmpty) return null;
    try {
      return jsonDecode(utf8.decode(response.bodyBytes));
    } catch (_) {
      throw const ApiException(
        '서버 응답 형식이 올바르지 않습니다.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }
  }

  String _extractErrorMessage(http.Response response) {
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic>) {
        return decoded['message']?.toString() ??
            decoded['error']?.toString() ??
            '요청 처리에 실패했습니다. (${response.statusCode})';
      }
    } catch (_) {
      // JSON 오류 응답이 아니면 기본 메시지를 사용한다.
    }
    return '요청 처리에 실패했습니다. (${response.statusCode})';
  }
}