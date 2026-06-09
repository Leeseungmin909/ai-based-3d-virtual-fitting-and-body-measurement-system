package kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Collections;
import java.util.List;

@Getter
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiClothesLibraryResponse {
    private List<String> tops = Collections.emptyList();
    private List<String> bottoms = Collections.emptyList();
}