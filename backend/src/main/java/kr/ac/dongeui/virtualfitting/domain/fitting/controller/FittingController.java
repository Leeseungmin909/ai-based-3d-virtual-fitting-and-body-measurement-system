package kr.ac.dongeui.virtualfitting.domain.fitting.controller;

import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingHistoryResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.service.FittingService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/fitting")
public class FittingController {

    private final FittingService fittingService;

    public FittingController(FittingService fittingService) {
        this.fittingService = fittingService;
    }

    // 내 피팅 히스토리 불러오기
    @GetMapping("/history")
    public ResponseEntity<List<FittingHistoryResponse>> getMyFittingHistory(Authentication authentication) {
        String email = authentication.getName(); // JWT 토큰에서 이메일 추출
        List<FittingHistoryResponse> history = fittingService.getMyFittingHistory(email);
        return ResponseEntity.ok(history);
    }

    // 가상 피팅 요청 및 히스토리 저장
    @PostMapping("/history")
    public ResponseEntity<Map<String, Object>> requestVirtualFitting(
            Authentication authentication,
            @RequestBody Map<String, Long> requestData) {

        String userEmail = authentication.getName();
        Long clothesId = requestData.get("clothesId");

        Long fittingId = fittingService.requestFitting(userEmail, clothesId);

        Map<String, Object> response = new HashMap<>();
        response.put("status", "PENDING");
        response.put("fittingId", fittingId);
        response.put("message", "피팅 요청 및 히스토리 저장 성공");

        return ResponseEntity.ok(response);
    }

    @PostMapping("/webhook/complete")
    public ResponseEntity<String> completeVirtualFitting(@RequestBody Map<String, Object> requestData) {
        Long fittingId = ((Number) requestData.get("fittingId")).longValue();
        String resultSplatUrl = (String) requestData.get("resultSplatUrl");
        fittingService.completeFitting(fittingId, resultSplatUrl);
        return ResponseEntity.ok("자바 서버: 피팅 결과 업데이트 완료");
    }
}