package kr.ac.dongeui.virtualfitting.domain.user.dto;

/**
 * 이메일/비밀번호 로그인 요청 본문이다.
 */
public record LoginRequest(String email, String password) {
}
