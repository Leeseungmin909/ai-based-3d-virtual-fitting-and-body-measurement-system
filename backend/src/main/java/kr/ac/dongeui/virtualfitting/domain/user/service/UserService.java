package kr.ac.dongeui.virtualfitting.domain.user.service;

import kr.ac.dongeui.virtualfitting.domain.measurement.entity.UserMeasurement;
import kr.ac.dongeui.virtualfitting.domain.measurement.repository.UserMeasurementRepository;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import kr.ac.dongeui.virtualfitting.global.security.JwtTokenProvider;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 사용자 로그인, JWT 발급, 키 정보 동기화를 처리한다.
 */
@Transactional
@Service
public class UserService {

    private final UserRepository userRepository;
    private final UserMeasurementRepository measurementRepository;
    private final JwtTokenProvider jwtTokenProvider;

    public UserService(UserRepository userRepository,
                       UserMeasurementRepository measurementRepository,
                       JwtTokenProvider jwtTokenProvider) {
        this.userRepository = userRepository;
        this.measurementRepository = measurementRepository;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    /**
     * mock Google 로그인 요청에서 사용자를 생성 또는 조회하고 JWT를 발급한다.
     */
    public LoginResult googleLoginOrSignup(String email, String name) {
        if (email == null || email.isBlank()) {
            throw new IllegalArgumentException("email is required.");
        }
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("name is required.");
        }

        User user = userRepository.findByEmail(email).orElseGet(() -> {
            User newUser = new User();
            newUser.setEmail(email);
            newUser.setName(name);
            return userRepository.save(newUser);
        });

        String token = jwtTokenProvider.createToken(user.getEmail());
        return new LoginResult(token, user);
    }

    /**
     * 사용자 키를 users와 user_measurements에 함께 저장한다.
     */
    public User updateHeight(String email, Double heightCm) {
        if (heightCm == null || heightCm <= 0) {
            throw new IllegalArgumentException("heightCm must be greater than 0.");
        }

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException("User not found."));

        user.setHeightCm(heightCm);
        upsertMeasurementHeight(user, heightCm);
        return user;
    }

    /**
     * 치수 기록이 없으면 생성하고, 있으면 키 정보만 갱신한다.
     */
    private void upsertMeasurementHeight(User user, Double heightCm) {
        UserMeasurement measurement = measurementRepository.findByUserId(user.getId())
                .orElseGet(() -> {
                    UserMeasurement created = new UserMeasurement();
                    created.setUser(user);
                    return created;
                });

        measurement.setHeightCm(heightCm);
        measurementRepository.save(measurement);
    }

    public record LoginResult(String token, User user) {
    }
}
