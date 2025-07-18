from pulp import *
import numpy as np

def solve(data):
    CustomerCount = data["CustomerCount"]
    VehicleCount = data["VehicleCount"]
    CustomerDemand = np.array(data["CustomerDemand"])
    CustomerLBTW = np.array(data["CustomerLBTW"])
    CustomerUBTW = np.array(data["CustomerUBTW"])
    CustomerDistance = np.array(data["CustomerDistance"])
    CustomerServiceTime = np.array(data["CustomerServiceTime"])
    VehicleCapacity = np.array(data["VehicleCapacity"])

    prob = LpProblem("VRPTW", LpMinimize)
    x = LpVariable.dicts("x", (range(CustomerCount+1), range(CustomerCount+1), range(VehicleCount)), 0, 1, LpBinary)
    ArrivalTime = LpVariable.dicts("ArrivalTime", (range(CustomerCount), range(VehicleCount)), lowBound=0)
    u = LpVariable.dicts("u", range(1, CustomerCount), lowBound=0, upBound=CustomerCount-1, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "x": {(i, j, k): x[i][j][k].varValue
                  for i in range(CustomerCount+1)
                  for j in range(CustomerCount+1)
                  for k in range(VehicleCount)},
            "ArrivalTime": {(i, k): ArrivalTime[i][k].varValue
                            for i in range(CustomerCount)
                            for k in range(VehicleCount)},
            "u": {i: u[i].varValue for i in range(1, CustomerCount)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}