import '../../../core/services/api_client.dart';
import '../models/clothes.dart';

/// Fetches clothes from Spring and converts them into Flutter models.
class ClothesService {
  ClothesService({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  /// Loads the clothes list shown on the clothes selection screen.
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
