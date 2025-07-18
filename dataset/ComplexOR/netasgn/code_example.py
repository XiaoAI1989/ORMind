from pulp import *
import numpy as np

def solve(data):
    People = data["People"]
    Projects = data["Projects"]
    Supply = np.array(data["Supply"])
    Demand = np.array(data["Demand"])
    Cost = np.array(data["Cost"])
    Limit = np.array(data["Limit"])

    prob = LpProblem("Project Assignment", LpMinimize)
    hours = LpVariable.dicts("hours", ((i, j) for i in range(People) for j in range(Projects)), lowBound=0)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "hours": {(i, j): hours[i, j].varValue
                      for i in range(People)
                      for j in range(Projects)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}