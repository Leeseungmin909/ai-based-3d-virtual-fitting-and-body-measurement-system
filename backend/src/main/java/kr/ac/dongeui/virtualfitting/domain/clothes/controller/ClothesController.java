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
 * ?? ?? ??? ???? ?? ?? API? ????.
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
     * Flutter ?? ?? ??? ??? ?? ?? ??? ????.
     */
    @GetMapping
    public List<ClothesResponse> getAllClothes() {
        return clothesRepository.findAll().stream()
                .map(ClothesResponse::new)
                .collect(Collectors.toList());
    }

    /**
     * ?? ???? ?? ??? ????? ?? ??? ????.
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