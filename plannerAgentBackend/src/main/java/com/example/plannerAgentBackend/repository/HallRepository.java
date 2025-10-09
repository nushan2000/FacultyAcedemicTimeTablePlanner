package com.example.plannerAgentBackend.repository;

import com.example.plannerAgentBackend.model.Hall;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface HallRepository extends JpaRepository<Hall, Long> {

    // Find hall by room name
    Optional<Hall> findByRoomName(String roomName);

    // Find halls with capacity greater than or equal to specified value
    List<Hall> findByCapacityGreaterThanEqual(Integer capacity);

    // Find halls with capacity between min and max
    List<Hall> findByCapacityBetween(Integer minCapacity, Integer maxCapacity);

    // Find halls ordered by capacity (ascending)
    List<Hall> findAllByOrderByCapacityAsc();

    // Find halls ordered by capacity (descending)
    List<Hall> findAllByOrderByCapacityDesc();

    // Find halls by room name containing specific text (case insensitive)
    List<Hall> findByRoomNameContainingIgnoreCase(String roomName);

    // Custom query to find available halls with minimum capacity
    @Query("SELECT h FROM Hall h WHERE h.capacity >= :minCapacity ORDER BY h.capacity ASC")
    List<Hall> findAvailableHallsWithMinCapacity(@Param("minCapacity") Integer minCapacity);

    // Custom query to find halls with exact capacity
    @Query("SELECT h FROM Hall h WHERE h.capacity = :capacity")
    List<Hall> findHallsByExactCapacity(@Param("capacity") Integer capacity);

    // Check if hall exists by room name
    boolean existsByRoomName(String roomName);

    // Delete hall by room name
    void deleteByRoomName(String roomName);

    // Count halls with capacity greater than specified value
    Long countByCapacityGreaterThan(Integer capacity);

    // Find the hall with maximum capacity
    @Query("SELECT h FROM Hall h ORDER BY h.capacity DESC LIMIT 1")
    Optional<Hall> findHallWithMaxCapacity();

    // Find the hall with minimum capacity
    @Query("SELECT h FROM Hall h ORDER BY h.capacity ASC LIMIT 1")
    Optional<Hall> findHallWithMinCapacity();

    // Find halls with capacity in specific range ordered by capacity
    List<Hall> findByCapacityBetweenOrderByCapacityAsc(Integer minCapacity, Integer maxCapacity);
}