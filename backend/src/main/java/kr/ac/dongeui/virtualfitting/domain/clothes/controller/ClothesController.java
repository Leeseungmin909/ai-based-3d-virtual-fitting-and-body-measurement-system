package kr.ac.dongeui.virtualfitting.domain.clothes.controller;

import kr.ac.dongeui.virtualfitting.domain.clothes.dto.ClothesCreateRequest;
import kr.ac.dongeui.virtualfitting.domain.clothes.dto.ClothesResponse;
import kr.ac.dongeui.virtualfitting.domain.clothes.repository.ClothesRepository;
import kr.ac.dongeui.virtualfitting.domain.clothes.service.ClothesService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 옷 목록 조회와 테스트용 옷 등록 API를 제공한다.
 */
@RestController
@RequestMapping("/api/clothes")
public class ClothesController {

    private final ClothesRepository clothesRepository;
    private final ClothesService clothesService;

    public ClothesController(ClothesRepository clothesRepository, ClothesService clothesService) {
        this.clothesRepository = clothesRepository;
        this.clothesService = clothesService;
    }

    /**
     * Flutter 옷 선택 화면에 필요한 전체 옷 목록을 반환한다.
     */
    @GetMapping
    public List<ClothesResponse> getAllClothes() {
        return clothesRepository.findAll().stream()
                .map(ClothesResponse::new)
                .collect(Collectors.toList());
    }

    /**
     * 로컬 테스트 또는 초기 데이터 입력용 옷 메타데이터를 저장한다.
     */
    @PostMapping
    public ResponseEntity<Map<String, Object>> createClothes(@RequestBody ClothesCreateRequest request) {
        Long clothesId = clothesService.createClothes(request);

        Map<String, Object> response = new HashMap<>();
        response.put("message", "Clothes created successfully.");
        response.put("clothesId", clothesId);

        return ResponseEntity.ok(response);
    }
}
