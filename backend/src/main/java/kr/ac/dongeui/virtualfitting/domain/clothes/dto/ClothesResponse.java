package kr.ac.dongeui.virtualfitting.domain.clothes.dto;

import kr.ac.dongeui.virtualfitting.domain.clothes.entity.Clothes;
import lombok.Getter;

@Getter
public class ClothesResponse {
    private final Long id;
    private final String name;
    private final String category;
    private final String imageUrl;
    private final String base3dUrl;
    private final Double totalLengthCm;
    private final Double shoulderWidthCm;
    private final Double chestWidthCm;
    private final Double sleeveLengthCm;
    private final Double waistWidthCm;
    private final Double hipWidthCm;
    private final Double thighWidthCm;
    private final Double crotchCm;
    private final Double hemWidthCm;

    public ClothesResponse(Clothes clothes) {
        this.id = clothes.getId();
        this.name = clothes.getName();
        this.category = clothes.getCategory();
        this.imageUrl = clothes.getImageUrl();
        this.base3dUrl = clothes.getBase3dUrl();
        this.totalLengthCm = clothes.getTotalLengthCm();
        this.shoulderWidthCm = clothes.getShoulderWidthCm();
        this.chestWidthCm = clothes.getChestWidthCm();
        this.sleeveLengthCm = clothes.getSleeveLengthCm();
        this.waistWidthCm = clothes.getWaistWidthCm();
        this.hipWidthCm = clothes.getHipWidthCm();
        this.thighWidthCm = clothes.getThighWidthCm();
        this.crotchCm = clothes.getCrotchCm();
        this.hemWidthCm = clothes.getHemWidthCm();
    }
}