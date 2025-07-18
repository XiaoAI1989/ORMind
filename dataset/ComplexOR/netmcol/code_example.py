from pulp import *
import numpy as np

def solve(data):
    Cities = data["Cities"]
    Links = data["Links"]
    Products = data["Products"]
    Supply = np.array(data["Supply"])
    Demand = np.array(data["Demand"])
    ShipmentCost = np.array(data["ShipmentCost"])
    Capacity = np.array(data["Capacity"])
    JointCapacity = np.array(data["JointCapacity"])

    prob = LpProblem("netmcol_Problem", LpMinimize)
    packages = LpVariable.dicts("Packages",
                                ((i, j, p) for i in range(Cities) for j in range(Cities) for p in range(Products)),
                                lowBound=0, cat='Integer')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "packages": {(i, j, p): packages[i, j, p].varValue
                         for i in range(Cities)
                         for j in range(Cities)
                         for p in range(Products)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}