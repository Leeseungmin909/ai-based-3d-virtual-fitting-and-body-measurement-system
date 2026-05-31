package kr.ac.dongeui.virtualfitting.domain.user.controller;

import kr.ac.dongeui.virtualfitting.domain.user.dto.AuthResponse;
import kr.ac.dongeui.virtualfitting.domain.user.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Flutter mock login flow?? ??? ?? API? ????.
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserService userService;

    public AuthController(UserService userService) {
        this.userService = userService;
    }

    /**
     * ???? ???? ???? ????? ??? ? JWT? ????.
     */
    @PostMapping("/google")
    public ResponseEntity<AuthResponse> googleLogin(@RequestParam String email, @RequestParam String name) {
        UserService.LoginResult result = userService.googleLoginOrSignup(email, name);
        return ResponseEntity.ok(new AuthResponse(result.token(), result.user()));
    }
}
