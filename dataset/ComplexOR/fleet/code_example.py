from pulp import *
import numpy as np

def solve(data):
    Locations = data["Locations"]
    Planes = data["Planes"]
    Periods = data["Periods"]
    Capacity = np.array(data["Capacity"])
    Cost = np.array(data["Cost"])
    AvailablePlanes = np.array(data["AvailablePlanes"])
    Delta = np.array(data["Delta"])
    NumberOfPassengers = np.array(data["NumberOfPassengers"])

    prob = LpProblem("Aircraft_Assignment_Problem", LpMinimize)
    planes_assigned = LpVariable.dicts("PlanesAssigned", ((i, t, v) for i in range(Locations) for t in range(Periods) for v in range(Planes)), lowBound=0, cat='Integer')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "planes_assigned": {(i, t, v): planes_assigned[i, t, v].varValue
                                for i in range(Locations)
                                for t in range(Periods)
                                for v in range(Planes)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}