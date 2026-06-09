package kr.ac.dongeui.virtualfitting.domain.fitting.dto;

import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import lombok.Getter;

import java.time.format.DateTimeFormatter;

@Getter
public class FittingHistoryResponse {
    private final Long id;
    private final Long clothesId;
    private final String clothesName;
    private final String fittingDate;
    private final String createdAt;
    private final String status;
    private final String aiJobId;
    private final String avatarGlbUrl;
    private final String renderImageUrl;
    private final String resultJsonUrl;

    public FittingHistoryResponse(FittingHistory history) {
        this.id = history.getId();
        this.clothesId = history.getClothes().getId();
        this.clothesName = history.getClothes().getName();
        this.fittingDate = history.getCreatedAt() != null
                ? history.getCreatedAt().format(DateTimeFormatter.ISO_LOCAL_DATE)
                : null;
        this.createdAt = history.getCreatedAt() != null
                ? history.getCreatedAt().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                : null;
        this.status = history.getStatus() != null ? history.getStatus().name() : "PENDING";
        this.aiJobId = history.getAiJobId();
        this.avatarGlbUrl = history.getAvatarGlbUrl();
        this.renderImageUrl = history.getRenderImageUrl();
        this.resultJsonUrl = history.getResultJsonUrl();
    }
}