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
 * AI 결과 JSON 또는 Flutter 입력값으로 사용자 신체 치수를 저장한다.
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
     * 사용자 신체 치수 기록을 생성하거나 갱신한다.
     */
    public UserMeasurementResponse upsertByUserId(Long userId, UserMeasurementUpsertRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));

        if (request.getHeightCm() == null) {
            throw new IllegalArgumentException("heightCm is required.");
        }

        UserMeasurement measurement = measurementRepository.findByUserId(userId)
                .orElseGet(() -> {
                    UserMeasurement created = new UserMeasurement();
                    created.setUser(user);
                    return created;
                });

        measurement.setHeightCm(request.getHeightCm());
        measurement.setShoulderWidthCm(request.getShoulderWidthCm());
        measurement.setChestWidthCm(request.getChestWidthCm());
        measurement.setSleeveLengthCm(request.getSleeveLengthCm());
        measurement.setWaistWidthCm(request.getWaistWidthCm());
        measurement.setHipWidthCm(request.getHipWidthCm());
        measurement.setThighWidthCm(request.getThighWidthCm());
        measurement.setCrotchCm(request.getCrotchCm());
        measurement.setSourceVideoUrl(request.getSourceVideoUrl());
        measurement.setSmplMeshUrl(request.getSmplMeshUrl());
        measurement.setResultJsonUrl(request.getResultJsonUrl());

        user.setHeightCm(request.getHeightCm());
        UserMeasurement saved = measurementRepository.save(measurement);
        return new UserMeasurementResponse(saved);
    }
}
