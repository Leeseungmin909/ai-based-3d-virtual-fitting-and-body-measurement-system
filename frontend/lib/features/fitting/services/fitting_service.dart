import '../../../core/services/api_client.dart';
import '../models/fitting_history_item.dart';

/// 피팅 기록 조회와 피팅 요청 생성 API를 감싼다.
class FittingService {
  FittingService({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  /// 현재 로그인한 사용자의 피팅 기록을 조회한다.
  Future<List<FittingHistoryItem>> fetchHistory() async {
    final response = await _apiClient.getJson(
      '/api/fitting/history',
      authorized: true,
    );
    if (response == null) return const [];

    final List<dynamic> items;
    if (response is List) {
      items = response;
    } else if (response is Map<String, dynamic> && response['data'] is List) {
      items = response['data'] as List;
    } else {
      throw const ApiException(
        'Fitting history response format is invalid.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }

    return items
        .whereType<Map<String, dynamic>>()
        .map(FittingHistoryItem.fromJson)
        .toList();
  }

  /// 선택한 옷 ID로 피팅 요청 기록을 생성한다.
  Future<void> createHistory(int clothesId) async {
    await _apiClient.postJson('/api/fitting/history', {
      'clothesId': clothesId,
    }, authorized: true);
  }
}
