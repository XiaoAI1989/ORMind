from pulp import *
import numpy as np


def solve(data):
    TotalAircrafts = data["TotalAircrafts"]
    EarliestLandingTime = np.array(data["EarliestLandingTime"])
    LatestLandingTime = np.array(data["LatestLandingTime"])
    TargetLandingTime = np.array(data["TargetLandingTime"])
    PenaltyTimeAfterTarget = np.array(data["PenaltyTimeAfterTarget"])
    PenaltyTimeBeforeTarget = np.array(data["PenaltyTimeBeforeTarget"])
    SeparationTimeMatrix = np.array(data["SeparationTimeMatrix"])

    prob = LpProblem("Aircraft Landing Problem", LpMinimize)

  ###########TODO##########

    prob.solve()
    optimized_vars={}
    if prob.status == LpStatusOptimal:
        # Extract the optimized variables
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}


