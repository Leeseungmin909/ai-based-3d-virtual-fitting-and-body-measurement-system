package kr.ac.dongeui.virtualfitting.domain.user.service;

import kr.ac.dongeui.virtualfitting.domain.measurement.entity.UserMeasurement;
import kr.ac.dongeui.virtualfitting.domain.measurement.repository.UserMeasurementRepository;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import kr.ac.dongeui.virtualfitting.global.security.JwtTokenProvider;
import org.springframework.security.crypto.password.PasswordEncoder;
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
    private final PasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository,
                       UserMeasurementRepository measurementRepository,
                       JwtTokenProvider jwtTokenProvider,
                       PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.measurementRepository = measurementRepository;
        this.jwtTokenProvider = jwtTokenProvider;
        this.passwordEncoder = passwordEncoder;
    }

    /**
     * 이메일/비밀번호로 신규 사용자를 생성하고 JWT를 발급한다.
     */
    public LoginResult signup(String email, String name, String password) {
        if (email == null || email.isBlank()) {
            throw new IllegalArgumentException("이메일을 입력해 주세요.");
        }
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("이름을 입력해 주세요.");
        }
        if (password == null || password.length() < 4) {
            throw new IllegalArgumentException("비밀번호는 4자 이상이어야 합니다.");
        }
        if (userRepository.findByEmail(email).isPresent()) {
            throw new IllegalArgumentException("이미 가입된 이메일입니다.");
        }

        User user = new User();
        user.setEmail(email);
        user.setName(name);
        user.setPassword(passwordEncoder.encode(password));
        userRepository.save(user);

        String token = jwtTokenProvider.createToken(user.getEmail());
        return new LoginResult(token, user);
    }

    /**
     * 이메일/비밀번호를 검증하고 일치하면 JWT를 발급한다.
     */
    public LoginResult login(String email, String password) {
        if (email == null || email.isBlank() || password == null || password.isBlank()) {
            throw new IllegalArgumentException("이메일과 비밀번호를 입력해 주세요.");
        }

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException("이메일 또는 비밀번호가 올바르지 않습니다."));

        if (user.getPassword() == null || !passwordEncoder.matches(password, user.getPassword())) {
            throw new IllegalArgumentException("이메일 또는 비밀번호가 올바르지 않습니다.");
        }

        String token = jwtTokenProvider.createToken(user.getEmail());
        return new LoginResult(token, user);
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
