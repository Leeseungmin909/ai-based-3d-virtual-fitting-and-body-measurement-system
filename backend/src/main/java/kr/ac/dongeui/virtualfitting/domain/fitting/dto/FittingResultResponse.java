package kr.ac.dongeui.virtualfitting.domain.fitting.dto;

import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingStatus;
import lombok.Getter;

@Getter
public class FittingResultResponse {
    private final Long fittingId;
    private final String status;
    private final boolean ready;
    private final String aiJobId;
    private final String avatarGlbUrl;
    private final String renderImageUrl;
    private final String resultJsonUrl;
    private final String message;

    /**
     * 피팅 결과 화면에서 필요한 결과 URL과 완료 여부를 반환합니다.
     */
    public FittingResultResponse(FittingHistory history) {
        this.fittingId = history.getId();
        FittingStatus fittingStatus = history.getStatus() != null ? history.getStatus() : FittingStatus.PENDING;
        this.status = fittingStatus.name();
        this.aiJobId = history.getAiJobId();
        this.avatarGlbUrl = history.getAvatarGlbUrl();
        this.renderImageUrl = history.getRenderImageUrl();
        this.resultJsonUrl = history.getResultJsonUrl();
        this.ready = fittingStatus == FittingStatus.SUCCESS && history.getAvatarGlbUrl() != null;
        this.message = createMessage(fittingStatus);
    }

    /**
     * Flutter 화면에서 상태별 안내 문구를 분기할 수 있도록 기본 메시지를 제공합니다.
     */
    private String createMessage(FittingStatus status) {
        return switch (status) {
            case PENDING -> "피팅 요청이 접수되었습니다.";
            case PROCESSING -> "AI 피팅 결과를 생성하는 중입니다.";
            case SUCCESS -> "피팅 결과가 준비되었습니다.";
            case FAIL -> "피팅 결과 생성에 실패했습니다.";
        };
    }
}