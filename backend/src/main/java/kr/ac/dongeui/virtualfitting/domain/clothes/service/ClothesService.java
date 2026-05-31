package kr.ac.dongeui.virtualfitting.domain.clothes.service;

import kr.ac.dongeui.virtualfitting.domain.clothes.dto.ClothesCreateRequest;
import kr.ac.dongeui.virtualfitting.domain.clothes.entity.Clothes;
import kr.ac.dongeui.virtualfitting.domain.clothes.repository.ClothesRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 옷 치수와 에셋 URL 저장을 처리한다.
 */
@Service
@Transactional
public class ClothesService {

    private final ClothesRepository clothesRepository;

    public ClothesService(ClothesRepository clothesRepository) {
        this.clothesRepository = clothesRepository;
    }

    /**
     * 요청 DTO를 Clothes 엔티티로 변환해 저장한다.
     */
    public Long createClothes(ClothesCreateRequest request) {
        Clothes clothes = new Clothes();
        clothes.setName(request.getName());
        clothes.setCategory(request.getCategory());
        clothes.setImageUrl(request.getImageUrl());
        clothes.setBase3dUrl(request.getBase3dUrl());
        clothes.setTotalLengthCm(request.getTotalLengthCm());
        clothes.setShoulderWidthCm(request.getShoulderWidthCm());
        clothes.setChestWidthCm(request.getChestWidthCm());
        clothes.setSleeveLengthCm(request.getSleeveLengthCm());
        clothes.setWaistWidthCm(request.getWaistWidthCm());
        clothes.setHipWidthCm(request.getHipWidthCm());
        clothes.setThighWidthCm(request.getThighWidthCm());
        clothes.setCrotchCm(request.getCrotchCm());
        clothes.setHemWidthCm(request.getHemWidthCm());

        Clothes savedClothes = clothesRepository.save(clothes);
        return savedClothes.getId();
    }
}
