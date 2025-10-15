package com.example.plannerAgentBackend.controller;

import com.example.plannerAgentBackend.model.ExamTableRecords;
import com.example.plannerAgentBackend.model.SolverResult;
import com.example.plannerAgentBackend.service.SolverExamService;
import com.example.plannerAgentBackend.service.SolverService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:3000")
public class SolverController {

    @Autowired
    private SolverService solverService;

    @Autowired
    private SolverExamService solverExamService;

    @GetMapping("/solve")
    public ResponseEntity<String> runSolver() {
        String result = solverService.runSolver();
        return ResponseEntity.ok(result);
    }
    @GetMapping("/examSolve")
    public ResponseEntity<String> runExamSolver() {
        String result = solverExamService.runExamSolver();
        return ResponseEntity.ok(result);
    }

    @GetMapping("/solver-results")
    public ResponseEntity<List<SolverResult>> getAllSolverResults() throws Exception {
        return ResponseEntity.ok(solverService.getAllSolverResults());
    }
    @GetMapping("/solver-exam-results")
    public ResponseEntity<List<ExamTableRecords>> getAllExamSolverResults() throws Exception {
        return ResponseEntity.ok(solverExamService.getAllExamTableRecords());
    }
}
