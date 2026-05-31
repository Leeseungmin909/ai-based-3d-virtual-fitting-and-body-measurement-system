package kr.ac.dongeui.virtualfitting.domain.measurement.controller;

import kr.ac.dongeui.virtualfitting.domain.measurement.dto.UserMeasurementResponse;
import kr.ac.dongeui.virtualfitting.domain.measurement.dto.UserMeasurementUpsertRequest;
import kr.ac.dongeui.virtualfitting.domain.measurement.service.UserMeasurementService;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 사용자 신체 치수 저장과 조회 API를 제공한다.
 */
@RestController
@RequestMapping("/api/users")
public class UserMeasurementController {

    private final UserMeasurementService measurementService;
    private final UserRepository userRepository;

    public UserMeasurementController(UserMeasurementService measurementService, UserRepository userRepository) {
        this.measurementService = measurementService;
        this.userRepository = userRepository;
    }

    /**
     * 관리자 또는 테스트 용도로 특정 사용자 ID의 치수 정보를 조회한다.
     */
    @GetMapping("/{userId}/measurements")
    public ResponseEntity<UserMeasurementResponse> getUserMeasurements(@PathVariable Long userId) {
        return ResponseEntity.ok(measurementService.getByUserId(userId));
    }

    /**
     * 특정 사용자 ID의 치수 정보를 생성하거나 갱신한다.
     */
    @PutMapping("/{userId}/measurements")
    public ResponseEntity<UserMeasurementResponse> upsertUserMeasurements(
            @PathVariable Long userId,
            @RequestBody UserMeasurementUpsertRequest request) {
        return ResponseEntity.ok(measurementService.upsertByUserId(userId, request));
    }

    /**
     * 현재 인증된 사용자의 치수 정보를 조회한다.
     */
    @GetMapping("/me/measurements")
    public ResponseEntity<UserMeasurementResponse> getMyMeasurements(Authentication authentication) {
        User user = getAuthenticatedUser(authentication);
        return ResponseEntity.ok(measurementService.getByUserId(user.getId()));
    }

    /**
     * 현재 인증된 사용자의 치수 정보를 생성하거나 갱신한다.
     */
    @PutMapping("/me/measurements")
    public ResponseEntity<UserMeasurementResponse> upsertMyMeasurements(
            Authentication authentication,
            @RequestBody UserMeasurementUpsertRequest request) {
        User user = getAuthenticatedUser(authentication);
        return ResponseEntity.ok(measurementService.upsertByUserId(user.getId(), request));
    }

    /**
     * Spring Security 인증 정보에서 현재 사용자를 조회한다.
     */
    private User getAuthenticatedUser(Authentication authentication) {
        return userRepository.findByEmail(authentication.getName())
                .orElseThrow(() -> new IllegalArgumentException("User not found."));
    }
}
