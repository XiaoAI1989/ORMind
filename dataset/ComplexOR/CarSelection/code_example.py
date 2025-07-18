from pulp import *
import numpy as np

def solve(data):
    ParticipantNum = data["ParticipantNum"]
    CarNum = data["CarNum"]
    InterestMatrix = np.array(data["InterestMatrix"])

    prob = LpProblem("Car Selection Problem", LpMaximize)
    Assignment = LpVariable.dicts("Assignment",
                                  ((p, c) for p in range(ParticipantNum) for c in range(CarNum)),
                                  cat='Binary')

  ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables
        optimized_vars = {
            "assignment": {(p, c): Assignment[(p, c)].varValue
                           for p in range(ParticipantNum)
                           for c in range(CarNum)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}
