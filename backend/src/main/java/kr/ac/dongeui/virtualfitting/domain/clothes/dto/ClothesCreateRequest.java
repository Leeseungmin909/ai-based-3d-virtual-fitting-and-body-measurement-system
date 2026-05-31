package kr.ac.dongeui.virtualfitting.domain.clothes.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Getter;

@Getter
public class ClothesCreateRequest {
    private String name;
    private String category;
    private String imageUrl;
    private String base3dUrl;

    @JsonAlias("totalLength")
    private Double totalLengthCm;

    @JsonAlias("shoulderWidth")
    private Double shoulderWidthCm;

    @JsonAlias("chestWidth")
    private Double chestWidthCm;

    @JsonAlias("sleeveLength")
    private Double sleeveLengthCm;

    @JsonAlias("waistWidth")
    private Double waistWidthCm;

    @JsonAlias("hipWidth")
    private Double hipWidthCm;

    @JsonAlias("thighWidth")
    private Double thighWidthCm;

    @JsonAlias("crotch")
    private Double crotchCm;

    @JsonAlias("hemWidth")
    private Double hemWidthCm;
}