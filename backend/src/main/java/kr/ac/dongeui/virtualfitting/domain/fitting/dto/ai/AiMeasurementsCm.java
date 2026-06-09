package kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiMeasurementsCm {
    @JsonProperty("height_cm")
    private Double heightCm;

    @JsonProperty("shoulder_width_cm")
    private Double shoulderWidthCm;

    @JsonProperty("chest_width_cm")
    private Double chestWidthCm;

    @JsonProperty("sleeve_length_cm")
    private Double sleeveLengthCm;

    @JsonProperty("waist_width_cm")
    private Double waistWidthCm;

    @JsonProperty("hip_width_cm")
    private Double hipWidthCm;

    @JsonProperty("thigh_width_cm")
    private Double thighWidthCm;

    @JsonProperty("crotch_cm")
    private Double crotchCm;
}