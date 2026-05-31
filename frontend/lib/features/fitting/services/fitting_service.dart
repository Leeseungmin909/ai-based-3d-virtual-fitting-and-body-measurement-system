import '../../../core/services/api_client.dart';
import '../models/fitting_history_item.dart';

/// ?? ?? ??? ?? ?? ?? API? ???.
class FittingService {
  FittingService({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  /// ?? ???? ???? ?? ??? ????.
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

  /// ??? ?? ID? ?? ?? ??? ????.
  Future<void> createHistory(int clothesId) async {
    await _apiClient.postJson('/api/fitting/history', {
      'clothesId': clothesId,
    }, authorized: true);
  }
}
