package kr.ac.dongeui.virtualfitting.global.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Exposes the local storage directory through HTTP static resources.
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
     * Maps /storage/** requests to files under the local storage directory.
     */
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler(publicPath + "/**")
                .addResourceLocations(storageRoot.toUri().toString());
    }

    /**
     * Normalizes blank or malformed public path settings.
     */
    private String normalizePublicPath(String value) {
        String normalized = value == null || value.isBlank() ? "/storage" : value.trim();
        if (!normalized.startsWith("/")) {
            normalized = "/" + normalized;
        }
        return normalized.replaceAll("/+$", "");
    }
}
