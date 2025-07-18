from pulp import *
import numpy as np

def solve(data):
    NumItems = data["NumItems"]
    NumPeriods = data["NumPeriods"]
    Demand = np.array(data["Demand"])
    TotalPeriodCapacity = np.array(data["TotalPeriodCapacity"])
    ItemCapacity = np.array(data["ItemCapacity"])
    HoldingCost = np.array(data["HoldingCost"])
    BackorderCost = np.array(data["BackorderCost"])
    FixedCost = np.array(data["FixedCost"])
    InitialStock = np.array(data["InitialStock"])

    prob = LpProblem("Lot_Sizing_Problem", LpMinimize)
    production = LpVariable.dicts("Production", ((i, j) for i in range(NumItems) for j in range(NumPeriods)), lowBound=0, cat='Integer')
    setup = LpVariable.dicts("Setup", range(NumItems), cat='Binary')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "production": {(i, j): production[i, j].varValue
                           for i in range(NumItems)
                           for j in range(NumPeriods)},
            "setup": {i: setup[i].varValue
                      for i in range(NumItems)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}