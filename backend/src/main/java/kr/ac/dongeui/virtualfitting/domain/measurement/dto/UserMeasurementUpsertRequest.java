package kr.ac.dongeui.virtualfitting.domain.measurement.dto;

import lombok.Getter;

@Getter
public class UserMeasurementUpsertRequest {
    private Double heightCm;
    private Double shoulderWidthCm;
    private Double chestWidthCm;
    private Double sleeveLengthCm;
    private Double waistWidthCm;
    private Double hipWidthCm;
    private Double thighWidthCm;
    private Double crotchCm;
    private String sourceImageUrl;
    private String smplMeshUrl;
    private String resultJsonUrl;
}