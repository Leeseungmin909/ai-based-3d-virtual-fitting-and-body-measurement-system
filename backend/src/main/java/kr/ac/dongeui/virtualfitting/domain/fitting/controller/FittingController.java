package kr.ac.dongeui.virtualfitting.domain.fitting.controller;

import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingCreateRequest;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingCreateResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingHistoryResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import kr.ac.dongeui.virtualfitting.domain.fitting.service.FittingService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

/**
 * 피팅 요청 생성, 기록 조회, AI 완료 콜백을 처리한다.
 */
@RestController
@RequestMapping("/api/fitting")
public class FittingController {

    private final FittingService fittingService;

    public FittingController(FittingService fittingService) {
        this.fittingService = fittingService;
    }

    /**
     * 현재 사용자의 피팅 기록을 최신순으로 반환한다.
     */
    @GetMapping("/history")
    public ResponseEntity<List<FittingHistoryResponse>> getMyFittingHistory(Authentication authentication) {
        return ResponseEntity.ok(fittingService.getMyFittingHistory(authentication.getName()));
    }

    /**
     * 선택한 옷에 대해 PENDING 상태의 피팅 요청을 생성한다.
     */
    @PostMapping("/history")
    public ResponseEntity<FittingCreateResponse> requestVirtualFitting(
            Authentication authentication,
            @RequestBody FittingCreateRequest request) {
        FittingHistory history = fittingService.requestFitting(authentication.getName(), request.getClothesId());
        return ResponseEntity.ok(new FittingCreateResponse(history));
    }

    /**
     * AI 파이프라인이 완료를 보고하면 결과 URL을 저장한다.
     */
    @PostMapping("/webhook/complete")
    public ResponseEntity<Map<String, String>> completeVirtualFitting(@RequestBody Map<String, Object> requestData) {
        Long fittingId = ((Number) requestData.get("fittingId")).longValue();
        String resultSplatUrl = (String) requestData.get("resultSplatUrl");
        fittingService.completeFitting(fittingId, resultSplatUrl);
        return ResponseEntity.ok(Map.of("message", "Fitting result updated successfully."));
    }
}
