package kr.ac.dongeui.virtualfitting.global.infra.file;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

/**
 * 업로드 파일을 로컬 저장소에 저장하고 공개 URL을 반환한다.
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
     * 폴더명과 파일명을 정리한 뒤 UUID 접두사를 붙여 저장한다.
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
     * 상위 디렉터리 접근을 막기 위해 폴더 경로 입력값을 정리한다.
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
     * 정적 공개 경로가 항상 슬래시로 시작하도록 정규화한다.
     */
    private String normalizePublicPath(String value) {
        String normalized = value == null || value.isBlank() ? "/storage" : value.trim();
        if (!normalized.startsWith("/")) {
            normalized = "/" + normalized;
        }
        return normalized.replaceAll("/+$", "");
    }
}
