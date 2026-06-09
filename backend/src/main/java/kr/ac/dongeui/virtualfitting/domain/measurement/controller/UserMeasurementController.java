package kr.ac.dongeui.virtualfitting.domain.measurement.controller;

import kr.ac.dongeui.virtualfitting.domain.measurement.dto.UserMeasurementResponse;
import kr.ac.dongeui.virtualfitting.domain.measurement.dto.UserMeasurementUpsertRequest;
import kr.ac.dongeui.virtualfitting.domain.measurement.service.UserMeasurementService;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import kr.ac.dongeui.virtualfitting.global.infra.file.LocalFileStorageService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

/**
 * 사용자 신체 치수 저장, 조회, 원본 이미지 업로드 API를 제공한다.
 */
@RestController
@RequestMapping("/api/users")
public class UserMeasurementController {

    private final UserMeasurementService measurementService;
    private final UserRepository userRepository;
    private final LocalFileStorageService localFileStorageService;

    public UserMeasurementController(UserMeasurementService measurementService,
                                     UserRepository userRepository,
                                     LocalFileStorageService localFileStorageService) {
        this.measurementService = measurementService;
        this.userRepository = userRepository;
        this.localFileStorageService = localFileStorageService;
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
     * AI 처리에 사용할 원본 전신 이미지를 로컬 저장소에 저장하고 source_image_url에 반영한다.
     */
    @PostMapping("/me/source-image")
    public ResponseEntity<UserMeasurementResponse> uploadMySourceImage(
            Authentication authentication,
            @RequestParam("file") MultipartFile file) {
        User user = getAuthenticatedUser(authentication);
        try {
            String fileUrl = localFileStorageService.uploadFile(file, "measurements/" + user.getId() + "/source-images");
            return ResponseEntity.ok(measurementService.updateSourceImageUrl(user.getId(), fileUrl));
        } catch (IOException e) {
            throw new IllegalStateException("Source image upload failed.", e);
        }
    }

    /**
     * Spring Security 인증 정보에서 현재 사용자를 조회한다.
     */
    private User getAuthenticatedUser(Authentication authentication) {
        return userRepository.findByEmail(authentication.getName())
                .orElseThrow(() -> new IllegalArgumentException("User not found."));
    }
}