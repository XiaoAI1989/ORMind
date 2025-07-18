from pulp import *
import numpy as np

def solve(data):
    JobCount = data["JobCount"]
    MachineCount = data["MachineCount"]
    ProcessingTime = np.array(data["ProcessingTime"])

    # Create the model
    prob = LpProblem("Aircraft_Assignment_Problem", LpMinimize)
    JobMachine = LpVariable.dicts("JobMachine", ((i, j) for i in range(JobCount) for j in range(MachineCount)), cat='Binary')
    completion_time = LpVariable("CompletionTime", lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "JobMachine": {(i, j): JobMachine[i, j].varValue
                           for i in range(JobCount)
                           for j in range(MachineCount)},
            "completion_time": completion_time.varValue
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}