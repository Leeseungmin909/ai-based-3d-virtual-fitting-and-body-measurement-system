package kr.ac.dongeui.virtualfitting.domain.fitting.controller;

import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingCreateRequest;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingCreateResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingHistoryResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingResultResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import kr.ac.dongeui.virtualfitting.domain.fitting.service.FittingService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

/**
 * 피팅 요청 생성, 상태 조회, 결과 조회, AI 완료 콜백 처리를 담당하는 컨트롤러입니다.
 */
@RestController
@RequestMapping("/api/fitting")
public class FittingController {

    private final FittingService fittingService;

    public FittingController(FittingService fittingService) {
        this.fittingService = fittingService;
    }

    /**
     * 현재 로그인한 사용자의 피팅 기록을 최신순으로 조회합니다.
     */
    @GetMapping("/history")
    public ResponseEntity<List<FittingHistoryResponse>> getMyFittingHistory(Authentication authentication) {
        return ResponseEntity.ok(fittingService.getMyFittingHistory(authentication.getName()));
    }

    /**
     * 특정 피팅 작업의 현재 상태와 결과 URL을 조회합니다.
     */
    @GetMapping("/history/{fittingId}")
    public ResponseEntity<FittingHistoryResponse> getFittingHistoryDetail(
            Authentication authentication,
            @PathVariable Long fittingId) {
        return ResponseEntity.ok(fittingService.getMyFittingHistoryDetail(authentication.getName(), fittingId));
    }

    /**
     * 결과 화면에서 사용할 GLB, 렌더 이미지, 결과 JSON URL을 조회합니다.
     */
    @GetMapping("/history/{fittingId}/result")
    public ResponseEntity<FittingResultResponse> getFittingResult(
            Authentication authentication,
            @PathVariable Long fittingId) {
        return ResponseEntity.ok(fittingService.getMyFittingResult(authentication.getName(), fittingId));
    }

    /**
     * 선택한 옷에 대해 PENDING 상태의 피팅 요청을 생성합니다.
     */
    @PostMapping("/history")
    public ResponseEntity<FittingCreateResponse> requestVirtualFitting(
            Authentication authentication,
            @RequestBody FittingCreateRequest request) {
        FittingHistory history = fittingService.requestFitting(authentication.getName(), request.getClothesId());
        return ResponseEntity.ok(new FittingCreateResponse(history));
    }

    /**
     * AI 파이프라인이 완료되면 결과 모델과 렌더 이미지 URL을 저장합니다.
     */
    @PostMapping("/webhook/complete")
    public ResponseEntity<Map<String, String>> completeVirtualFitting(@RequestBody Map<String, Object> requestData) {
        Long fittingId = ((Number) requestData.get("fittingId")).longValue();
        String aiJobId = (String) requestData.get("aiJobId");
        String avatarGlbUrl = (String) requestData.get("avatarGlbUrl");
        String renderImageUrl = (String) requestData.get("renderImageUrl");
        String resultJsonUrl = (String) requestData.get("resultJsonUrl");

        fittingService.completeFitting(fittingId, aiJobId, avatarGlbUrl, renderImageUrl, resultJsonUrl);
        return ResponseEntity.ok(Map.of("message", "Fitting result updated successfully."));
    }
}
