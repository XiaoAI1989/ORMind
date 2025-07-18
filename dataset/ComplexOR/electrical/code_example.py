from pulp import *
import numpy as np

def solve(data):
    GeneratorTypes = data["GeneratorTypes"]
    TimePeriods = data["TimePeriods"]
    OnStart = data["OnStart"]  # OnStart 是一个标量
    Generators = np.array(data["Generators"])
    Demand = np.array(data["Demand"])
    MinOutput = np.array(data["MinOutput"])
    MaxOutput = np.array(data["MaxOutput"])
    BaseCost = np.array(data["BaseCost"])
    PerMWCost = np.array(data["PerMWCost"])
    StartupCost = np.array(data["StartupCost"])

    prob = LpProblem("Power Generation Optimization", LpMinimize)
    on_off_vars = LpVariable.dicts("GeneratorOnOff", ((i, j) for i in range(GeneratorTypes) for j in range(TimePeriods)), cat='Binary')
    power_vars = LpVariable.dicts("GeneratorPower", ((i, j) for i in range(GeneratorTypes) for j in range(TimePeriods)), lowBound=0, upBound=None, cat='Continuous')
    startup_vars = LpVariable.dicts("GeneratorStartup", (i for i in range(GeneratorTypes)), lowBound=0, upBound=None, cat='Integer')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "on_off_vars": {(i, j): on_off_vars[i, j].varValue for i in range(GeneratorTypes) for j in range(TimePeriods)},
            "power_vars": {(i, j): power_vars[i, j].varValue for i in range(GeneratorTypes) for j in range(TimePeriods)},
            "startup_vars": {i: startup_vars[i].varValue for i in range(GeneratorTypes)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}