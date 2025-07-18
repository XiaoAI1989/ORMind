from pulp import *
import numpy as np

def solve(data):
    Cities = data["Cities"]
    Links = data["Links"]
    Supply = np.array(data["Supply"])
    Demand = np.array(data["Demand"])
    ShippingCost = np.array(data["ShippingCost"])
    Capacity = np.array(data["Capacity"])

    prob = LpProblem("Network Flow Problem", LpMinimize)
    packages = LpVariable.dicts("Packages", ((i, j) for i in range(Cities) for j in range(Cities)), lowBound=0, cat='Integer')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "packages": {(i, j): packages[i, j].varValue
                         for i in range(Cities)
                         for j in range(Cities)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}