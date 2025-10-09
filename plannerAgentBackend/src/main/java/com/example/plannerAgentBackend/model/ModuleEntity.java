package com.example.plannerAgentBackend.model;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Entity
@Table(name="module")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ModuleEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "module_code", nullable = false)
    @NotNull(message = "Module code cannot be null")
    private String moduleCode;

    @Column(name = "semester", nullable = false)
    @NotNull(message = "Semester cannot be null")
    private Integer semester;

    @Column(name = "duration", nullable = false)
    @NotNull(message = "Duration cannot be null")
    private Integer duration;

    @Column(name = "department", nullable = false)
    @NotNull(message = "Department cannot be null")
    private String department;

    @Column(name = "is_common", nullable = false)
    @NotNull(message = "IsCommon cannot be null")
    private Boolean isCommon;

    @Column(name = "no_of_students", nullable = false)
    @NotNull(message = "NoOfStudents cannot be null")
    private Integer noOfStudents;
}