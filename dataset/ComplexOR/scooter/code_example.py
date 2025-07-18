from pulp import *
import numpy as np

def solve(data):
    DemandPoints = data["DemandPoints"]
    CandidateLocations = data["CandidateLocations"]
    EstimatedDemand = np.array(data["EstimatedDemand"])
    Distance = np.array(data["Distance"])
    NumAvailableScooters = data["NumAvailableScooters"]
    MaxSelectedLocations = data["MaxSelectedLocations"]
    NewMax = data["NewMax"]

    prob = LpProblem("Scooter_Assignment_Problem", LpMinimize)
    assign = LpVariable.dicts("Assign", [(i, j) for i in range(DemandPoints) for j in range(CandidateLocations)], 0, 1, LpBinary)
    newScooters = LpVariable.dicts("NewScooters", range(CandidateLocations), 0, NewMax, LpInteger)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "assign": {(i, j): assign[i, j].varValue
                       for i in range(DemandPoints)
                       for j in range(CandidateLocations)},
            "newScooters": {j: newScooters[j].varValue
                            for j in range(CandidateLocations)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}