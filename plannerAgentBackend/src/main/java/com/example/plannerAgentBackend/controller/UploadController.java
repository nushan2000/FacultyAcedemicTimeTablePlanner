package com.example.plannerAgentBackend.controller;

import com.example.plannerAgentBackend.service.ExcelService;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.ss.usermodel.WorkbookFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.file.Paths;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:3000")
public class UploadController {
    @Autowired
    private ExcelService excelService;

    private final String uploadDir = "uploaded_excels";
    private final String examUploadDir = "uploaded_exams"; // folder to save Exam files

    @PostMapping("/upload")
    public ResponseEntity<?> uploadExcel(@RequestParam("file") MultipartFile file) {
        if (file == null || file.isEmpty()) {
            return ResponseEntity.badRequest().body("No file uploaded or file is empty.");
        }

        String filename = file.getOriginalFilename();
        if (filename == null ||
                (!filename.endsWith(".xls") && !filename.endsWith(".xlsx"))) {
            return ResponseEntity.badRequest()
                    .body("Invalid file type. Only Excel files (.xls, .xlsx) are allowed.");
        }

        try {
            // --- VALIDATE EXCEL CONTENT FIRST ---
            try (InputStream inputStream = file.getInputStream();
                 Workbook workbook = WorkbookFactory.create(inputStream)) {

                boolean hasModuleSheet = workbook.getSheet("module codes") != null;
                boolean hasHallsSheet = workbook.getSheet("halls") != null;

                if (!hasModuleSheet || !hasHallsSheet) {
                    String missingSheets = (!hasModuleSheet ? "module codes " : "") +
                            (!hasHallsSheet ? "halls" : "");
                    return ResponseEntity.badRequest()
                            .body("Excel validation failed. Missing sheet(s): " + missingSheets.trim());
                }
            } catch (org.apache.poi.openxml4j.exceptions.OLE2NotOfficeXmlFileException |
                     org.apache.poi.poifs.filesystem.NotOLE2FileException e) {
                return ResponseEntity.badRequest().body("Invalid file content. Please upload a valid Excel file.");
            }
            excelService.saveExcelData(file);
            // --- SAVE FILE AFTER SUCCESSFUL VALIDATION ---
            File dir = new File(uploadDir);
            if (!dir.exists()) dir.mkdirs();

            String filePath = Paths.get(uploadDir, filename).toString();
            try (FileOutputStream fos = new FileOutputStream(filePath)) {
                fos.write(file.getBytes());
            }

            return ResponseEntity.ok("Excel uploaded, validated, and saved successfully at: " + filePath);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500).body("Server error: " + e.getMessage());
        }
    }

    @PostMapping("/uploadExam")
    public ResponseEntity<?> uploadExamExcel(@RequestParam("file") MultipartFile file) {
    if (file == null || file.isEmpty()) {
            return ResponseEntity.badRequest().body("No file uploaded or file is empty.");
        }

        String filename = file.getOriginalFilename();
        if (filename == null ||
                (!filename.endsWith(".xls") && !filename.endsWith(".xlsx"))) {
            return ResponseEntity.badRequest()
                    .body("Invalid file type. Only Excel files (.xls, .xlsx) are allowed.");
        }

        try {
            // --- VALIDATE EXCEL CONTENT FIRST ---
            try (InputStream inputStream = file.getInputStream();
                 Workbook workbook = WorkbookFactory.create(inputStream)) {

                boolean hasModuleSheet = workbook.getSheet("module codes") != null;
                boolean hasHallsSheet = workbook.getSheet("halls") != null;

                if (!hasModuleSheet || !hasHallsSheet) {
                    String missingSheets = (!hasModuleSheet ? "module codes " : "") +
                            (!hasHallsSheet ? "halls" : "");
                    return ResponseEntity.badRequest()
                            .body("Excel validation failed. Missing sheet(s): " + missingSheets.trim());
                }
            } catch (org.apache.poi.openxml4j.exceptions.OLE2NotOfficeXmlFileException |
                     org.apache.poi.poifs.filesystem.NotOLE2FileException e) {
                return ResponseEntity.badRequest().body("Invalid file content. Please upload a valid Excel file.");
            }
            excelService.saveExamExcelData(file);
            // --- SAVE FILE AFTER SUCCESSFUL VALIDATION ---
            File dir = new File(examUploadDir);
            if (!dir.exists()) dir.mkdirs();

            String filePath = Paths.get(examUploadDir, filename).toString();
            try (FileOutputStream fos = new FileOutputStream(filePath)) {
                fos.write(file.getBytes());
            }

            return ResponseEntity.ok("Excel uploaded, validated, and saved successfully at: " + filePath);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500).body("Server error: " + e.getMessage());
        }
    }


}
