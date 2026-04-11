package kr.ac.dongeui.virtualfitting.domain.fitting.service;

import kr.ac.dongeui.virtualfitting.domain.clothes.entity.Clothes;
import kr.ac.dongeui.virtualfitting.domain.clothes.repository.ClothesRepository;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingHistoryResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingStatus; // (enum: PENDING, COMPLETED)
import kr.ac.dongeui.virtualfitting.domain.fitting.repository.FittingHistoryRepository;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

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

    // 피팅 내역 불러오기
    @Transactional(readOnly = true)
    public List<FittingHistoryResponse> getMyFittingHistory(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        return fittingHistoryRepository.findByUserOrderByIdDesc(user).stream()
                .map(FittingHistoryResponse::new)
                .collect(Collectors.toList());
    }

    // 피팅 저장하기
    @Transactional
    public Long requestFitting(String email, Long clothesId) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        Clothes clothes = clothesRepository.findById(clothesId)
                .orElseThrow(() -> new IllegalArgumentException("옷 정보를 찾을 수 없습니다."));

        FittingHistory history = FittingHistory.builder()
                .user(user)
                .clothes(clothes)
                .status(FittingStatus.PENDING)
                .build();

        fittingHistoryRepository.save(history);

        // TODO: 나중에 여기에 파이썬 서버로 렌더링 시작을 알리는 HTTP POST 통신 코드를 추가해야함

        return history.getId();
    }

    // 파이썬 콜백 처리
    @Transactional
    public void completeFitting(Long fittingId, String resultUrl) {
        FittingHistory history = fittingHistoryRepository.findById(fittingId)
                .orElseThrow(() -> new IllegalArgumentException("내역을 찾을 수 없습니다."));
        history.updateStatus(FittingStatus.SUCCESS, resultUrl);
    }
}