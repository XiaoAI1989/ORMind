from pulp import *
import numpy as np

def solve(data):
    number_of_origins = data["NumberOfOrigins"]
    number_of_destinations = data["NumberOfDestinations"]
    supply_of_origin = np.array(data["SupplyOfOrigin"])
    demand_of_destination = np.array(data["DemandOfDestination"])
    cost_per_unit = np.array(data["CostPerUnit"])

    prob = LpProblem("Aircraft_Assignment_Problem", LpMinimize)
    transport_vars = LpVariable.dicts("Transport",
                                      ((i, j) for i in range(number_of_origins) for j in range(number_of_destinations)),
                                      lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "transport_vars": {(i, j): transport_vars[i, j].varValue
                               for i in range(number_of_origins)
                               for j in range(number_of_destinations)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}