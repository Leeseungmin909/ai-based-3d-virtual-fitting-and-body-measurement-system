package kr.ac.dongeui.virtualfitting.domain.measurement.dto;

import kr.ac.dongeui.virtualfitting.domain.measurement.entity.UserMeasurement;
import lombok.Getter;

@Getter
public class UserMeasurementResponse {
    private final Long id;
    private final Long userId;
    private final Double heightCm;
    private final Double shoulderWidthCm;
    private final Double chestWidthCm;
    private final Double sleeveLengthCm;
    private final Double waistWidthCm;
    private final Double hipWidthCm;
    private final Double thighWidthCm;
    private final Double crotchCm;
    private final String sourceVideoUrl;
    private final String smplMeshUrl;
    private final String resultJsonUrl;

    public UserMeasurementResponse(UserMeasurement measurement) {
        this.id = measurement.getId();
        this.userId = measurement.getUser().getId();
        this.heightCm = measurement.getHeightCm();
        this.shoulderWidthCm = measurement.getShoulderWidthCm();
        this.chestWidthCm = measurement.getChestWidthCm();
        this.sleeveLengthCm = measurement.getSleeveLengthCm();
        this.waistWidthCm = measurement.getWaistWidthCm();
        this.hipWidthCm = measurement.getHipWidthCm();
        this.thighWidthCm = measurement.getThighWidthCm();
        this.crotchCm = measurement.getCrotchCm();
        this.sourceVideoUrl = measurement.getSourceVideoUrl();
        this.smplMeshUrl = measurement.getSmplMeshUrl();
        this.resultJsonUrl = measurement.getResultJsonUrl();
    }
}