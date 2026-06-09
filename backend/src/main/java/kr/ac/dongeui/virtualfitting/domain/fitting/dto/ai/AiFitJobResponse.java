package kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiFitJobResponse {
    @JsonProperty("job_id")
    private String jobId;

    private String status;
}