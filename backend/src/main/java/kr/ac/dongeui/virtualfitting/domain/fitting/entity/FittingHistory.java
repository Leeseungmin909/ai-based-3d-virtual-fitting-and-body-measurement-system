package kr.ac.dongeui.virtualfitting.domain.fitting.entity;

import jakarta.persistence.*;
import kr.ac.dongeui.virtualfitting.domain.clothes.entity.Clothes;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Getter
@Setter
@NoArgsConstructor
@Table(name = "fitting_histories")
@AllArgsConstructor
@Builder
@EntityListeners(AuditingEntityListener.class) // 날짜 자동 생성을 위한 리스너 추가
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

    @Column(columnDefinition = "TEXT")
    private String resultSplatUrl;

    // 피팅 상태
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private FittingStatus status;

    @CreatedDate
    @Column(updatable = false)
    private LocalDateTime createdAt;

    public void updateStatus(FittingStatus status, String resultSplatUrl) {
        this.status = status;
        this.resultSplatUrl = resultSplatUrl;
    }
}