package com.example.plannerAgentBackend.service;

import com.example.plannerAgentBackend.model.Hall;
import com.example.plannerAgentBackend.model.ModuleEntity;
import com.example.plannerAgentBackend.repository.HallRepository;
import com.example.plannerAgentBackend.repository.ModuleRepository;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Service
public class ExcelService {

    @Autowired
    private ModuleRepository moduleRepo;

    @Autowired
    private SolverService solverService;

    @Autowired
    private SolverExamService solverExamService;

    @Autowired
    private HallRepository hallRepo;

    public void saveExcelData(MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("File is empty");
        }

        try (Workbook workbook = new XSSFWorkbook(file.getInputStream())) {
            // Read "module codes" sheet
            processModuleSheet(workbook);

            // Read "halls" sheet
            processHallSheet(workbook);
            solverService.runSolver();
        }
    }
    public void saveExamExcelData(MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("File is empty");
        }

        try (Workbook workbook = new XSSFWorkbook(file.getInputStream())) {
            // Read "module codes" sheet
            processModuleSheet(workbook);

            // Read "halls" sheet
            processHallSheet(workbook);
            solverExamService.runExamSolver();
        }
    }

    private void processModuleSheet(Workbook workbook) {
        Sheet moduleSheet = workbook.getSheet("module codes");
        if (moduleSheet == null) {
            throw new IllegalArgumentException("Sheet 'module codes' not found");
        }

        FormulaEvaluator evaluator = workbook.getCreationHelper().createFormulaEvaluator();
        List<ModuleEntity> moduleEntities = new ArrayList<>();

        // 🧹 Clear existing data before saving new
        moduleRepo.deleteAll();

        for (Row row : moduleSheet) {
            if (row.getRowNum() == 0) continue; // skip header

            String moduleCode = getEvaluatedStringCellValue(row.getCell(2), evaluator).trim();
            if (moduleCode.isEmpty()) continue; // 🛑 skip empty module_code rows

            ModuleEntity module = new ModuleEntity();
            module.setModuleCode(moduleCode);
            module.setSemester((int) getEvaluatedNumericCellValue(row.getCell(1), evaluator));
            module.setDuration((int) getEvaluatedNumericCellValue(row.getCell(3), evaluator));
            module.setDepartment(getEvaluatedStringCellValue(row.getCell(5), evaluator));
            module.setIsCommon(getEvaluatedBooleanCellValue(row.getCell(4), evaluator));
            module.setNoOfStudents((int) getEvaluatedNumericCellValue(row.getCell(6), evaluator));

            moduleEntities.add(module);
        }

        if (!moduleEntities.isEmpty()) {
            moduleRepo.saveAll(moduleEntities);
        }
    }

    private String getEvaluatedStringCellValue(Cell cell, FormulaEvaluator evaluator) {
        if (cell == null) return "";
        CellValue cellValue = evaluator.evaluate(cell);
        if (cellValue == null) return "";
        switch (cellValue.getCellType()) {
            case STRING: return cellValue.getStringValue().trim();
            case NUMERIC: return String.valueOf((int) cellValue.getNumberValue());
            case BOOLEAN: return String.valueOf(cellValue.getBooleanValue());
            default: return "";
        }
    }

    private double getEvaluatedNumericCellValue(Cell cell, FormulaEvaluator evaluator) {
        if (cell == null) return 0;
        CellValue cellValue = evaluator.evaluate(cell);
        if (cellValue == null) return 0;
        return cellValue.getNumberValue();
    }

    private boolean getEvaluatedBooleanCellValue(Cell cell, FormulaEvaluator evaluator) {
        if (cell == null) return false;
        CellValue cellValue = evaluator.evaluate(cell);
        if (cellValue == null) return false;
        if (cellValue.getCellType() == CellType.BOOLEAN) {
            return cellValue.getBooleanValue();
        } else if (cellValue.getCellType() == CellType.STRING) {
            return Boolean.parseBoolean(cellValue.getStringValue());
        } else {
            return false;
        }
    }


    private void processHallSheet(Workbook workbook) {
        Sheet hallSheet = workbook.getSheet("halls");
        if (hallSheet == null) {
            throw new IllegalArgumentException("Sheet 'halls' not found");
        }
        FormulaEvaluator evaluator = workbook.getCreationHelper().createFormulaEvaluator();
        List<Hall> halls = new ArrayList<>();
        hallRepo.deleteAll();

        for (Row row : hallSheet) {
            if (row.getRowNum() == 0) continue;

            String hallsCode=getEvaluatedStringCellValue(row.getCell(2),evaluator ).trim();
            if (hallsCode.isEmpty()) continue;

            Hall hall = new Hall();
            hall.setRoomName(getEvaluatedStringCellValue(row.getCell(4), evaluator));
            hall.setCapacity((int) getEvaluatedNumericCellValue(row.getCell(7), evaluator));
            halls.add(hall);
        }

        if (!halls.isEmpty()) {
            hallRepo.saveAll(halls);
        }
    }

}