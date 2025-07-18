from pulp import *
import numpy as np

def solve(data):
    Tower = data["Tower"]
    Region = data["Region"]
    Delta = np.array(data["Delta"])
    Cost = np.array(data["Cost"])
    Population = np.array(data["Population"])
    Budget = data["Budget"]

    prob = LpProblem("Cell Tower Coverage Optimization", LpMaximize)
    tower_vars = LpVariable.dicts("Tower", range(Tower), 0, 1, LpBinary)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "tower_vars": {t: tower_vars[t].varValue for t in range(Tower)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}