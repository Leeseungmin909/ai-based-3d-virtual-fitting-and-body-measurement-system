package kr.ac.dongeui.virtualfitting.global.infra.file;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

/**
 * 업로드 파일을 로컬 저장소에 저장하고 공개 URL과 실제 파일 경로를 관리한다.
 */
@Service
public class LocalFileStorageService {

    private final Path storageRoot;
    private final String publicPath;

    public LocalFileStorageService(
            @Value("${app.storage.root:storage}") String storageRoot,
            @Value("${app.storage.public-path:/storage}") String publicPath) {
        this.storageRoot = Paths.get(storageRoot).toAbsolutePath().normalize();
        this.publicPath = normalizePublicPath(publicPath);
    }

    /**
     * 폴더명과 파일명을 정리한 뒤 UUID 접두어를 붙여 로컬 저장소에 저장한다.
     */
    public String uploadFile(MultipartFile file, String folder) throws IOException {
        if (file == null || file.isEmpty()) {
            throw new IOException("Uploaded file is empty.");
        }

        String safeFolder = sanitizePathPart(folder == null ? "uploads" : folder);
        String safeOriginalName = sanitizeFilename(file.getOriginalFilename());
        String storedName = UUID.randomUUID() + "_" + safeOriginalName;

        Path targetDir = storageRoot.resolve(safeFolder).normalize();
        if (!targetDir.startsWith(storageRoot)) {
            throw new IOException("Invalid upload folder.");
        }

        Files.createDirectories(targetDir);
        Path targetFile = targetDir.resolve(storedName).normalize();
        file.transferTo(targetFile);

        return publicPath + "/" + safeFolder + "/" + storedName;
    }

    /**
     * /storage/... 공개 URL을 AI 서버에 전송 가능한 실제 로컬 파일 경로로 변환한다.
     */
    public Path resolvePublicUrlToPath(String fileUrl) {
        if (fileUrl == null || fileUrl.isBlank()) {
            throw new IllegalArgumentException("파일 URL이 비어 있습니다.");
        }

        String path = extractPath(fileUrl.trim());
        if (!path.startsWith(publicPath + "/")) {
            throw new IllegalArgumentException("로컬 저장소 URL이 아닙니다: " + fileUrl);
        }

        String relativePath = path.substring((publicPath + "/").length());
        Path resolvedPath = storageRoot.resolve(relativePath).normalize();
        if (!resolvedPath.startsWith(storageRoot)) {
            throw new IllegalArgumentException("잘못된 파일 경로입니다: " + fileUrl);
        }
        if (!Files.isRegularFile(resolvedPath)) {
            throw new IllegalArgumentException("업로드된 원본 이미지 파일을 찾을 수 없습니다: " + resolvedPath);
        }
        return resolvedPath;
    }

    /**
     * 절대 URL이면 path 부분만 사용하고, 상대 URL이면 앞에 슬래시를 붙인다.
     */
    private String extractPath(String fileUrl) {
        if (fileUrl.startsWith("http://") || fileUrl.startsWith("https://")) {
            return URI.create(fileUrl).getPath();
        }
        return fileUrl.startsWith("/") ? fileUrl : "/" + fileUrl;
    }

    /**
     * 상위 디렉터리 접근을 막기 위해 업로드 폴더 경로를 정리한다.
     */
    private String sanitizePathPart(String value) {
        String sanitized = value.replace('\\', '/').replaceAll("[^a-zA-Z0-9/_-]", "_");
        while (sanitized.contains("..")) {
            sanitized = sanitized.replace("..", "_");
        }
        sanitized = sanitized.replaceAll("^/+", "").replaceAll("/+$", "");
        return sanitized.isBlank() ? "uploads" : sanitized;
    }

    /**
     * 원본 파일명에서 안전하지 않은 문자를 제거한다.
     */
    private String sanitizeFilename(String filename) {
        String value = filename == null || filename.isBlank() ? "file" : filename;
        value = Paths.get(value).getFileName().toString();
        return value.replaceAll("[^a-zA-Z0-9._-]", "_");
    }

    /**
     * 공개 경로가 항상 슬래시로 시작하고 끝에는 슬래시가 없도록 정규화한다.
     */
    private String normalizePublicPath(String value) {
        String normalized = value == null || value.isBlank() ? "/storage" : value.trim();
        if (!normalized.startsWith("/")) {
            normalized = "/" + normalized;
        }
        return normalized.replaceAll("/+$", "");
    }
}