package kr.ac.dongeui.virtualfitting.domain.user.service;

import kr.ac.dongeui.virtualfitting.domain.measurement.entity.UserMeasurement;
import kr.ac.dongeui.virtualfitting.domain.measurement.repository.UserMeasurementRepository;
import kr.ac.dongeui.virtualfitting.domain.user.entity.User;
import kr.ac.dongeui.virtualfitting.domain.user.repository.UserRepository;
import kr.ac.dongeui.virtualfitting.global.security.JwtTokenProvider;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Handles user login, JWT issuing, and height synchronization.
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
     * Handles mock Google login by creating or loading a user and issuing a JWT.
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
     * Stores the user height in both users and user_measurements.
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
     * Creates the measurement record when missing, otherwise updates only height.
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
