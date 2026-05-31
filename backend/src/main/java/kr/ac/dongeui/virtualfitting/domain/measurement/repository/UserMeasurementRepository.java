package kr.ac.dongeui.virtualfitting.domain.measurement.repository;

import kr.ac.dongeui.virtualfitting.domain.measurement.entity.UserMeasurement;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserMeasurementRepository extends JpaRepository<UserMeasurement, Long> {
    Optional<UserMeasurement> findByUserId(Long userId);
}