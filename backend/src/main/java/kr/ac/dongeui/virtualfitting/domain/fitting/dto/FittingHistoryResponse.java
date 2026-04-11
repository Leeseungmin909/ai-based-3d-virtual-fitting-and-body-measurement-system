package kr.ac.dongeui.virtualfitting.domain.fitting.dto;

import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import lombok.Getter;

import java.time.format.DateTimeFormatter;

@Getter
public class FittingHistoryResponse {
    private Long id;
    private String clothesName;
    private String fittingDate;
    private String status;
    private String resultUrl;

    public FittingHistoryResponse(FittingHistory history) {
        this.id = history.getId();
        this.clothesName = history.getClothes().getName();

        this.fittingDate = history.getCreatedAt() != null ?
                history.getCreatedAt().format(DateTimeFormatter.ofPattern("yyyy-MM-dd")) : "오늘";

        String rawStatus = history.getStatus() != null ? history.getStatus().name() : "PENDING";
        if (rawStatus.equals("PENDING")) this.status = "피팅 진행중..";
        else if (rawStatus.equals("COMPLETED")) this.status = "피팅 완료";
        else this.status = "에러 발생";

        this.resultUrl = history.getResultSplatUrl();
    }
}