from pulp import *
import numpy as np

def solve(data):
    TargetAudiences = data["TargetAudiences"]
    AdvertisingMedia = data["AdvertisingMedia"]
    Incidence = np.array(data["Incidence"])
    CostOfMedia = np.array(data["CostOfMedia"])

    prob = LpProblem("Media_Selection_Problem", LpMinimize)
    media_vars = LpVariable.dicts("Media", range(AdvertisingMedia), lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "media_vars": {m: media_vars[m].varValue for m in range(AdvertisingMedia)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}