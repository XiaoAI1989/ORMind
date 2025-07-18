from pulp import *
import numpy as np

def solve(data):
    NumProducts = data["NumProducts"]
    NumStages = data["NumStages"]
    ProductionRate = np.array(data["ProductionRate"])
    ProfitPerTon = np.array(data["ProfitPerTon"])
    MinCommitment = np.array(data["MinCommitment"])
    MaxMarketLimit = np.array(data["MaxMarketLimit"])
    StageAvailability = np.array(data["StageAvailability"])

    prob = LpProblem("steel4_Problem", LpMaximize)
    Production = LpVariable.dicts("Production", range(NumProducts), lowBound=0)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "Production": {i: Production[i].varValue for i in range(NumProducts)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}