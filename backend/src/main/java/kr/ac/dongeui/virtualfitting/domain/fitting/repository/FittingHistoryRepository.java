package kr.ac.dongeui.virtualfitting.domain.fitting.repository;

import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface FittingHistoryRepository extends JpaRepository<FittingHistory, Long> {
    // 특정 사용자의 피팅 이력을 최신순으로 조회합니다.
    List<FittingHistory> findByUserOrderByIdDesc(User user);

    // 다른 사용자의 피팅 상태를 조회하지 못하도록 사용자 조건을 함께 적용합니다.
    Optional<FittingHistory> findByIdAndUser(Long id, User user);
}
