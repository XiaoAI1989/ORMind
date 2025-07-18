from pulp import *
import numpy as np

def solve(data):
    OriginNum = data["OriginNum"]
    DestinationNum = data["DestinationNum"]
    ProductNum = data["ProductNum"]
    Supply = np.array(data["Supply"])
    Demand = np.array(data["Demand"])
    Limit = np.array(data["Limit"])
    Cost = np.array(data["Cost"])

    prob = LpProblem("Multi-Commodity Transportation Problem", LpMinimize)
    ship = LpVariable.dicts("Ship", ((i, j, p) for i in range(OriginNum) for j in range(DestinationNum) for p in
                                     range(ProductNum)), lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "ship": {(i, j, p): ship[i, j, p].varValue
                     for i in range(OriginNum)
                     for j in range(DestinationNum)
                     for p in range(ProductNum)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}