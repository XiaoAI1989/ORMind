from pulp import *
import numpy as np

def solve(data):
    TotalItems = data["TotalItems"]
    ItemValues = np.array(data["ItemValues"])
    ItemWeights = np.array(data["ItemWeights"])
    MaxKnapsackWeight = data["MaxKnapsackWeight"]

    prob = LpProblem("Knapsack Problem", LpMaximize)
    x = LpVariable.dicts("Item", range(TotalItems), 0, 1, LpBinary)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "x": {i: x[i].varValue for i in range(TotalItems)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}