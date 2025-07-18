from pulp import *
import numpy as np

def solve(data):
    people = data["People"]
    projects = data["Projects"]
    skills = data["Skills"]
    required_skill = np.array(data["RequiredSkill"])
    individual_skill = np.array(data["IndividualSkill"])

    prob = LpProblem("Team_Problem", LpMinimize)
    assign = LpVariable.dicts("Assign", ((p, c) for p in range(people) for c in range(projects)), cat='Binary')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "assign": {(p, c): assign[p, c].varValue
                       for p in range(people)
                       for c in range(projects)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}