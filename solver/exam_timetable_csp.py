"""
Exam timetable solver (converted from academic timetable)

- Loads modules and halls from the same Excel file/sheets you were using.
- Exams: 2 weeks (14 days), 2 slots per day (e.g., morning/afternoon).
- Each exam occupies exactly 1 slot (no durations).
- Each module scheduled exactly once (day, slot, hall).
- Hall capacity enforced.
- At most one exam per hall per (day, slot).
- Soft objective: minimize same-department overlaps at the same day+slot.
- Prints JSON output and human-readable grids.
"""

import pandas as pd
from ortools.sat.python import cp_model
import json

# ----------------------------
# 1. LOAD DATA
# ----------------------------
def load_data():
    file_path = "../data/planner_agent_data_nushan.xlsx"
    modules_df = pd.read_excel(file_path, sheet_name="module codes")
    halls_df = pd.read_excel(file_path, sheet_name="halls-exam")

    # Keep required columns; for exams we don't need duration
    modules_df = modules_df.dropna(subset=["module_code", "no_of_students"])
    modules_df["iscommon"] = modules_df.get("iscommon", False).fillna(False).astype(bool)
    modules_df["no_of_students"] = modules_df["no_of_students"].astype(int)

    modules = []
    for _, row in modules_df.iterrows():
        modules.append({
            "code": row["module_code"],
            # semester & department are optional but helpful for soft constraints
            "semester": int(row["semester"]) if "semester" in row and pd.notna(row["semester"]) else None,
            "iscommon": bool(row.get("iscommon", False)),
            "department": row.get("department", None),
            "students": int(row["no_of_students"])
        })

    halls = []
    for _, row in halls_df.iterrows():
        halls.append({
            "hall": row["room_name"],
            "capacity": int(row["capacity"]),
        })

    return modules, halls

# ----------------------------
# 2. BUILD EXAM MODEL
# ----------------------------
def build_exam_model(modules, halls, days, slots_per_day):
    model = cp_model.CpModel()

    num_days = len(days)
    num_slots = slots_per_day
    num_halls = len(halls)

    # Int vars per module for day and slot only (no single hall var any more)
    module_vars = {}
    for m in modules:
        code = m["code"]
        dvar = model.NewIntVar(0, num_days - 1, f"day_{code}")
        svar = model.NewIntVar(0, num_slots - 1, f"slot_{code}")
        module_vars[code] = {"day": dvar, "slot": svar}

    # presence[(code,d,s,h)] == True iff module code uses hall h at day d, slot s
    presence = {}
    for m in modules:
        code = m["code"]
        for d in range(num_days):
            for s in range(num_slots):
                for h in range(num_halls):
                    p = model.NewBoolVar(f"pres_{code}_d{d}_s{s}_h{h}")
                    presence[(code, d, s, h)] = p
                    # If p then day/slot equal (link to module_vars)
                    model.Add(module_vars[code]["day"] == d).OnlyEnforceIf(p)
                    model.Add(module_vars[code]["slot"] == s).OnlyEnforceIf(p)

    # assign_ds[(code,d,s)] == True iff module scheduled at day d & slot s (in >=1 hall)
    assign_ds = {}
    for m in modules:
        code = m["code"]
        for d in range(num_days):
            for s in range(num_slots):
                a = model.NewBoolVar(f"assign_{code}_d{d}_s{s}")
                assign_ds[(code, d, s)] = a
                # If any presence for that (d,s) then assign_ds must be true
                pres_over_halls = [presence[(code, d, s, h)] for h in range(num_halls)]
                # presence -> assign_ds
                for ph in pres_over_halls:
                    model.AddImplication(ph, a)
                # assign_ds -> at least one presence (i.e. module uses >=1 hall at that slot)
                model.Add(sum(pres_over_halls) >= 1).OnlyEnforceIf(a)
                # if not assigned then no presences
                for ph in pres_over_halls:
                    model.Add(ph == 0).OnlyEnforceIf(a.Not())

    # Exactly one (day,slot) per module
    for m in modules:
        code = m["code"]
        a_list = [assign_ds[(code, d, s)] for d in range(num_days) for s in range(num_slots)]
        model.AddExactlyOne(a_list)
        # Link assign_ds -> module_vars day/slot (redundant with presence->day/slot)
        # but ensures day/slot values correspond even if solver picks day/slot ints directly.
        for d in range(num_days):
            for s in range(num_slots):
                model.Add(module_vars[code]["day"] == d).OnlyEnforceIf(assign_ds[(code, d, s)])
                model.Add(module_vars[code]["slot"] == s).OnlyEnforceIf(assign_ds[(code, d, s)])

    # Hall capacity coverage: when a module is assigned at (d,s),
    # sum(capacity[h] * presence) >= students
    for m in modules:
        code = m["code"]
        students = m["students"]
        for d in range(num_days):
            for s in range(num_slots):
                pres_over_halls = [presence[(code, d, s, h)] for h in range(num_halls)]
                # Build linear expr sum(capacity * pres)
                coeffs = [halls[h]["capacity"] for h in range(num_halls)]
                # Add conditional capacity constraint only when assign_ds is true
                # sum(capacity[h] * pres_over_halls[h]) >= students  if assign_ds[(code,d,s)]
                # CP-SAT requires building a linear expression and using OnlyEnforceIf on the constraint.
                model.Add(
                    sum(coeffs[h] * pres_over_halls[h] for h in range(num_halls)) >= students
                ).OnlyEnforceIf(assign_ds[(code, d, s)])

    # At most one exam per hall per (day, slot)
    for d in range(num_days):
        for s in range(num_slots):
            for h_idx in range(num_halls):
                pres_list = [presence[(m["code"], d, s, h_idx)] for m in modules]
                model.Add(sum(pres_list) <= 1)

    # For the soft objective we can reuse assign_ds as dp[(code,d,s)]
    dp = assign_ds  # rename for clarity in rest of your code

    # Soft objective: minimize same-department overlaps at same day+slot
    overlap_vars = []
    # Build dept map (skip modules without department)
    dept_map = {}
    for m in modules:
        dept = m.get("department")
        if pd.isna(dept) or dept is None:
            continue
        dept_map.setdefault(dept, []).append(m)

    for dept, mod_list in dept_map.items():
        n = len(mod_list)
        for i in range(n):
            for j in range(i + 1, n):
                mi = mod_list[i]["code"]
                mj = mod_list[j]["code"]
                for d in range(num_days):
                    for s in range(num_slots):
                        ov = model.NewBoolVar(f"ov_{dept}_{mi}_{mj}_d{d}_s{s}")
                        overlap_vars.append(ov)
                        dpi = dp[(mi, d, s)]
                        dpj = dp[(mj, d, s)]
                        model.AddImplication(ov, dpi)
                        model.AddImplication(ov, dpj)
                        model.AddBoolOr([dpi.Not(), dpj.Not(), ov])

    # Objective: minimize overlaps if any
    if overlap_vars:
        model.Minimize(sum(overlap_vars))

    return model, module_vars, presence, dp


def generate_exam_json(status, solver, module_vars, modules, halls, days, presence):
    result = {
        "status": "INFEASIBLE" if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE) else "OPTIMAL",
        "timetable": []
    }

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return result

    for m in modules:
        code = m["code"]
        d = solver.Value(module_vars[code]["day"])
        s = solver.Value(module_vars[code]["slot"])

        # collect all halls used for this module at (d,s)
        hall_list = []
        for h_idx in range(len(halls)):
            if solver.Value(presence[(code, d, s, h_idx)]) == 1:
                hall_list.append(halls[h_idx])

        # distribute students among halls proportionally to capacity
        total_students = m["students"]
        distributed_students = []
        if hall_list:
            total_capacity = sum(h["capacity"] for h in hall_list)
            remaining_students = total_students
            for i, h in enumerate(hall_list):
                if i < len(hall_list) - 1:
                    # proportional allocation
                    allocated = min(remaining_students, int(total_students * h["capacity"] / total_capacity))
                    remaining_students -= allocated
                else:
                    # last hall gets remaining students
                    allocated = remaining_students
                distributed_students.append(f"{h['hall']}-{allocated}")

        entry = {
            "code": code,
            "day": days[d],
            "slot": int(s),
            "halls": [dstr for dstr in distributed_students],  # AUDI-200, AUDI2-27
            "students": total_students,
            "department": m.get("department"),
            "semester": m.get("semester"),
            "iscommon": m.get("iscommon", False)
        }
        result["timetable"].append(entry)

    return result



# ----------------------------
# Solve
# ----------------------------
def solve_model(model, time_limit_seconds=60, workers=8):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = workers
    status = solver.Solve(model)
    return status, solver

# ----------------------------
# Main
# ----------------------------
import json
def main():
    # 2 weeks (14 days)
    days = ["day1", "day2", "day3", "day4", "day5", "day6", "day7",
            "day8", "day9", "day10", "day11", "day12", "day13", "day14"]
    slots_per_day = 2  # two exam slots per day (morning, afternoon)

    modules, halls = load_data()
    # print_diagnostics(modules, halls, days, slots_per_day)

    model, module_vars, presence, dp = build_exam_model(modules, halls, days, slots_per_day)

    # Solve
    status, solver = solve_model(model, time_limit_seconds=60, workers=8)

    # Produce JSON and prints
    result_json = generate_exam_json(status, solver, module_vars, modules, halls, days, presence)
 

    print(json.dumps(result_json))

    # if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    #     # print_slot_expanded(solver, module_vars, modules, halls, days)
    #     # print_timetable_grid(solver, module_vars, modules, halls, days, slots_per_day)
    # else:
    #     print("No feasible solution found (INFEASIBLE or TIMEOUT).")

if __name__ == "__main__":
    main()
