package com.example.plannerAgentBackend.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "solver_result")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SolverResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String code;
    private String day;
    private String hall;
    private int slot;
    private int duration;
    private int students;
    private String department;
    private int semester;
    private boolean isCommon;
    
}
