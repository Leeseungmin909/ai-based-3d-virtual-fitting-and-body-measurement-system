package kr.ac.dongeui.virtualfitting.domain.measurement.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Getter
@Setter
@NoArgsConstructor
@Table(name = "user_measurements")
public class UserMeasurement {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "height_cm", nullable = false)
    private Double heightCm;

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

    @Column(name = "source_video_url", columnDefinition = "TEXT")
    private String sourceVideoUrl;

    @Column(name = "smpl_mesh_url", columnDefinition = "TEXT")
    private String smplMeshUrl;

    @Column(name = "result_json_url", columnDefinition = "TEXT")
    private String resultJsonUrl;
}