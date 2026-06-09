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
public class AiRendersResponse {
    private List<String> renders = Collections.emptyList();

    @JsonProperty("avatar_glb")
    private String avatarGlbUrl;

    public String getPrimaryRenderImageUrl() {
        if (renders == null || renders.isEmpty()) {
            return null;
        }
        return renders.get(0);
    }
}