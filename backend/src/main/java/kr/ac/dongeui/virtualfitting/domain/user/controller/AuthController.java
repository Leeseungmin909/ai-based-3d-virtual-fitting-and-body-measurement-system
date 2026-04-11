package kr.ac.dongeui.virtualfitting.domain.user.controller;

import kr.ac.dongeui.virtualfitting.domain.user.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserService userService;

    public AuthController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping("/google")
    public ResponseEntity<Map<String, String>> googleLogin(@RequestParam String email, @RequestParam String name) {
        String token = userService.googleLoginOrSignup(email, name);
        Map<String, String> response = new HashMap<>();
        response.put("token", token);
        return ResponseEntity.ok(response);
    }
}