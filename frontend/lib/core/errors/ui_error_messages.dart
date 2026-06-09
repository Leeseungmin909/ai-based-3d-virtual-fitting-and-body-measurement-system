import '../services/api_client.dart';

/// 예외 종류를 화면에서 이해하기 쉬운 한글 메시지로 바꾼다.
class UiErrorMessages {
  const UiErrorMessages._();

  static String login(Object error) => _message(error, '로그인에 실패했습니다.');
  static String signUp(Object error) => _message(error, '회원가입에 실패했습니다.');
  static String saveHeight(Object error) => _message(error, '키 저장에 실패했습니다.');
  static String uploadSourceImage(Object error) => _message(error, '사진 업로드에 실패했습니다.');
  static String loadClothes(Object error) => _message(error, '옷 목록을 불러오지 못했습니다.');
  static String createFitting(Object error) => _message(error, '피팅 요청 생성에 실패했습니다.');
  static String loadFittingHistory(Object error) => _message(error, '피팅 기록을 불러오지 못했습니다.');
  static String loadFittingResult(Object error) => _message(error, '피팅 결과를 불러오지 못했습니다.');

  static String _message(Object error, String fallback) {
    if (error is ApiException) {
      switch (error.kind) {
        case ApiExceptionKind.network:
          return '서버 연결에 실패했습니다. 서버 주소와 실행 상태를 확인해 주세요.';
        case ApiExceptionKind.unauthorized:
          return '로그인이 필요합니다. 다시 로그인해 주세요.';
        case ApiExceptionKind.notFound:
          return '요청한 데이터가 없습니다.';
        case ApiExceptionKind.server:
          return '서버 내부 오류가 발생했습니다. Spring 로그를 확인해 주세요.';
        case ApiExceptionKind.invalidResponse:
          return '서버 응답 형식이 Flutter와 맞지 않습니다.';
        case ApiExceptionKind.unknown:
          return '$fallback\n${error.message}';
      }
    }
    return '$fallback\n$error';
  }
}