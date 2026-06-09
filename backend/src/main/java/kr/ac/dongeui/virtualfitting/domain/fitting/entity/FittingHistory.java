package kr.ac.dongeui.virtualfitting.domain.fitting.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import kr.ac.dongeui.virtualfitting.domain.clothes.entity.Clothes;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Table(name = "fitting_histories")
@EntityListeners(AuditingEntityListener.class)
public class FittingHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "clothes_id", nullable = false)
    private Clothes clothes;

    @Column(name = "ai_job_id", length = 100)
    private String aiJobId;

    @Column(name = "avatar_glb_url", columnDefinition = "TEXT")
    private String avatarGlbUrl;

    @Column(name = "render_image_url", columnDefinition = "TEXT")
    private String renderImageUrl;

    @Column(name = "result_json_url", columnDefinition = "TEXT")
    private String resultJsonUrl;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 50)
    private FittingStatus status;

    @CreatedDate
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (status == null) {
            status = FittingStatus.PENDING;
        }
    }

    public void updateResult(FittingStatus status, String aiJobId, String avatarGlbUrl, String renderImageUrl, String resultJsonUrl) {
        this.status = status;
        this.aiJobId = aiJobId;
        this.avatarGlbUrl = avatarGlbUrl;
        this.renderImageUrl = renderImageUrl;
        this.resultJsonUrl = resultJsonUrl;
    }
}