package com.example.plannerAgentBackend.repository;

import com.example.plannerAgentBackend.model.SolverResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SolverResultRepository extends JpaRepository<SolverResult, Long> {
}
