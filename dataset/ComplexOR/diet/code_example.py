from pulp import *
import numpy as np

def solve(data):
    NutrientCount = data["NutrientCount"]
    FoodCount = data["FoodCount"]
    Cost = np.array(data["Cost"])
    FoodMin = np.array(data["FoodMin"])
    FoodMax = np.array(data["FoodMax"])
    NutrientMin = np.array(data["NutrientMin"])
    NutrientMax = np.array(data["NutrientMax"])
    AmountNutrient = np.array(data["AmountNutrient"])

    prob = LpProblem("Diet_Optimization", LpMinimize)
    x = LpVariable.dicts("Food", range(FoodCount), lowBound=0)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "x": {i: x[i].varValue for i in range(FoodCount)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}