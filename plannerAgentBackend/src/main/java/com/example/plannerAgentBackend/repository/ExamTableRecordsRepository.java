package com.example.plannerAgentBackend.repository;

import com.example.plannerAgentBackend.model.ExamTableRecords;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ExamTableRecordsRepository extends JpaRepository<ExamTableRecords, Long> {
}
