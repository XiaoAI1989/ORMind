from pulp import *
import numpy as np

def solve(data):
    ProductNum = data["ProductNum"]
    ProductionRate = np.array(data["ProductionRate"])
    ProfitPerTon = np.array(data["ProfitPerTon"])
    MinimumSale = np.array(data["MinimumSale"])
    MaximumSale = np.array(data["MaximumSale"])
    AvailableHours = data["AvailableHours"]

    prob = LpProblem("Steel3_Problem", LpMaximize)
    tons = LpVariable.dicts("Tons", range(ProductNum), lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "tons": {i: tons[i].varValue for i in range(ProductNum)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}