package kr.ac.dongeui.virtualfitting.domain.fitting.service;

import kr.ac.dongeui.virtualfitting.domain.clothes.entity.Clothes;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiFitJobResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiJobStatusResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiMeasurementsCm;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiRendersResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiResultResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingHistory;
import kr.ac.dongeui.virtualfitting.domain.fitting.entity.FittingStatus;
import kr.ac.dongeui.virtualfitting.domain.fitting.repository.FittingHistoryRepository;
import kr.ac.dongeui.virtualfitting.domain.measurement.entity.UserMeasurement;
import kr.ac.dongeui.virtualfitting.domain.measurement.repository.UserMeasurementRepository;
import kr.ac.dongeui.virtualfitting.global.infra.file.LocalFileStorageService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.nio.file.Path;
import java.util.function.Consumer;

@Service
public class AiCommunicationService {

    private static final Logger log = LoggerFactory.getLogger(AiCommunicationService.class);

    private final FittingHistoryRepository fittingHistoryRepository;
    private final UserMeasurementRepository userMeasurementRepository;
    private final AiServiceClient aiServiceClient;
    private final LocalFileStorageService localFileStorageService;
    private final TransactionTemplate transactionTemplate;
    private final int pollAttempts;
    private final long pollIntervalMs;

    public AiCommunicationService(
            FittingHistoryRepository fittingHistoryRepository,
            UserMeasurementRepository userMeasurementRepository,
            AiServiceClient aiServiceClient,
            LocalFileStorageService localFileStorageService,
            PlatformTransactionManager transactionManager,
            @Value("${ai.service.poll-attempts:180}") int pollAttempts,
            @Value("${ai.service.poll-interval-ms:2000}") long pollIntervalMs) {
        this.fittingHistoryRepository = fittingHistoryRepository;
        this.userMeasurementRepository = userMeasurementRepository;
        this.aiServiceClient = aiServiceClient;
        this.localFileStorageService = localFileStorageService;
        this.transactionTemplate = new TransactionTemplate(transactionManager);
        this.pollAttempts = Math.max(1, pollAttempts);
        this.pollIntervalMs = Math.max(200L, pollIntervalMs);
    }

    /**
     * 피팅 기록을 기준으로 FastAPI 작업을 생성하고, 완료 결과를 DB에 저장한다.
     */
    @Async
    public void startAiFitting(Long fittingId) {
        String aiJobId = null;
        try {
            AiFittingRequestContext context = loadRequestContext(fittingId);
            Path sourceImagePath = localFileStorageService.resolvePublicUrlToPath(context.sourceImageUrl());

            String shirt = resolveShirtFilename(context.category(), context.base3dUrl());
            String pants = resolvePantsFilename(context.category(), context.base3dUrl());

            AiFitJobResponse fitJob = aiServiceClient.requestFit(
                    sourceImagePath,
                    "neutral",
                    context.heightCm(),
                    shirt,
                    pants
            );
            aiJobId = requireJobId(fitJob);
            markProcessing(fittingId, aiJobId);

            boolean completed = waitUntilFinished(aiJobId);
            if (!completed) {
                log.warn("AI fitting job timed out. fittingId={}, aiJobId={}", fittingId, aiJobId);
                return;
            }

            AiResultResponse result = aiServiceClient.getMeasurements(aiJobId);
            AiRendersResponse renders = safeGetRenders(aiJobId);
            saveSuccess(fittingId, aiJobId, result, renders);
        } catch (Exception e) {
            log.warn("AI fitting request failed. fittingId={}, aiJobId={}", fittingId, aiJobId, e);
            markFail(fittingId, aiJobId);
        }
    }

    /**
     * 피팅 기록, 선택 옷, 사용자 원본 이미지 정보를 하나의 요청 컨텍스트로 읽는다.
     */
    private AiFittingRequestContext loadRequestContext(Long fittingId) {
        return transactionTemplate.execute(status -> {
            FittingHistory history = fittingHistoryRepository.findById(fittingId)
                    .orElseThrow(() -> new IllegalArgumentException("Fitting history not found."));
            Clothes clothes = history.getClothes();
            UserMeasurement measurement = userMeasurementRepository.findByUserId(history.getUser().getId())
                    .orElseThrow(() -> new IllegalArgumentException("User measurement not found."));

            if (!hasText(measurement.getSourceImageUrl())) {
                throw new IllegalArgumentException("sourceImageUrl is required before AI fitting.");
            }
            if (clothes == null || !hasText(clothes.getBase3dUrl())) {
                throw new IllegalArgumentException("Selected clothes 3D file is required.");
            }

            return new AiFittingRequestContext(
                    fittingId,
                    measurement.getSourceImageUrl(),
                    measurement.getHeightCm(),
                    clothes.getCategory(),
                    clothes.getBase3dUrl()
            );
        });
    }

    /**
     * AI 작업 상태가 완료 또는 실패가 될 때까지 제한 횟수만큼 조회한다.
     */
    private boolean waitUntilFinished(String aiJobId) {
        for (int attempt = 0; attempt < pollAttempts; attempt++) {
            AiJobStatusResponse jobStatus = aiServiceClient.getJobStatus(aiJobId);
            if (jobStatus != null && jobStatus.isFailed()) {
                throw new IllegalStateException("AI job failed: " + firstNonBlank(jobStatus.getError(), jobStatus.getMessage(), jobStatus.getStatus()));
            }
            if (jobStatus != null && jobStatus.isCompleted()) {
                return true;
            }
            sleepBeforeNextPoll();
        }
        return false;
    }

    /**
     * AI 작업 ID를 피팅 기록에 저장하고 진행 중 상태로 변경한다.
     */
    private void markProcessing(Long fittingId, String aiJobId) {
        transactionTemplate.executeWithoutResult(status -> {
            FittingHistory history = fittingHistoryRepository.findById(fittingId)
                    .orElseThrow(() -> new IllegalArgumentException("Fitting history not found."));
            history.setAiJobId(aiJobId);
            history.setStatus(FittingStatus.PROCESSING);
        });
    }

    /**
     * AI 결과 URL과 측정값을 피팅 기록 및 사용자 측정 테이블에 저장한다.
     */
    private void saveSuccess(Long fittingId, String aiJobId, AiResultResponse result, AiRendersResponse renders) {
        transactionTemplate.executeWithoutResult(status -> {
            FittingHistory history = fittingHistoryRepository.findById(fittingId)
                    .orElseThrow(() -> new IllegalArgumentException("Fitting history not found."));
            UserMeasurement measurement = userMeasurementRepository.findByUserId(history.getUser().getId())
                    .orElseThrow(() -> new IllegalArgumentException("User measurement not found."));

            applyMeasurements(measurement, result != null ? result.getMeasurementsCm() : null);

            String avatarGlbUrl = aiServiceClient.toAbsoluteUrl(firstNonBlank(
                    result != null ? result.getAvatarGlbUrl() : null,
                    renders != null ? renders.getAvatarGlbUrl() : null,
                    aiServiceClient.buildAvatarGlbUrl(aiJobId)
            ));
            String renderImageUrl = aiServiceClient.toAbsoluteUrl(firstNonBlank(
                    result != null ? result.getPrimaryRenderImageUrl() : null,
                    renders != null ? renders.getPrimaryRenderImageUrl() : null
            ));
            String resultJsonUrl = aiServiceClient.toAbsoluteUrl(result != null ? result.getResultJsonUrl() : null);
            String smplMeshUrl = aiServiceClient.toAbsoluteUrl(result != null ? result.getSmplMeshUrl() : null);

            measurement.setSmplMeshUrl(smplMeshUrl);
            measurement.setResultJsonUrl(resultJsonUrl);
            history.updateResult(FittingStatus.SUCCESS, aiJobId, avatarGlbUrl, renderImageUrl, resultJsonUrl);
        });
    }

    /**
     * AI 측정값이 null이 아닌 항목만 사용자 측정 정보에 반영한다.
     */
    private void applyMeasurements(UserMeasurement measurement, AiMeasurementsCm cm) {
        if (cm == null) {
            return;
        }
        setIfPresent(cm.getHeightCm(), measurement::setHeightCm);
        setIfPresent(cm.getShoulderWidthCm(), measurement::setShoulderWidthCm);
        setIfPresent(cm.getChestWidthCm(), measurement::setChestWidthCm);
        setIfPresent(cm.getSleeveLengthCm(), measurement::setSleeveLengthCm);
        setIfPresent(cm.getWaistWidthCm(), measurement::setWaistWidthCm);
        setIfPresent(cm.getHipWidthCm(), measurement::setHipWidthCm);
        setIfPresent(cm.getThighWidthCm(), measurement::setThighWidthCm);
        setIfPresent(cm.getCrotchCm(), measurement::setCrotchCm);
    }

    /**
     * AI 통신 실패 또는 작업 실패 시 피팅 상태를 FAIL로 변경한다.
     */
    private void markFail(Long fittingId, String aiJobId) {
        transactionTemplate.executeWithoutResult(status -> fittingHistoryRepository.findById(fittingId).ifPresent(history -> {
            if (hasText(aiJobId)) {
                history.setAiJobId(aiJobId);
            }
            history.setStatus(FittingStatus.FAIL);
        }));
    }

    /**
     * 선택 옷이 상의면 FastAPI shirt 필드에 넣을 옷 상대 경로를 추출한다.
     */
    private String resolveShirtFilename(String category, String base3dUrl) {
        if (isTop(category)) {
            return normalizeClothesReference(base3dUrl);
        }
        if (isBottom(category)) {
            return null;
        }
        throw new IllegalArgumentException("Unsupported clothes category: " + category);
    }

    /**
     * 선택 옷이 하의면 FastAPI pants 필드에 넣을 옷 상대 경로를 추출한다.
     */
    private String resolvePantsFilename(String category, String base3dUrl) {
        if (isBottom(category)) {
            return normalizeClothesReference(base3dUrl);
        }
        if (isTop(category)) {
            return null;
        }
        throw new IllegalArgumentException("Unsupported clothes category: " + category);
    }

    /**
     * render API는 선택 결과이므로 실패해도 전체 피팅 성공 저장은 계속 진행한다.
     */
    private AiRendersResponse safeGetRenders(String aiJobId) {
        try {
            return aiServiceClient.getRenders(aiJobId);
        } catch (Exception e) {
            log.warn("AI render list request failed. aiJobId={}", aiJobId, e);
            return null;
        }
    }

    private String requireJobId(AiFitJobResponse response) {
        if (response == null || !hasText(response.getJobId())) {
            throw new IllegalStateException("AI fit response does not contain job_id.");
        }
        return response.getJobId();
    }

    private void sleepBeforeNextPoll() {
        try {
            Thread.sleep(pollIntervalMs);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("AI polling interrupted.", e);
        }
    }

    private void setIfPresent(Double value, Consumer<Double> setter) {
        if (value != null) {
            setter.accept(value);
        }
    }

    private boolean isTop(String category) {
        return hasText(category) && (category.equalsIgnoreCase("TOP") || category.contains("상의"));
    }

    private boolean isBottom(String category) {
        return hasText(category) && (category.equalsIgnoreCase("BOTTOM") || category.contains("하의"));
    }

    /**
     * DB에 저장된 URL에서 AI 서버의 clothes 루트 아래 상대 경로를 보존한다.
     * 기존처럼 파일명만 저장된 데이터도 그대로 전달해 하위 호환성을 유지한다.
     */
    private String normalizeClothesReference(String value) {
        if (!hasText(value)) {
            return null;
        }
        String normalized = value.replace('\\', '/');
        int clothesIndex = normalized.indexOf("/clothes/");
        if (clothesIndex >= 0) {
            return normalized.substring(clothesIndex + "/clothes/".length());
        }
        if (normalized.startsWith("clothes/")) {
            return normalized.substring("clothes/".length());
        }
        return normalized.startsWith("/") ? normalized.substring(1) : normalized;
    }

    private String firstNonBlank(String... values) {
        if (values == null) {
            return null;
        }
        for (String value : values) {
            if (hasText(value)) {
                return value;
            }
        }
        return null;
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private record AiFittingRequestContext(
            Long fittingId,
            String sourceImageUrl,
            Double heightCm,
            String category,
            String base3dUrl
    ) {
    }
}
