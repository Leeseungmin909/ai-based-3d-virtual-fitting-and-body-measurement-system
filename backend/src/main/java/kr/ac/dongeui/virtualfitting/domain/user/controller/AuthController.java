package kr.ac.dongeui.virtualfitting.domain.user.controller;

import kr.ac.dongeui.virtualfitting.domain.user.dto.AuthResponse;
import kr.ac.dongeui.virtualfitting.domain.user.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Flutter mock 로그인 흐름에서 사용하는 인증 API를 제공한다.
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserService userService;

    public AuthController(UserService userService) {
        this.userService = userService;
    }

    /**
     * 이메일과 이름으로 사용자를 생성 또는 조회하고 JWT를 반환한다.
     */
    @PostMapping("/google")
    public ResponseEntity<AuthResponse> googleLogin(@RequestParam String email, @RequestParam String name) {
        UserService.LoginResult result = userService.googleLoginOrSignup(email, name);
        return ResponseEntity.ok(new AuthResponse(result.token(), result.user()));
    }
}
