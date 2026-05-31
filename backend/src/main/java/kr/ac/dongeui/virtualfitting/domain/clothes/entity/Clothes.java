package kr.ac.dongeui.virtualfitting.domain.clothes.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Getter
@Setter
@NoArgsConstructor
@Table(name = "clothes")
public class Clothes {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, length = 50)
    private String category;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String imageUrl;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String base3dUrl;

    @Column(name = "total_length_cm")
    private Double totalLengthCm;

    @Column(name = "shoulder_width_cm")
    private Double shoulderWidthCm;

    @Column(name = "chest_width_cm")
    private Double chestWidthCm;

    @Column(name = "sleeve_length_cm")
    private Double sleeveLengthCm;

    @Column(name = "waist_width_cm")
    private Double waistWidthCm;

    @Column(name = "hip_width_cm")
    private Double hipWidthCm;

    @Column(name = "thigh_width_cm")
    private Double thighWidthCm;

    @Column(name = "crotch_cm")
    private Double crotchCm;

    @Column(name = "hem_width_cm")
    private Double hemWidthCm;
}