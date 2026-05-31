package kr.ac.dongeui.virtualfitting.domain.fitting.dto;

import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import lombok.Getter;

@Getter
public class FittingCreateResponse {
    private final Long fittingId;
    private final Long clothesId;
    private final String status;
    private final String message;

    public FittingCreateResponse(FittingHistory history) {
        this.fittingId = history.getId();
        this.clothesId = history.getClothes().getId();
        this.status = history.getStatus().name();
        this.message = "Fitting request created successfully.";
    }
}
