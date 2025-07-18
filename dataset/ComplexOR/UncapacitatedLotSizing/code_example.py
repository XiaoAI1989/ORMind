from pulp import *
import numpy as np

def solve(data):
    periods = data["Periods"]
    demand = np.array(data["Demand"])
    cost_fixed = np.array(data["CostFixed"])
    cost_unit_order = np.array(data["CostUnitOrder"])
    cost_unit_hold = np.array(data["CostUnitHold"])

    prob = LpProblem("UncapacitatedLotSizing", LpMinimize)
    Order_Quantity = LpVariable.dicts("Order_Quantity", range(periods), lowBound=0, cat='Continuous')
    Inventory_Level = LpVariable.dicts("Inventory_Level", range(periods + 1), lowBound=0, cat='Continuous')
    Ordering_Binary = LpVariable.dicts("Ordering_Binary", range(periods), cat='Binary')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "Order_Quantity": {t: Order_Quantity[t].varValue for t in range(periods)},
            "Inventory_Level": {t: Inventory_Level[t].varValue for t in range(periods + 1)},
            "Ordering_Binary": {t: Ordering_Binary[t].varValue for t in range(periods)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}