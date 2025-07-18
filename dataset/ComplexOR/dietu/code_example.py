from pulp import *
import numpy as np

def solve(data):
    FoodNum = data["FoodNum"]
    NutrientNum = data["NutrientNum"]
    CostPerFood = np.array(data["CostPerFood"])
    FoodMin = np.array(data["FoodMin"])
    FoodMax = np.array(data["FoodMax"])
    MinReqAmount = np.array(data["MinReqAmount"])
    MaxReqAmount = np.array(data["MaxReqAmount"])
    AmountPerNutrient = np.array(data["AmountPerNutrient"])

    # Create the LP problem
    prob = LpProblem("Diet_Optimization", LpMinimize)
    food_vars = LpVariable.dicts("Food", range(FoodNum), lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "food_vars": {i: food_vars[i].varValue for i in range(FoodNum)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}