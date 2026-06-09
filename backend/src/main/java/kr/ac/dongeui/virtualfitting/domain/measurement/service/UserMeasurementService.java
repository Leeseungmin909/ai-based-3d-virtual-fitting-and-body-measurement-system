package kr.ac.dongeui.virtualfitting.domain.measurement.service;

import kr.ac.dongeui.virtualfitting.domain.measurement.dto.UserMeasurementResponse;
import kr.ac.dongeui.virtualfitting.domain.measurement.dto.UserMeasurementUpsertRequest;
import kr.ac.dongeui.virtualfitting.domain.measurement.entity.UserMeasurement;
import kr.ac.dongeui.virtualfitting.domain.measurement.repository.UserMeasurementRepository;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 사용자 신체 치수와 AI 처리 결과 경로를 저장하고 조회한다.
 */
@Service
@Transactional
public class UserMeasurementService {

    private final UserMeasurementRepository measurementRepository;
    private final UserRepository userRepository;

    public UserMeasurementService(UserMeasurementRepository measurementRepository, UserRepository userRepository) {
        this.measurementRepository = measurementRepository;
        this.userRepository = userRepository;
    }

    /**
     * 사용자 ID로 신체 치수 기록을 조회한다.
     */
    @Transactional(readOnly = true)
    public UserMeasurementResponse getByUserId(Long userId) {
        UserMeasurement measurement = measurementRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("User measurement not found."));
        return new UserMeasurementResponse(measurement);
    }

    /**
     * Flutter 입력값 또는 AI 결과값으로 사용자 신체 치수 기록을 생성하거나 갱신한다.
     */
    public UserMeasurementResponse upsertByUserId(Long userId, UserMeasurementUpsertRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));

        if (request.getHeightCm() == null) {
            throw new IllegalArgumentException("heightCm is required.");
        }

        UserMeasurement measurement = measurementRepository.findByUserId(userId)
                .orElseGet(() -> createMeasurement(user));

        measurement.setHeightCm(request.getHeightCm());
        measurement.setShoulderWidthCm(request.getShoulderWidthCm());
        measurement.setChestWidthCm(request.getChestWidthCm());
        measurement.setSleeveLengthCm(request.getSleeveLengthCm());
        measurement.setWaistWidthCm(request.getWaistWidthCm());
        measurement.setHipWidthCm(request.getHipWidthCm());
        measurement.setThighWidthCm(request.getThighWidthCm());
        measurement.setCrotchCm(request.getCrotchCm());
        measurement.setSourceImageUrl(request.getSourceImageUrl());
        measurement.setSmplMeshUrl(request.getSmplMeshUrl());
        measurement.setResultJsonUrl(request.getResultJsonUrl());

        user.setHeightCm(request.getHeightCm());
        UserMeasurement saved = measurementRepository.save(measurement);
        return new UserMeasurementResponse(saved);
    }

    /**
     * 원본 전신 이미지 업로드 후 공개 URL을 user_measurements.source_image_url에 저장한다.
     */
    public UserMeasurementResponse updateSourceImageUrl(Long userId, String sourceImageUrl) {
        if (sourceImageUrl == null || sourceImageUrl.isBlank()) {
            throw new IllegalArgumentException("sourceImageUrl is required.");
        }

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));

        UserMeasurement measurement = measurementRepository.findByUserId(userId)
                .orElseGet(() -> createMeasurement(user));

        if (measurement.getHeightCm() == null) {
            if (user.getHeightCm() == null) {
                throw new IllegalArgumentException("heightCm must be saved before source image upload.");
            }
            measurement.setHeightCm(user.getHeightCm());
        }

        measurement.setSourceImageUrl(sourceImageUrl);
        UserMeasurement saved = measurementRepository.save(measurement);
        return new UserMeasurementResponse(saved);
    }

    /**
     * 신규 신체 치수 엔티티를 만들고 사용자와 연결한다.
     */
    private UserMeasurement createMeasurement(User user) {
        UserMeasurement created = new UserMeasurement();
        created.setUser(user);
        return created;
    }
}