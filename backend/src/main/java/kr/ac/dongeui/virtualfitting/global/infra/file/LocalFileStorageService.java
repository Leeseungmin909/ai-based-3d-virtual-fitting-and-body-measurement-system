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
 * Stores uploaded files under the local storage directory and returns public URLs.
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
     * Sanitizes folder and file names, then stores the file with a UUID prefix.
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
     * Sanitizes folder path input to prevent parent directory traversal.
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
     * Removes unsafe characters from the original filename.
     */
    private String sanitizeFilename(String filename) {
        String value = filename == null || filename.isBlank() ? "file" : filename;
        value = Paths.get(value).getFileName().toString();
        return value.replaceAll("[^a-zA-Z0-9._-]", "_");
    }

    /**
     * Normalizes the static public path to always start with a slash.
     */
    private String normalizePublicPath(String value) {
        String normalized = value == null || value.isBlank() ? "/storage" : value.trim();
        if (!normalized.startsWith("/")) {
            normalized = "/" + normalized;
        }
        return normalized.replaceAll("/+$", "");
    }
}
