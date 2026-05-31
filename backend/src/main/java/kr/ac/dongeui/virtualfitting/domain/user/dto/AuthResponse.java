package kr.ac.dongeui.virtualfitting.domain.user.dto;

import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import lombok.Getter;

@Getter
public class AuthResponse {
    private final String token;
    private final Long userId;
    private final String email;
    private final String name;
    private final Double heightCm;

    public AuthResponse(String token, User user) {
        this.token = token;
        this.userId = user.getId();
        this.email = user.getEmail();
        this.name = user.getName();
        this.heightCm = user.getHeightCm();
    }
}
