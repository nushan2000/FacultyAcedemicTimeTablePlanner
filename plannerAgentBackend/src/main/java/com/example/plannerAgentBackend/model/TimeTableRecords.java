
// "duration": 2, "students": 200, "department": "EC"}, {"code": "EC3203", "day_index": 4, "day": "Fri", "hall_index": 1, "hall": "LT1", "slot": 0, "duration": 2, "students": 200, "department": "EC"}, {"code": "EC3404", "day_index": 3,
package com.example.plannerAgentBackend.model;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Entity
@Table(name="times")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TimeTableRecords {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "code", nullable = false)
    @NotNull(message = "Code cannot be null")
    private String code;

    @Column(name = "day_index", nullable = false)
    @NotNull(message = "Day index cannot be null")
    private Integer day_index;

    @Column(name = "day", nullable = false)
    @NotNull(message = "Day cannot be null")
    private String day;

    @Column(name = "hall_index", nullable = false)
    @NotNull(message = "Hall index cannot be null")
    private Integer hall_index;

    @Column(name = "hall", nullable = false)
    @NotNull(message = "Hall cannot be null")
    private String hall;

    @Column(name = "slot", nullable = false)
    @NotNull(message = "Slot cannot be null")
    private Integer slot;

    @Column(name = "duration", nullable = false)
    @NotNull(message = "Duration cannot be null")
    private Integer duration;

    @Column(name = "students", nullable = false)
    @NotNull(message = "Students cannot be null")
    private Integer students;

    @Column(name = "department", nullable = false)
    @NotNull(message = "Department cannot be null")
    private String department;

    

}
