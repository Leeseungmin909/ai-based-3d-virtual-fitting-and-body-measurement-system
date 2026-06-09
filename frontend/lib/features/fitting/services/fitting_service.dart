import '../../../core/services/api_client.dart';
import '../models/fitting_history_item.dart';
import '../models/fitting_result.dart';

/// 피팅 기록 생성, 목록 조회, 상태/결과 조회를 담당한다.
class FittingService {
  FittingService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<FittingCreateResult> createHistory({required int clothesId}) async {
    final response = await _apiClient.postJson('/api/fitting/history', {
      'clothesId': clothesId,
    });
    if (response is! Map<String, dynamic>) {
      throw const ApiException(
        'Fitting create response format is invalid.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }
    return FittingCreateResult.fromJson(response);
  }

  Future<List<FittingHistoryItem>> fetchHistory() async {
    final response = await _apiClient.getJson('/api/fitting/history');
    if (response is! List) {
      throw const ApiException(
        'Fitting history response format is invalid.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }
    return response
        .whereType<Map<String, dynamic>>()
        .map(FittingHistoryItem.fromJson)
        .toList();
  }

  Future<FittingResult> fetchResult(int fittingId) async {
    final response = await _apiClient.getJson('/api/fitting/history/$fittingId/result');
    if (response is! Map<String, dynamic>) {
      throw const ApiException(
        'Fitting result response format is invalid.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }
    return FittingResult.fromJson(response);
  }
}