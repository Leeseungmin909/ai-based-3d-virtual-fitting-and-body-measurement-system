package kr.ac.dongeui.virtualfitting.domain.user.controller;

import kr.ac.dongeui.virtualfitting.domain.user.dto.UserBodyInfoRequest;
import kr.ac.dongeui.virtualfitting.domain.user.dto.UserBodyInfoResponse;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 현재 사용자의 기본 신체 정보를 수정하는 API를 제공한다.
 */
@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    /**
     * 현재 사용자의 키를 저장하고 치수 정보와 동기화한다.
     */
    @PutMapping("/me/body-info")
    public ResponseEntity<UserBodyInfoResponse> updateMyBodyInfo(
            Authentication authentication,
            @RequestBody UserBodyInfoRequest request) {
        User user = userService.updateHeight(authentication.getName(), request.getHeightCm());
        return ResponseEntity.ok(new UserBodyInfoResponse(user));
    }
}
