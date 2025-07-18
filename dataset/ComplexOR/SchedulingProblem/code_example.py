from pulp import *
import numpy as np

def solve(data):
    NumRestaurants = data["NumRestaurants"]
    NumEmployees = data["NumEmployees"]
    NumShifts = data["NumShifts"]
    NumSkills = data["NumSkills"]
    Demand = np.array(data["Demand"])
    EmployeeSkills = np.array(data["EmployeeSkills"])
    SkillPreference = np.array(data["SkillPreference"])
    ShiftAvailability = np.array(data["ShiftAvailability"])
    UnfulfilledPositionWeight = data["UnfulfilledPositionWeight"]

    prob = LpProblem("Employee_Assignment_Problem", LpMinimize)
    assignment = LpVariable.dicts("Assignment", ((i, j, k) for i in range(NumEmployees) for j in range(NumShifts) for k in range(NumRestaurants)), 0, 1, LpBinary)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "assignment": {(i, j, k): assignment[i, j, k].varValue
                           for i in range(NumEmployees)
                           for j in range(NumShifts)
                           for k in range(NumRestaurants)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}