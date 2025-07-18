from pulp import *
import numpy as np

def solve(data):

    TotalAircraft = data["TotalAircraft"]
    TotalRoutes = data["TotalRoutes"]
    Availability = np.array(data["Availability"])
    Demand = np.array(data["Demand"])
    Capacity = np.array(data["Capacity"])
    Costs = np.array(data["Costs"])

    prob = LpProblem("Aircraft Assignment", LpMinimize)
    aircraft_route = LpVariable.dicts("Assign", ((i, j) for i in range(TotalAircraft) for j in range(TotalRoutes)),
                                           0, 1, LpBinary)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables
        optimized_vars = {"aircraft_route": {(i, j): aircraft_route[(i, j)].varValue
                                 for i in range(TotalAircraft)
                                 for j in range(TotalRoutes)}}
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}

