from pulp import *
import numpy as np

def solve(data):
    Producers = range(data["Producers"])
    Contracts = range(data["Contracts"])
    AvailableCapacity = np.array(data["AvailableCapacity"])
    ProductionCost = np.array(data["ProductionCost"])
    MinimalDelivery = np.array(data["MinimalDelivery"])
    ContractSize = np.array(data["ContractSize"])
    MinimalNumberofContributors = np.array(data["MinimalNumberofContributors"])

    prob = LpProblem("Contract Allocation Problem", LpMinimize)
    x = LpVariable.dicts("x", (Producers, Contracts), cat='Binary')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "x": {(i, j): x[i][j].varValue for i in Producers for j in Contracts}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}