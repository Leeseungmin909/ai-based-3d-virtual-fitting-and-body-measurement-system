package kr.ac.dongeui.virtualfitting.domain.user.dto;

import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import lombok.Getter;

@Getter
public class UserBodyInfoResponse {
    private final Long userId;
    private final Double heightCm;

    public UserBodyInfoResponse(User user) {
        this.userId = user.getId();
        this.heightCm = user.getHeightCm();
    }
}
