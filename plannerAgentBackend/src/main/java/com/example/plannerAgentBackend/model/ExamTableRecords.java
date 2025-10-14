
// "duration": 2, "students": 200, "department": "EC"}, {"code": "EC3203", "day_index": 4, "day": "Fri", "hall_index": 1, "hall": "LT1", "slot": 0, "duration": 2, "students": 200, "department": "EC"}, {"code": "EC3404", "day_index": 3,
package com.example.plannerAgentBackend.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name="examTimes")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ExamTableRecords {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String code;
    private String day;
    private String hall;
    private int slot;
//    private int duration;
    private int students;
    private String department;
    private int semester;
    private boolean isCommon;

}
