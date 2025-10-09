package com.example.plannerAgentBackend.repository;

import com.example.plannerAgentBackend.model.ModuleEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ModuleRepository extends JpaRepository<ModuleEntity, Long> {

    // Find module by module code
    Optional<ModuleEntity> findByModuleCode(String moduleCode);

    // Find all modules by semester
    List<ModuleEntity> findBySemester(Integer semester);

    // Find all modules by department
    List<ModuleEntity> findByDepartment(String department);

    // Find modules by semester and department
    List<ModuleEntity> findBySemesterAndDepartment(Integer semester, String department);

    // Find common modules
    List<ModuleEntity> findByIsCommonTrue();

    // Find modules with student count greater than specified value
    List<ModuleEntity> findByNoOfStudentsGreaterThan(Integer noOfStudents);

    // Find modules by duration
    List<ModuleEntity> findByDuration(Integer duration);

    // Custom query to find modules by multiple criteria
    @Query("SELECT m FROM ModuleEntity m WHERE m.semester = :semester AND m.department = :department AND m.isCommon = :isCommon")
    List<ModuleEntity> findModulesBySemesterDeptAndCommon(
            @Param("semester") Integer semester,
            @Param("department") String department,
            @Param("isCommon") Boolean isCommon
    );

    // Custom query to find modules with minimum student count
    @Query("SELECT m FROM ModuleEntity m WHERE m.noOfStudents >= :minStudents")
    List<ModuleEntity> findModulesWithMinStudents(@Param("minStudents") Integer minStudents);

    // Check if module exists by module code
    boolean existsByModuleCode(String moduleCode);

    // Delete module by module code
    void deleteByModuleCode(String moduleCode);

    // Count modules by department
    Long countByDepartment(String department);

    // Find modules ordered by number of students (descending)
    List<ModuleEntity> findAllByOrderByNoOfStudentsDesc();

    // Find modules by semester ordered by module code
    List<ModuleEntity> findBySemesterOrderByModuleCodeAsc(Integer semester);
}