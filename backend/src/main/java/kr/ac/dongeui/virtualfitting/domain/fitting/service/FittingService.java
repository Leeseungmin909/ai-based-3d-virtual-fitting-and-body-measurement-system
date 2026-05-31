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
 * ??? ?? ?? ??, ??, ?? ?? ??? ????.
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
     * ??? ?? ???? ?? ?? ???? ?? ??? ????? ????.
     */
    @Transactional(readOnly = true)
    public List<FittingHistoryResponse> getMyFittingHistory(String email) {
        User user = getUserByEmail(email);
        return fittingHistoryRepository.findByUserOrderByIdDesc(user).stream()
                .map(FittingHistoryResponse::new)
                .collect(Collectors.toList());
    }

    /**
     * ?? ??? ????? ??? ? PENDING ?? ??? ????.
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
     * AI ?? ?? ??? ?? ?? URL? SUCCESS ??? ????.
     */
    @Transactional
    public void completeFitting(Long fittingId, String resultUrl) {
        FittingHistory history = fittingHistoryRepository.findById(fittingId)
                .orElseThrow(() -> new IllegalArgumentException("Fitting history not found."));
        history.updateStatus(FittingStatus.SUCCESS, resultUrl);
    }

    /**
     * ?? ???? ???? ???? ????.
     */
    private User getUserByEmail(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));
    }
}
