package kr.ac.dongeui.virtualfitting.domain.user.controller;

import kr.ac.dongeui.virtualfitting.domain.user.dto.AuthResponse;
import kr.ac.dongeui.virtualfitting.domain.user.dto.LoginRequest;
import kr.ac.dongeui.virtualfitting.domain.user.dto.SignUpRequest;
import kr.ac.dongeui.virtualfitting.domain.user.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
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
     * 이메일/비밀번호로 회원가입하고 JWT를 반환한다.
     */
    @PostMapping("/signup")
    public ResponseEntity<AuthResponse> signup(@RequestBody SignUpRequest request) {
        UserService.LoginResult result = userService.signup(request.email(), request.name(), request.password());
        return ResponseEntity.ok(new AuthResponse(result.token(), result.user()));
    }

    /**
     * 이메일/비밀번호로 로그인하고 JWT를 반환한다.
     */
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody LoginRequest request) {
        UserService.LoginResult result = userService.login(request.email(), request.password());
        return ResponseEntity.ok(new AuthResponse(result.token(), result.user()));
    }

    /**
     * 이메일과 이름으로 사용자를 생성 또는 조회하고 JWT를 반환한다. (테스트용 mock)
     */
    @PostMapping("/google")
    public ResponseEntity<AuthResponse> googleLogin(@RequestParam String email, @RequestParam String name) {
        UserService.LoginResult result = userService.googleLoginOrSignup(email, name);
        return ResponseEntity.ok(new AuthResponse(result.token(), result.user()));
    }
}
