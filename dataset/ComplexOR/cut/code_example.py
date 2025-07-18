from pulp import *
import numpy as np

def solve(data):
    NumWidths = data["NumWidths"]
    NumPatterns = data["NumPatterns"]
    Widths = np.array(data["Widths"])
    RollWidth = data["RollWidth"]
    Orders = np.array(data["Orders"])
    NumRollsWidthPattern = np.array(data["NumRollsWidthPattern"])

    prob = LpProblem("Cutting Stock Problem", LpMinimize)
    x = LpVariable.dicts("x", range(NumPatterns), lowBound=0, cat='Integer')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "x": {i: x[i].varValue for i in range(NumPatterns)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}