package com.example.plannerAgentBackend.service;

import com.example.plannerAgentBackend.model.SolverResult;
import com.example.plannerAgentBackend.repository.SolverResultRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class SolverService {

    @Autowired
    private SolverResultRepository solverResultRepository;

    public String runSolver() {
        try {
            // Run Python script
            ProcessBuilder pb = new ProcessBuilder("python", "D:/8th/FYP/plannerAgent/solver/timetable_csp.py");
            pb.redirectErrorStream(true);
            Process process = pb.start();

            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }

            process.waitFor();

            // Extract JSON from output
            Pattern pattern = Pattern.compile("\\{.*\\}", Pattern.DOTALL);
            Matcher matcher = pattern.matcher(output.toString());
            if (!matcher.find()) {
                return "No JSON found in solver output.";
            }

            String jsonOutput = matcher.group(0);

            // Parse JSON
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(jsonOutput);

            if (!root.has("timetable")) {
                return "No timetable found in JSON.";
            }

            JsonNode timetableNode = root.get("timetable");
            List<SolverResult> results = new ArrayList<>();

            for (JsonNode entry : timetableNode) {
                SolverResult result = new SolverResult();
                result.setCode(entry.get("code").asText());
                result.setDay(entry.get("day").asText());
                result.setHall(entry.get("hall").asText());
                result.setSlot(entry.get("slot").asInt());

                result.setDuration(entry.get("duration").asInt());
                result.setStudents(entry.get("students").asInt());
                result.setDepartment(entry.get("department").asText());

                result.setSemester(entry.get("semester").asInt());
                result.setCommon(entry.get("iscommon").asBoolean());
                results.add(result);
            }

            solverResultRepository.deleteAll();
            solverResultRepository.saveAll(results);

            return "Solver executed successfully. " + results.size() + " records saved.";

        } catch (Exception e) {
            e.printStackTrace();
            return "Error running solver: " + e.getMessage();
        }


    }
    public List<SolverResult> getAllSolverResults() {
        return solverResultRepository.findAll();
    }
}
