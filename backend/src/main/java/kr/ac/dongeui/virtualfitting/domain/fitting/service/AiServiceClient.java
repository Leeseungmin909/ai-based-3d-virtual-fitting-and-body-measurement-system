package kr.ac.dongeui.virtualfitting.domain.fitting.service;

import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiClothesLibraryResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiFitJobResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiJobStatusResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiRendersResponse;
import kr.ac.dongeui.virtualfitting.domain.fitting.dto.ai.AiResultResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.nio.file.Files;
import java.nio.file.Path;

@Service
public class AiServiceClient {

    private final RestTemplate restTemplate;
    private final String aiBaseUrl;
    private final String publicBaseUrl;

    public AiServiceClient(
            @Value("${ai.service.base-url:http://localhost:8000}") String aiBaseUrl,
            @Value("${ai.service.public-base-url:${ai.service.base-url:http://localhost:8000}}") String publicBaseUrl) {
        this.restTemplate = new RestTemplate();
        this.aiBaseUrl = normalizeBaseUrl(aiBaseUrl);
        this.publicBaseUrl = normalizeBaseUrl(publicBaseUrl);
    }

    /**
     * FastAPI /api/fit에 원본 이미지와 선택 의상 파일명을 multipart로 전송한다.
     */
    public AiFitJobResponse requestFit(Path imagePath, String gender, Double heightCm, String shirt, String pants) {
        validateImagePath(imagePath);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new FileSystemResource(imagePath));
        body.add("gender", hasText(gender) ? gender : "neutral");
        addOptionalNumberPart(body, "height_cm", heightCm);
        addOptionalPart(body, "shirt", shirt);
        addOptionalPart(body, "pants", pants);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);
        return restTemplate.postForObject(endpoint("/api/fit"), request, AiFitJobResponse.class);
    }

    /**
     * FastAPI /api/job/{job_id}에서 현재 작업 상태와 진행률을 조회한다.
     */
    public AiJobStatusResponse getJobStatus(String jobId) {
        return restTemplate.getForObject(jobEndpoint("/api/job/{jobId}", jobId), AiJobStatusResponse.class);
    }

    /**
     * FastAPI /api/measurements/{job_id}에서 신체 치수와 결과 파일 경로를 조회한다.
     */
    public AiResultResponse getMeasurements(String jobId) {
        return restTemplate.getForObject(jobEndpoint("/api/measurements/{jobId}", jobId), AiResultResponse.class);
    }

    /**
     * FastAPI /api/renders/{job_id}에서 미리보기 이미지 목록과 avatar GLB 경로를 조회한다.
     */
    public AiRendersResponse getRenders(String jobId) {
        return restTemplate.getForObject(jobEndpoint("/api/renders/{jobId}", jobId), AiRendersResponse.class);
    }

    /**
     * FastAPI /api/clothes에서 AI 서버가 가진 의상 파일 목록을 조회한다.
     */
    public AiClothesLibraryResponse getClothesLibrary() {
        return restTemplate.getForObject(endpoint("/api/clothes"), AiClothesLibraryResponse.class);
    }

    /**
     * avatar GLB는 바이너리 응답이므로 DB에는 접근 가능한 URL만 저장한다.
     */
    public String buildAvatarGlbUrl(String jobId) {
        return UriComponentsBuilder.fromUriString(publicBaseUrl + "/api/avatar-glb/{jobId}")
                .buildAndExpand(jobId)
                .toUriString();
    }

    /**
     * AI 서버가 상대 경로를 반환하면 Flutter(외부 기기)가 접근 가능한 절대 URL로 변환한다.
     * 내부 호출용 base-url이 아니라 외부 공개 주소(public-base-url)를 사용한다.
     */
    public String toAbsoluteUrl(String pathOrUrl) {
        if (!hasText(pathOrUrl)) {
            return null;
        }
        if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
            return pathOrUrl;
        }
        String path = pathOrUrl.startsWith("/") ? pathOrUrl : "/" + pathOrUrl;
        return publicBaseUrl + path;
    }

    private void validateImagePath(Path imagePath) {
        if (imagePath == null || !Files.isRegularFile(imagePath)) {
            throw new IllegalArgumentException("AI 서버에 전송할 이미지 파일을 찾을 수 없습니다.");
        }
    }

    private void addOptionalPart(MultiValueMap<String, Object> body, String name, String value) {
        if (hasText(value)) {
            body.add(name, value);
        }
    }

    private void addOptionalNumberPart(MultiValueMap<String, Object> body, String name, Double value) {
        if (value != null) {
            body.add(name, value.toString());
        }
    }

    private String endpoint(String path) {
        String normalizedPath = path.startsWith("/") ? path : "/" + path;
        return aiBaseUrl + normalizedPath;
    }

    private String jobEndpoint(String pathTemplate, String jobId) {
        return UriComponentsBuilder.fromUriString(endpoint(pathTemplate))
                .buildAndExpand(jobId)
                .toUriString();
    }

    private String normalizeBaseUrl(String value) {
        if (!hasText(value)) {
            return "http://localhost:8000";
        }
        return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
