from pulp import *
import numpy as np

def solve(data):
    Tasks = data["Tasks"]
    Machines = data["Machines"]
    ProcessingTime = np.array(data["ProcessingTime"])
    Delta = np.array(data["Delta"])
    BigM = data["BigM"]

    prob = LpProblem("Job_Problem", LpMinimize)

    Start = LpVariable.dicts("Start", ((j, m) for j in range(Tasks) for m in range(Machines)), lowBound=0)
    Completion = LpVariable.dicts("Completion", ((j, m) for j in range(Tasks) for m in range(Machines)), lowBound=0)
    Cmax = LpVariable("Cmax", lowBound=0)

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "Start": {(j, m): Start[j, m].varValue for j in range(Tasks) for m in range(Machines)},
            "Completion": {(j, m): Completion[j, m].varValue for j in range(Tasks) for m in range(Machines)},
            "Cmax": Cmax.varValue
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}