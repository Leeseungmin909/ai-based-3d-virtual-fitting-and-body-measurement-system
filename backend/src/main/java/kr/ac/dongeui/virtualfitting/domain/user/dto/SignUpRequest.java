package kr.ac.dongeui.virtualfitting.domain.user.dto;

/**
 * 이메일/비밀번호 회원가입 요청 본문이다.
 */
public record SignUpRequest(String email, String name, String password) {
}
