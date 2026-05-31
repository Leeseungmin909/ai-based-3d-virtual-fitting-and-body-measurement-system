package kr.ac.dongeui.virtualfitting.domain.fitting.service;

import kr.ac.dongeui.virtualfitting.domain.clothes.entity.Clothes;
import kr.ac.dongeui.virtualfitting.domain.clothes.repository.ClothesRepository;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingHistoryResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingStatus;
import kr.ac.dongeui.virtualfitting.domain.fitting.repository.FittingHistoryRepository;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 피팅 기록 생성, 조회, 완료 상태 갱신을 처리한다.
 */
@Service
public class FittingService {

    private final FittingHistoryRepository fittingHistoryRepository;
    private final UserRepository userRepository;
    private final ClothesRepository clothesRepository;

    public FittingService(FittingHistoryRepository fittingHistoryRepository,
                          UserRepository userRepository,
                          ClothesRepository clothesRepository) {
        this.fittingHistoryRepository = fittingHistoryRepository;
        this.userRepository = userRepository;
        this.clothesRepository = clothesRepository;
    }

    /**
     * 이메일로 사용자를 찾고 최신순 피팅 기록을 반환한다.
     */
    @Transactional(readOnly = true)
    public List<FittingHistoryResponse> getMyFittingHistory(String email) {
        User user = getUserByEmail(email);
        return fittingHistoryRepository.findByUserOrderByIdDesc(user).stream()
                .map(FittingHistoryResponse::new)
                .collect(Collectors.toList());
    }

    /**
     * 선택한 옷을 검증하고 PENDING 상태의 피팅 기록을 생성한다.
     */
    @Transactional
    public FittingHistory requestFitting(String email, Long clothesId) {
        if (clothesId == null) {
            throw new IllegalArgumentException("clothesId is required.");
        }

        User user = getUserByEmail(email);
        Clothes clothes = clothesRepository.findById(clothesId)
                .orElseThrow(() -> new IllegalArgumentException("Clothes not found."));

        FittingHistory history = FittingHistory.builder()
                .user(user)
                .clothes(clothes)
                .status(FittingStatus.PENDING)
                .build();

        return fittingHistoryRepository.save(history);
    }

    /**
     * AI 완료 콜백의 결과 URL과 SUCCESS 상태를 저장한다.
     */
    @Transactional
    public void completeFitting(Long fittingId, String resultUrl) {
        FittingHistory history = fittingHistoryRepository.findById(fittingId)
                .orElseThrow(() -> new IllegalArgumentException("Fitting history not found."));
        history.updateStatus(FittingStatus.SUCCESS, resultUrl);
    }

    /**
     * 인증된 이메일로 사용자를 조회한다.
     */
    private User getUserByEmail(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));
    }
}
