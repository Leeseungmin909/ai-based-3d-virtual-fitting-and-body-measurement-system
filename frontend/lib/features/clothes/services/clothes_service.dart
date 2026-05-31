import '../../../core/services/api_client.dart';
import '../models/clothes.dart';

/// Spring에서 옷 목록을 받아 Flutter 모델로 변환한다.
class ClothesService {
  ClothesService({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  /// 옷 선택 화면에 표시할 옷 목록을 불러온다.
  Future<List<Clothes>> fetchClothes() async {
    final response = await _apiClient.getJson('/api/clothes');
    if (response is! List) {
      throw const ApiException(
        'Clothes response format is invalid.',
        kind: ApiExceptionKind.invalidResponse,
      );
    }
    return response
        .whereType<Map<String, dynamic>>()
        .map(Clothes.fromJson)
        .toList();
  }
}
