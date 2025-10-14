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
    halls_df = pd.read_excel(file_path, sheet_name="halls")

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

    # Int vars per module to easily read solution
    module_vars = {}
    for m in modules:
        code = m["code"]
        dvar = model.NewIntVar(0, num_days - 1, f"day_{code}")
        svar = model.NewIntVar(0, num_slots - 1, f"slot_{code}")
        hvar = model.NewIntVar(0, num_halls - 1, f"hall_{code}")
        module_vars[code] = {"day": dvar, "slot": svar, "hall": hvar}

    # presence[(code,d,s,h)] == True iff module code is scheduled at day d, slot s, hall h
    presence = {}
    for m in modules:
        code = m["code"]
        for d in range(num_days):
            for s in range(num_slots):
                for h in range(num_halls):
                    p = model.NewBoolVar(f"pres_{code}_d{d}_s{s}_h{h}")
                    presence[(code, d, s, h)] = p
                    # If p then day/slot/hall equal
                    model.Add(module_vars[code]["day"] == d).OnlyEnforceIf(p)
                    model.Add(module_vars[code]["slot"] == s).OnlyEnforceIf(p)
                    model.Add(module_vars[code]["hall"] == h).OnlyEnforceIf(p)

    # Exactly one presence per module (choose exactly one (d,s,h))
    for m in modules:
        code = m["code"]
        pres_list = [presence[(code, d, s, h)] for d in range(num_days) for s in range(num_slots) for h in range(num_halls)]
        model.AddExactlyOne(pres_list)

    # Hall capacity: forbid presence where capacity < students
    for m in modules:
        code = m["code"]
        students = m["students"]
        for d in range(num_days):
            for s in range(num_slots):
                for h_idx, hall in enumerate(halls):
                    if hall["capacity"] < students:
                        model.Add(presence[(code, d, s, h_idx)] == 0)

    # At most one exam per hall per (day, slot)
    for d in range(num_days):
        for s in range(num_slots):
            for h_idx in range(num_halls):
                pres_list = [presence[(m["code"], d, s, h_idx)] for m in modules]
                model.Add(sum(pres_list) <= 1)

    # Build dp[(code,d,s)] : module scheduled at day d & slot s (in any hall)
    dp = {}
    for m in modules:
        code = m["code"]
        for d in range(num_days):
            for s in range(num_slots):
                var = model.NewBoolVar(f"dp_{code}_d{d}_s{s}")
                dp[(code, d, s)] = var
                pres_over_halls = [presence[(code, d, s, h)] for h in range(num_halls)]
                # var == OR(pres_over_halls)
                # If var true then at least one presence true
                model.AddBoolOr(pres_over_halls).OnlyEnforceIf(var)
                # If var false then all pres false
                for ph in pres_over_halls:
                    model.Add(ph == 0).OnlyEnforceIf(var.Not())

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
        # For each unordered pair of modules in the same dept
        for i in range(n):
            for j in range(i + 1, n):
                mi = mod_list[i]["code"]
                mj = mod_list[j]["code"]
                # If you prefer to only penalize same-semester overlaps, add check here using module's semester
                for d in range(num_days):
                    for s in range(num_slots):
                        ov = model.NewBoolVar(f"ov_{dept}_{mi}_{mj}_d{d}_s{s}")
                        overlap_vars.append(ov)
                        dpi = dp[(mi, d, s)]
                        dpj = dp[(mj, d, s)]
                        # ov -> dpi and ov -> dpj
                        model.AddImplication(ov, dpi)
                        model.AddImplication(ov, dpj)
                        # dpi and dpj -> ov  (equivalently: not(dpi and dpj) or ov)
                        model.AddBoolOr([dpi.Not(), dpj.Not(), ov])

    # Objective: minimize total overlaps (soft)
    if overlap_vars:
        model.Minimize(sum(overlap_vars))
    else:
        # no department info -> no objective, just find a feasible solution
        pass

    return model, module_vars, presence, dp

# ----------------------------
# Diagnostics & printing
# ----------------------------
# def print_diagnostics(modules, halls, days, slots_per_day):
#     print("\n[DIAGNOSTICS]")
#     print(f"  Number of modules: {len(modules)}")
#     print(f"  Days (slots): {len(days)} days, {slots_per_day} slots/day")
#     print(f"  Halls: {len(halls)}")
#     total_avail = len(days) * slots_per_day * len(halls)
#     print(f"  Total available exam slots (day*slot*hall): {total_avail}")
#     if halls:
#         print(f"  Largest hall capacity: {max(h['capacity'] for h in halls)}")
#     if modules:
#         print(f"  Largest class size: {max(m['students'] for m in modules)}")

# def print_timetable_grid(solver, module_vars, modules, halls, days, slots_per_day):
#     print("\nTIMETABLE (Day x Slot x Hall):")
#     header = "Day/Slot".ljust(12)
#     for h in halls:
#         header += f"{h['hall']:<18}"
#     print(header)
#     print("-" * (12 + 18 * len(halls)))
#     for d_idx, dname in enumerate(days):
#         for s in range(slots_per_day):
#             row = f"{dname}-{s}".ljust(12)
#             for h_idx, h in enumerate(halls):
#                 entry = "-"
#                 for m in modules:
#                     code = m["code"]
#                     if solver.Value(module_vars[code]["day"]) == d_idx and \
#                        solver.Value(module_vars[code]["slot"]) == s and \
#                        solver.Value(module_vars[code]["hall"]) == h_idx:
#                         entry = code
#                         break
#                 row += f"{entry:<18}"
#             print(row)
#         print("-" * (12 + 18 * len(halls)))

# def print_slot_expanded(solver, module_vars, modules, halls, days):
#     print("\nAll scheduled exams (expanded view):")
#     for m in modules:
#         code = m["code"]
#         d = solver.Value(module_vars[code]["day"])
#         s = solver.Value(module_vars[code]["slot"])
#         h = solver.Value(module_vars[code]["hall"])
#         print(f"{code}: Day={days[d]}, Slot={s}, Hall={halls[h]['hall']}, Students={m['students']}, Dept={m.get('department')}")

def generate_exam_json(status, solver, module_vars, modules, halls, days):
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
        h = solver.Value(module_vars[code]["hall"])
        entry = {
            "code": code,
            "day": days[d],
            "slot": int(s),
            "hall": halls[h]["hall"],
            "students": m["students"],
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
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
            "Mon2", "Tue2", "Wed2", "Thu2", "Fri2", "Sat2", "Sun2"]
    slots_per_day = 2  # two exam slots per day (morning, afternoon)

    modules, halls = load_data()
    # print_diagnostics(modules, halls, days, slots_per_day)

    model, module_vars, presence, dp = build_exam_model(modules, halls, days, slots_per_day)

    # Solve
    status, solver = solve_model(model, time_limit_seconds=60, workers=8)

    # Produce JSON and prints
    result_json = generate_exam_json(status, solver, module_vars, modules, halls, days)
 

    print(json.dumps(result_json))

    # if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    #     # print_slot_expanded(solver, module_vars, modules, halls, days)
    #     # print_timetable_grid(solver, module_vars, modules, halls, days, slots_per_day)
    # else:
    #     print("No feasible solution found (INFEASIBLE or TIMEOUT).")

if __name__ == "__main__":
    main()
