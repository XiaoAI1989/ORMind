from pulp import *
import numpy as np

def solve(data):
    Periods = data["Periods"]
    Demand = np.array(data["Demand"])
    CostFixed = np.array(data["CostFixed"])
    CostUnitOrder = np.array(data["CostUnitOrder"])
    CostUnitHold = np.array(data["CostUnitHold"])
    Penalty = np.array(data["Penalty"])
    ServiceLevel = data["ServiceLevel"]

    prob = LpProblem("Lot-Sizing with Service Level", LpMinimize)
    order_vars = LpVariable.dicts("Order", range(Periods), lowBound=0, cat=LpContinuous)
    inventory_vars = LpVariable.dicts("Inventory", range(Periods+1), lowBound=0, cat=LpContinuous)
    backlogged_vars = LpVariable.dicts("Backlogged", range(Periods+1), lowBound=0, cat=LpContinuous)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "order": {t: order_vars[t].varValue for t in range(Periods)},
            "inventory": {t: inventory_vars[t].varValue for t in range(Periods+1)},
            "backlogged": {t: backlogged_vars[t].varValue for t in range(Periods+1)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}