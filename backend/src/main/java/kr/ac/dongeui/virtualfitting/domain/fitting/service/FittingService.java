package kr.ac.dongeui.virtualfitting.domain.fitting.service;

import kr.ac.dongeui.virtualfitting.domain.clothes.entity.Clothes;
import kr.ac.dongeui.virtualfitting.domain.clothes.repository.ClothesRepository;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingHistoryResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.FittingResultResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingStatus;
import kr.ac.dongeui.virtualfitting.domain.fitting.repository.FittingHistoryRepository;
import kr.ac.dongeui.virtualfitting.domain.measurement.entity.UserMeasurement;
import kr.ac.dongeui.virtualfitting.domain.measurement.repository.UserMeasurementRepository;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 피팅 기록 생성, 조회, 완료 상태 갱신을 처리합니다.
 */
@Service
public class FittingService {

    private final FittingHistoryRepository fittingHistoryRepository;
    private final UserRepository userRepository;
    private final ClothesRepository clothesRepository;
    private final UserMeasurementRepository userMeasurementRepository;
    private final AiCommunicationService aiCommunicationService;

    public FittingService(FittingHistoryRepository fittingHistoryRepository,
                          UserRepository userRepository,
                          ClothesRepository clothesRepository,
                          UserMeasurementRepository userMeasurementRepository,
                          AiCommunicationService aiCommunicationService) {
        this.fittingHistoryRepository = fittingHistoryRepository;
        this.userRepository = userRepository;
        this.clothesRepository = clothesRepository;
        this.userMeasurementRepository = userMeasurementRepository;
        this.aiCommunicationService = aiCommunicationService;
    }

    /**
     * 이메일로 사용자를 찾고 최신 피팅 기록을 반환합니다.
     */
    @Transactional(readOnly = true)
    public List<FittingHistoryResponse> getMyFittingHistory(String email) {
        User user = getUserByEmail(email);
        return fittingHistoryRepository.findByUserOrderByIdDesc(user).stream()
                .map(FittingHistoryResponse::new)
                .collect(Collectors.toList());
    }

    /**
     * 특정 피팅 기록이 현재 로그인한 사용자의 것인지 확인한 뒤 상태를 반환합니다.
     */
    @Transactional(readOnly = true)
    public FittingHistoryResponse getMyFittingHistoryDetail(String email, Long fittingId) {
        FittingHistory history = getOwnedFittingHistory(email, fittingId);
        return new FittingHistoryResponse(history);
    }

    /**
     * 특정 피팅 기록의 결과 화면용 URL과 완료 여부를 반환합니다.
     */
    @Transactional(readOnly = true)
    public FittingResultResponse getMyFittingResult(String email, Long fittingId) {
        FittingHistory history = getOwnedFittingHistory(email, fittingId);
        return new FittingResultResponse(history);
    }

    /**
     * 선택 옷을 검증하고 PENDING 상태의 피팅 기록을 만든 뒤 AI 작업을 예약합니다.
     */
    @Transactional
    public FittingHistory requestFitting(String email, Long clothesId) {
        if (clothesId == null) {
            throw new IllegalArgumentException("clothesId is required.");
        }

        User user = getUserByEmail(email);
        Clothes clothes = clothesRepository.findById(clothesId)
                .orElseThrow(() -> new IllegalArgumentException("Clothes not found."));

        // 옷 실측 사이즈가 사용자 체형보다 작으면 착용 불가로 판단해 요청을 막는다.
        validateWearable(user, clothes);

        FittingHistory history = FittingHistory.builder()
                .user(user)
                .clothes(clothes)
                .status(FittingStatus.PENDING)
                .build();

        FittingHistory savedHistory = fittingHistoryRepository.save(history);
        startAiJobAfterCommit(savedHistory.getId());
        return savedHistory;
    }

    /**
     * AI 완료 콜백을 받으면 작업 ID와 결과 파일 URL을 저장합니다.
     */
    @Transactional
    public void completeFitting(Long fittingId, String aiJobId, String avatarGlbUrl, String renderImageUrl, String resultJsonUrl) {
        FittingHistory history = fittingHistoryRepository.findById(fittingId)
                .orElseThrow(() -> new IllegalArgumentException("Fitting history not found."));
        history.updateResult(FittingStatus.SUCCESS, aiJobId, avatarGlbUrl, renderImageUrl, resultJsonUrl);
    }

    /**
     * 피팅 기록 저장 트랜잭션이 끝난 뒤 비동기 AI 호출을 시작합니다.
     */
    private void startAiJobAfterCommit(Long fittingId) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) {
            aiCommunicationService.startAiFitting(fittingId);
            return;
        }

        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                aiCommunicationService.startAiFitting(fittingId);
            }
        });
    }

    /**
     * 피팅 ID와 사용자 이메일을 함께 검사해 다른 사용자의 결과 접근을 차단합니다.
     */
    private FittingHistory getOwnedFittingHistory(String email, Long fittingId) {
        if (fittingId == null) {
            throw new IllegalArgumentException("fittingId is required.");
        }

        User user = getUserByEmail(email);
        return fittingHistoryRepository.findByIdAndUser(fittingId, user)
                .orElseThrow(() -> new IllegalArgumentException("Fitting history not found."));
    }

    /**
     * 인증 이메일로 사용자 엔티티를 조회합니다.
     */
    private User getUserByEmail(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));
    }

    /**
     * 사용자 신체 치수와 옷 실측 사이즈를 비교해 착용 가능 여부를 검사합니다.
     * 체형 정보가 없으면(아직 측정 전) 판단을 건너뜁니다.
     * 상의는 어깨너비·가슴단면, 하의는 허리너비·엉덩이너비를 기준으로 비교합니다.
     */
    private void validateWearable(User user, Clothes clothes) {
        UserMeasurement m = userMeasurementRepository.findByUserId(user.getId()).orElse(null);
        if (m == null) {
            return;
        }
        String category = clothes.getCategory();
        boolean isTop = category != null && (category.equalsIgnoreCase("TOP") || category.contains("상의"));
        boolean isBottom = category != null && (category.equalsIgnoreCase("BOTTOM") || category.contains("하의"));

        if (isTop) {
            checkDimension("어깨너비", clothes.getShoulderWidthCm(), m.getShoulderWidthCm());
            checkDimension("가슴단면", clothes.getChestWidthCm(), m.getChestWidthCm());
        } else if (isBottom) {
            checkDimension("허리너비", clothes.getWaistWidthCm(), m.getWaistWidthCm());
            checkDimension("엉덩이너비", clothes.getHipWidthCm(), m.getHipWidthCm());
        }
    }

    /**
     * 옷 치수가 체형 치수보다 작으면 착용 불가 예외를 던집니다.
     */
    private void checkDimension(String label, Double clothesCm, Double bodyCm) {
        if (clothesCm != null && bodyCm != null && clothesCm < bodyCm) {
            throw new IllegalArgumentException(String.format(
                    "선택하신 옷이 회원님 체형보다 작아 착용할 수 없습니다. (%s: 옷 %.1fcm < 체형 %.1fcm)",
                    label, clothesCm, bodyCm));
        }
    }
}