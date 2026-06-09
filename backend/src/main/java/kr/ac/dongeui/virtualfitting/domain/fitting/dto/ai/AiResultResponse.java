package kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Collections;
import java.util.List;

@Getter
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiResultResponse {
    @JsonProperty("job_id")
    private String jobId;

    private String status;

    @JsonProperty("measurements_cm")
    private AiMeasurementsCm measurementsCm;

    @JsonProperty("smpl_mesh_url")
    private String smplMeshUrl;

    @JsonProperty("avatar_glb_url")
    private String avatarGlbUrl;

    @JsonProperty("render_urls")
    private List<String> renderUrls = Collections.emptyList();

    @JsonProperty("result_json_url")
    private String resultJsonUrl;

    public String getPrimaryRenderImageUrl() {
        if (renderUrls == null || renderUrls.isEmpty()) {
            return null;
        }
        return renderUrls.get(0);
    }
}