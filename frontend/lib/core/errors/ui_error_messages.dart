import '../services/api_client.dart';

/// Converts API exceptions into user-facing screen messages.
class UiErrorMessages {
  const UiErrorMessages._();

  static String login(Object error) => _message(
    error,
    connection: '서버에 연결할 수 없습니다. 서버 주소와 Spring 실행 상태를 확인해 주세요.',
    loginRequired: '로그인 정보가 올바르지 않습니다. 다시 시도해 주세요.',
    validation: '로그인 요청 형식이 서버와 맞지 않습니다.',
    server: '서버에서 로그인 처리 중 오류가 발생했습니다.',
    invalidResponse: '로그인 응답 형식이 올바르지 않습니다.',
    fallback: '로그인에 실패했습니다.',
  );

  static String saveHeight(Object error) => _message(
    error,
    connection: '서버에 연결할 수 없어 키 정보를 저장하지 못했습니다.',
    loginRequired: '로그인이 필요합니다. 다시 로그인한 뒤 키를 저장해 주세요.',
    validation: '키 저장 요청 값이 올바르지 않습니다.',
    server: '서버에서 키 정보를 저장하는 중 오류가 발생했습니다.',
    invalidResponse: '키 저장 응답 형식이 올바르지 않습니다.',
    fallback: '키 정보를 저장하지 못했습니다.',
  );

  static String loadClothes(Object error) => _message(
    error,
    connection: '서버에 연결할 수 없어 옷 목록을 불러오지 못했습니다.',
    loginRequired: '옷 목록을 보려면 로그인이 필요합니다.',
    notFound: '옷 목록 API를 찾을 수 없습니다.',
    server: '서버에서 옷 목록을 불러오는 중 오류가 발생했습니다.',
    invalidResponse: '옷 목록 응답 형식이 올바르지 않습니다.',
    fallback: '옷 목록을 불러오지 못했습니다.',
  );

  static String createFitting(Object error) => _message(
    error,
    connection: '서버에 연결할 수 없어 피팅 요청을 만들지 못했습니다.',
    loginRequired: '로그인이 필요합니다. 다시 로그인한 뒤 피팅을 요청해 주세요.',
    validation: '피팅 요청 값이 서버 기준과 맞지 않습니다.',
    notFound: '선택한 옷 정보를 찾을 수 없습니다.',
    server: '서버에서 피팅 요청을 처리하는 중 오류가 발생했습니다.',
    invalidResponse: '피팅 요청 응답 형식이 올바르지 않습니다.',
    fallback: '피팅 요청에 실패했습니다.',
  );

  static String loadFittingHistory(Object error) => _message(
    error,
    connection: '서버에 연결할 수 없어 피팅 기록을 불러오지 못했습니다.',
    loginRequired: '피팅 기록을 보려면 로그인이 필요합니다.',
    notFound: '피팅 기록 API를 찾을 수 없습니다.',
    server: '서버에서 피팅 기록을 불러오는 중 오류가 발생했습니다.',
    invalidResponse: '피팅 기록 응답 형식이 올바르지 않습니다.',
    fallback: '피팅 기록을 불러오지 못했습니다.',
  );

  static String _message(
    Object error, {
    required String connection,
    required String loginRequired,
    String? validation,
    String? notFound,
    required String server,
    required String invalidResponse,
    required String fallback,
  }) {
    if (error is ApiException) {
      switch (error.kind) {
        case ApiExceptionKind.connection:
          return connection;
        case ApiExceptionKind.loginRequired:
          return loginRequired;
        case ApiExceptionKind.validation:
          return validation ?? fallback;
        case ApiExceptionKind.notFound:
          return notFound ?? fallback;
        case ApiExceptionKind.server:
          return server;
        case ApiExceptionKind.invalidResponse:
          return invalidResponse;
        case ApiExceptionKind.unknown:
          return '$fallback\n${error.message}';
      }
    }
    return '$fallback\n$error';
  }
}
