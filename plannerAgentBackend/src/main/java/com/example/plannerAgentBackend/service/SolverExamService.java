package com.example.plannerAgentBackend.service;

import com.example.plannerAgentBackend.model.ExamTableRecords;
import com.example.plannerAgentBackend.repository.ExamTableRecordsRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class SolverExamService {

    @Autowired
    private ExamTableRecordsRepository examSolverResultRepository;

    public String runExamSolver() {
        try {
            // Run Python script
            ProcessBuilder pb = new ProcessBuilder(
                    "python",
                    "D:\\7th\\FinalYearProject\\development\\AllSections\\AI-Assistance-FOE\\backend-Planner\\solver\\exam_timetable_csp2.py"
            );

// Merge stderr into stdout so you can catch errors
            pb.redirectErrorStream(true);

// Set working directory to the 7th semester folder
            pb.directory(new File("D:\\7th\\FinalYearProject\\development\\AllSections\\AI-Assistance-FOE\\backend-Planner\\solver"));

// Start the process
            Process process = pb.start();


            // Read Python output in real time
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                // Print Python script output
                System.out.println(line);
                output.append(line).append("\n");
            }

            process.waitFor();

            // Extract JSON from Python output
            Pattern pattern = Pattern.compile("\\{.*\\}", Pattern.DOTALL);
            Matcher matcher = pattern.matcher(output.toString());
            if (!matcher.find()) {
                return "No JSON found in solver output.";
            }

            String jsonOutput = matcher.group(0);

            // Parse JSON and save to database
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(jsonOutput);

            if (!root.has("timetable")) {
                return "No timetable found in JSON.";
            }

            JsonNode timetableNode = root.get("timetable");
            List<ExamTableRecords> results = new ArrayList<>();

            for (JsonNode entry : timetableNode) {
                ExamTableRecords result = new ExamTableRecords();
                result.setCode(entry.get("code").asText());
                result.setDay(entry.get("day").asText());

                JsonNode hallsNode = entry.get("halls");
                String hallsString = "";
                if (hallsNode != null && hallsNode.isArray()) {
                    List<String> hallList = new ArrayList<>();
                    for (JsonNode hall : hallsNode) {
                        hallList.add(hall.asText());
                    }
                    hallsString = String.join(", ", hallList);
                }
                result.setHall(hallsString);

                result.setSlot(entry.get("slot").asInt());
                result.setStudents(entry.get("students").asInt());
                result.setDepartment(entry.get("department").asText());
                result.setSemester(entry.get("semester").asInt());
                result.setCommon(entry.get("iscommon").asBoolean());
                JsonNode nameNode = entry.get("name");
                result.setName(nameNode != null ? nameNode.asText() : "");

                results.add(result);
            }

            examSolverResultRepository.deleteAll();
            examSolverResultRepository.saveAll(results);

            return "Solver executed successfully. " + results.size() + " records saved.";

        } catch (Exception e) {
            e.printStackTrace();
            return "Error running solver: " + e.getMessage();
        }
    }

    public List<ExamTableRecords> getAllExamTableRecords() {
        return examSolverResultRepository.findAll();
    }
}
