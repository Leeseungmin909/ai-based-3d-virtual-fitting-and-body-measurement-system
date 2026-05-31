package kr.ac.dongeui.virtualfitting;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * Spring Boot 애플리케이션 시작점이다.
 */
@EnableAsync
@EnableJpaAuditing
@SpringBootApplication
public class VirtualFittingApplication {
    public static void main(String[] args) {
        SpringApplication.run(VirtualFittingApplication.class, args);
    }
}
