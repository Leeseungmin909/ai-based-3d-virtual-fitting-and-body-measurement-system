package kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiJobStatusResponse {
    @JsonProperty("job_id")
    private String jobId;

    private String status;
    private Integer progress;
    private String step;
    private String message;
    private String error;

    @JsonProperty("avatar_glb")
    private String avatarGlbUrl;

    @JsonProperty("result_json_url")
    private String resultJsonUrl;

    public boolean isCompleted() {
        if (status == null) {
            return false;
        }
        return status.equalsIgnoreCase("done")
                || status.equalsIgnoreCase("completed")
                || status.equalsIgnoreCase("success");
    }

    public boolean isFailed() {
        if (status == null) {
            return false;
        }
        return status.equalsIgnoreCase("fail")
                || status.equalsIgnoreCase("failed")
                || status.equalsIgnoreCase("error");
    }
}