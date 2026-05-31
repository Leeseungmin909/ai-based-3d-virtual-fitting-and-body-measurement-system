package kr.ac.dongeui.virtualfitting.global.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * 로컬 저장소 디렉터리를 HTTP 정적 리소스로 노출한다.
 */
@Configuration
public class StaticResourceConfig implements WebMvcConfigurer {

    private final Path storageRoot;
    private final String publicPath;

    public StaticResourceConfig(
            @Value("${app.storage.root:storage}") String storageRoot,
            @Value("${app.storage.public-path:/storage}") String publicPath) {
        this.storageRoot = Paths.get(storageRoot).toAbsolutePath().normalize();
        this.publicPath = normalizePublicPath(publicPath);
    }

    /**
     * /storage/** 요청을 로컬 저장소 파일 경로에 매핑한다.
     */
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler(publicPath + "/**")
                .addResourceLocations(storageRoot.toUri().toString());
    }

    /**
     * 비어 있거나 잘못된 공개 경로 설정을 정규화한다.
     */
    private String normalizePublicPath(String value) {
        String normalized = value == null || value.isBlank() ? "/storage" : value.trim();
        if (!normalized.startsWith("/")) {
            normalized = "/" + normalized;
        }
        return normalized.replaceAll("/+$", "");
    }
}
