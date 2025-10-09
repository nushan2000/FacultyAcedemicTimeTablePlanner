"""
Timetable solver with SOFT department overlap penalty.

- Loads modules and halls from Excel
- Enforces hall capacity >= students
- Enforces duration (consecutive slots)
- No overlapping modules in same hall/day (hard)
- Each module scheduled exactly once (hard)
- Prefers to avoid overlaps between modules of the same department across halls (soft)
  by minimizing the number of same-department overlaps.
"""

import pandas as pd
from ortools.sat.python import cp_model


# ----------------------------
# 1. LOAD DATA
# ----------------------------
def load_data():
    file_path = "../data/planner_agent_data_nushan.xlsx"
    modules_df = pd.read_excel(file_path, sheet_name="module codes")
    halls_df = pd.read_excel(file_path, sheet_name="halls")

    modules_df = modules_df.dropna(subset=["semester", "duration", "module_code", "no_of_students"])
    modules_df["semester"] = modules_df["semester"].astype(int)
    modules_df["duration"] = modules_df["duration"].astype(int)
    modules_df["iscommon"] = modules_df.get("iscommon", False).fillna(False).astype(bool)
    modules_df["no_of_students"] = modules_df["no_of_students"].astype(int)

    modules = []
    for _, row in modules_df.iterrows():
        modules.append({
            "code": row["module_code"],
            "semester": int(row["semester"]),
            "duration": int(row["duration"]),
            "iscommon": bool(row["iscommon"]),
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
# 2. BUILD MODEL
# ----------------------------
def build_model(modules, halls, days, slots_per_day):
    model = cp_model.CpModel()

    module_vars = {}         # code -> vars dict
    presence_vars = {}       # (code, day_idx, hall_idx) -> Bool

    # --- Module variables
    for m in modules:
        code = m["code"]
        dur = m["duration"]
        day_var = model.NewIntVar(0, len(days) - 1, f"day_{code}")
        hall_var = model.NewIntVar(0, len(halls) - 1, f"hall_{code}")
        slot_var = model.NewIntVar(0, slots_per_day - dur, f"slot_{code}")
        end_var = model.NewIntVar(0, slots_per_day, f"end_{code}")
        model.Add(end_var == slot_var + dur)

        module_vars[code] = {
            "day": day_var,
            "hall": hall_var,
            "slot": slot_var,
            "end": end_var,
            "dur": dur
        }

    # --- Presence variables & hall-level optional intervals (hard no-overlap)
    for d_idx in range(len(days)):
        for h_idx in range(len(halls)):
            intervals = []
            for m in modules:
                code = m["code"]
                dur = m["duration"]
                pres = model.NewBoolVar(f"pres_{code}_d{d_idx}_h{h_idx}")
                presence_vars[(code, d_idx, h_idx)] = pres

                # Link presence to module's day/hall
                model.Add(module_vars[code]["day"] == d_idx).OnlyEnforceIf(pres)
                model.Add(module_vars[code]["hall"] == h_idx).OnlyEnforceIf(pres)

                interval = model.NewOptionalIntervalVar(
                    module_vars[code]["slot"], dur, module_vars[code]["end"], pres,
                    f"int_{code}_d{d_idx}_h{h_idx}"
                )
                intervals.append(interval)

            if intervals:
                model.AddNoOverlap(intervals)

    # --- Exactly one presence per module (hard)
    for m in modules:
        code = m["code"]
        pres_list = [presence_vars[(code, d, h)] for d in range(len(days)) for h in range(len(halls))]
        model.AddExactlyOne(pres_list)

    # --- Hall capacity (hard)
    for m in modules:
        code = m["code"]
        for h_idx, hall in enumerate(halls):
            if hall["capacity"] < m["students"]:
                for d in range(len(days)):
                    model.Add(presence_vars[(code, d, h_idx)] == 0)

    # --- Day-presence variable for each module+day
    day_presence = {}  # (code, day_idx) -> Bool
    for m in modules:
        code = m["code"]
        for d_idx in range(len(days)):
            dp = model.NewBoolVar(f"daypres_{code}_d{d_idx}")
            pres_list = [presence_vars[(code, d_idx, h)] for h in range(len(halls))]
            model.AddBoolOr(pres_list).OnlyEnforceIf(dp)
            model.AddBoolAnd([p.Not() for p in pres_list]).OnlyEnforceIf(dp.Not())
            day_presence[(code, d_idx)] = dp

    # --- SAME-DEPARTMENT NO-SLOT-CONFLICT constraint (hard)
    dept_map = {}
    for m in modules:
        dept = m.get("department")
        if not dept:
            continue
        dept_map.setdefault(dept, []).append(m)

        # --- SAME-DEPARTMENT + SAME-SEMESTER NO-SLOT-CONFLICT (hard)
        # --- SAME-DEPARTMENT + SAME-SEMESTER NO-TIME-OVERLAP (hard)
        # --- SAME-DEPARTMENT + SAME-SEMESTER NO-TIME-OVERLAP (hard)
    for dept, mod_list in dept_map.items():
        n = len(mod_list)
        for i in range(n):
            for j in range(i + 1, n):
                mi = mod_list[i]
                mj = mod_list[j]

                # Apply restriction only if same semester
                if mi["semester"] != mj["semester"]:
                    continue

                ci = mi["code"]
                cj = mj["code"]

                for d_idx in range(len(days)):
                    both_on_same_day = [day_presence[(ci, d_idx)], day_presence[(cj, d_idx)]]

                    # Boolean vars to represent ordering
                    ci_before_cj = model.NewBoolVar(f"{ci}_before_{cj}_d{d_idx}")
                    cj_before_ci = model.NewBoolVar(f"{cj}_before_{ci}_d{d_idx}")

                    # If ci_before_cj → ci.end <= cj.slot
                    model.Add(module_vars[ci]["end"] <= module_vars[cj]["slot"]).OnlyEnforceIf(ci_before_cj)
                    # If cj_before_ci → cj.end <= ci.slot
                    model.Add(module_vars[cj]["end"] <= module_vars[ci]["slot"]).OnlyEnforceIf(cj_before_ci)

                    # Ensure at least one of these two orderings holds when both are on the same day
                    model.AddBoolOr([ci_before_cj, cj_before_ci]).OnlyEnforceIf(both_on_same_day)




    return model, module_vars, presence_vars, day_presence


# ----------------------------
# Diagnostics & printing
# ----------------------------
def print_diagnostics(modules, halls, days, slots_per_day):
    total_req = sum(m["duration"] for m in modules)
    total_avail = len(days) * len(halls) * slots_per_day
    print("\n[DIAGNOSTICS]")
    print(f"  Total required slot-hours: {total_req}")
    print(f"  Total available slot-hours: {total_avail}")
    print(f"  Largest hall capacity: {max(h['capacity'] for h in halls)}")
    print(f"  Largest class size: {max(m['students'] for m in modules)}")
    print(f"  Max module duration: {max(m['duration'] for m in modules)}")
    print(f"  Min module duration: {min(m['duration'] for m in modules)}")


def print_timetable_grid(solver, module_vars, modules, halls, days, slots_per_day):
    print("\nTIMETABLE GRID (Day x Slot x Hall):")
    print("-" * (20 * (len(halls) + 1)))
    print(f"{'Slot/Day':<20}", end="")
    for h in halls:
        print(f"{h['hall']:<20}", end="")
    print()
    print("-" * (20 * (len(halls) + 1)))

    for d_idx, dname in enumerate(days):
        for slot in range(slots_per_day):
            print(f"{dname}-{slot:<12}", end="")
            for h_idx, h in enumerate(halls):
                entry = "-"
                for m in modules:
                    code = m["code"]
                    m_day = solver.Value(module_vars[code]["day"])
                    m_hall = solver.Value(module_vars[code]["hall"])
                    m_slot = solver.Value(module_vars[code]["slot"])
                    m_end = solver.Value(module_vars[code]["end"])
                    if m_day == d_idx and m_hall == h_idx and m_slot <= slot < m_end:
                        entry = code
                        break
                print(f"{entry:<20}", end="")
            print()
        print("-" * (20 * (len(halls) + 1)))


# ----------------------------
# Solve (refactored to return solver + status)
# ----------------------------
def solve_model(model, module_vars, modules, halls, days, slots_per_day):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    # if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    #     # Compact list: one line per module
    #     for m in modules:
    #         code = m["code"]
    #         d = solver.Value(module_vars[code]["day"])
    #         h = solver.Value(module_vars[code]["hall"])
    #         s = solver.Value(module_vars[code]["slot"])
    #         print(f"{code}: Day={days[d]}, Hall={halls[h]['hall']}, Slot={s}, Dur={m['duration']}")
    # else:
    #     print("No feasible solution found.")

    # Return solver & status so caller can inspect further (e.g. expanded slots)
    return status, solver

# ----------------------------
# Expanded slot view (one line per occupied slot)
# ----------------------------
def print_slot_expanded(solver, module_vars, modules, halls, days):
    print("\nAll occupied slots (expanded view):")
    for m in modules:
        code = m["code"]
        d = solver.Value(module_vars[code]["day"])
        h = solver.Value(module_vars[code]["hall"])
        start = solver.Value(module_vars[code]["slot"])
        dur = m["duration"]
        for s in range(start, start + dur):
            print(f"{code}: Day={days[d]}, Hall={halls[h]['hall']}, Slot={s}")

import json
def generate_expanded_json(status, solver, module_vars, modules, halls, days):
    result = {
        "status": "INFEASIBLE" if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE) else "OPTIMAL",
        "timetable": []
    }

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return result

    # Create one entry per occupied slot
    for m in modules:
        code = m["code"]
        d = solver.Value(module_vars[code]["day"])
        h = solver.Value(module_vars[code]["hall"])
        start = solver.Value(module_vars[code]["slot"])
        dur = m["duration"]

        for s in range(start, start + dur):
            entry = {
                "code": code,
                "day": days[d],
                "hall": halls[h]["hall"],
                "slot": s,
                "duration": dur,
                "students": m["students"],
                "department": m["department"],
                "semester": m["semester"],
                "iscommon": m["iscommon"]
            }
            result["timetable"].append(entry)

    return result


# ----------------------------
# Main
# ----------------------------
def main():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    slots_per_day = 8

    modules, halls = load_data()
    model, module_vars, presence_vars, day_presence = build_model(modules, halls, days, slots_per_day)

    status, solver = solve_model(model, module_vars, modules, halls, days, slots_per_day)

    result_json = generate_expanded_json(status, solver, module_vars, modules, halls, days)

    # 👉 Count and print how many JSON objects (timetable entries) are generated

    # 👇 Print JSON for Spring Boot to read
    print(json.dumps(result_json, indent=2))
    print(f"\nTotal JSON objects: {len(result_json['timetable'])}\n")

    # Only print expanded view if we found a solution
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print_slot_expanded(solver, module_vars, modules, halls, days)

if __name__ == "__main__":
    main()
