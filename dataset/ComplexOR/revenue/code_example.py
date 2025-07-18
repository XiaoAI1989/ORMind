from pulp import *
import numpy as np

def solve(data):
    FlightLegs = data["FlightLegs"]
    Packages = data["Packages"]
    AvailableSeats = np.array(data["AvailableSeats"])
    Demand = np.array(data["Demand"])
    Revenue = np.array(data["Revenue"])
    Delta = np.array(data["Delta"])

    prob = LpProblem("Aircraft_Assignment_Problem", LpMaximize)
    packages = LpVariable.dicts("Packages", range(Packages), lowBound=0, cat='Integer')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "packages": {i: packages[i].varValue for i in range(Packages)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}