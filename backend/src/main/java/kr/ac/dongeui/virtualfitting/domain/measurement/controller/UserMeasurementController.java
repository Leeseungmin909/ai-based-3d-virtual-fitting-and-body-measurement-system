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
 * ???? ?? ?? ??? ?? API? ????.
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
     * ???? ?????? ?? ??? ID? ???? ????.
     */
    @GetMapping("/{userId}/measurements")
    public ResponseEntity<UserMeasurementResponse> getUserMeasurements(@PathVariable Long userId) {
        return ResponseEntity.ok(measurementService.getByUserId(userId));
    }

    /**
     * ?? ??? ID? ???? ????? ????.
     */
    @PutMapping("/{userId}/measurements")
    public ResponseEntity<UserMeasurementResponse> upsertUserMeasurements(
            @PathVariable Long userId,
            @RequestBody UserMeasurementUpsertRequest request) {
        return ResponseEntity.ok(measurementService.upsertByUserId(userId, request));
    }

    /**
     * JWT ?? ?? ???? ???? ????.
     */
    @GetMapping("/me/measurements")
    public ResponseEntity<UserMeasurementResponse> getMyMeasurements(Authentication authentication) {
        User user = getAuthenticatedUser(authentication);
        return ResponseEntity.ok(measurementService.getByUserId(user.getId()));
    }

    /**
     * JWT ?? ?? ???? ???? ????? ????.
     */
    @PutMapping("/me/measurements")
    public ResponseEntity<UserMeasurementResponse> upsertMyMeasurements(
            Authentication authentication,
            @RequestBody UserMeasurementUpsertRequest request) {
        User user = getAuthenticatedUser(authentication);
        return ResponseEntity.ok(measurementService.upsertByUserId(user.getId(), request));
    }

    /**
     * Spring Security ?? ???? ?? ???? ????.
     */
    private User getAuthenticatedUser(Authentication authentication) {
        return userRepository.findByEmail(authentication.getName())
                .orElseThrow(() -> new IllegalArgumentException("User not found."));
    }
}