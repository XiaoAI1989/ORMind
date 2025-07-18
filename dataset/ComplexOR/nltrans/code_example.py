from pulp import *
import numpy as np

def solve(data):
    origins = data["Origins"]
    destinations = data["Destinations"]
    supply = np.array(data["Supply"])
    demand = np.array(data["Demand"])
    rate = np.array(data["Rate"])
    limit = np.array(data["Limit"])

    prob = LpProblem("nltrans_Problem", LpMinimize)
    shipment = LpVariable.dicts("shipment",
                         ((i, j) for i in range(origins) for j in range(destinations)),
                         lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "shipment": {(i, j): shipment[i, j].varValue
                         for i in range(origins)
                         for j in range(destinations)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}