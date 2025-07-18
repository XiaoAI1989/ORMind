from pulp import *
import numpy as np

def solve(data):
    OriginNum = data["OriginNum"]
    DestinationNum = data["DestinationNum"]
    Supply = np.array(data["Supply"])
    Demand = np.array(data["Demand"])
    Cost = np.array(data["Cost"])

    prob = LpProblem("TSP_Problem", LpMinimize)
    routes = [(i, j) for i in range(OriginNum) for j in range(DestinationNum)]
    route = LpVariable.dicts("Route", routes, lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "route": {(i, j): route[i, j].varValue
                      for i in range(OriginNum)
                      for j in range(DestinationNum)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}