from pulp import *
import numpy as np


def solve(data):
    AlloysOnMarket = data["AlloysOnMarket"]
    RequiredElements = data["RequiredElements"]
    CompositionDataPercentage = np.array(data["CompositionDataPercentage"])
    DesiredBlendPercentage = np.array(data["DesiredBlendPercentage"])
    AlloyPrice = np.array(data["AlloyPrice"])

    prob = LpProblem("Alloy Blending Optimization", LpMinimize)
    # Define decision variables
    alloys_used = LpVariable.dicts("Alloy", range(AlloysOnMarket), lowBound=0, cat='Continuous')
  ###########TODO##########

    prob.solve()


    if prob.status == LpStatusOptimal:
        # Extract the optimized variables
        optimized_vars = {"alloys_used": {a: alloys_used[a].varValue for a in range(AlloysOnMarket)}}
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}

