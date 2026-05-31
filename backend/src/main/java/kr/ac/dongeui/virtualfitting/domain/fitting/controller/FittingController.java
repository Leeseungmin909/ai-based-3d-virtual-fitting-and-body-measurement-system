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
 * ?? ?? ??, ?? ??, AI ?? ??? ????.
 */
@RestController
@RequestMapping("/api/fitting")
public class FittingController {

    private final FittingService fittingService;

    public FittingController(FittingService fittingService) {
        this.fittingService = fittingService;
    }

    /**
     * ?? ???? ???? ?? ?? ??? ????? ????.
     */
    @GetMapping("/history")
    public ResponseEntity<List<FittingHistoryResponse>> getMyFittingHistory(Authentication authentication) {
        return ResponseEntity.ok(fittingService.getMyFittingHistory(authentication.getName()));
    }

    /**
     * ??? ??? ?? ?? ??? PENDING ??? ????.
     */
    @PostMapping("/history")
    public ResponseEntity<FittingCreateResponse> requestVirtualFitting(
            Authentication authentication,
            @RequestBody FittingCreateRequest request) {
        FittingHistory history = fittingService.requestFitting(authentication.getName(), request.getClothesId());
        return ResponseEntity.ok(new FittingCreateResponse(history));
    }

    /**
     * AI ?????? ???? ? ?? URL? ??? ????.
     */
    @PostMapping("/webhook/complete")
    public ResponseEntity<Map<String, String>> completeVirtualFitting(@RequestBody Map<String, Object> requestData) {
        Long fittingId = ((Number) requestData.get("fittingId")).longValue();
        String resultSplatUrl = (String) requestData.get("resultSplatUrl");
        fittingService.completeFitting(fittingId, resultSplatUrl);
        return ResponseEntity.ok(Map.of("message", "Fitting result updated successfully."));
    }
}
