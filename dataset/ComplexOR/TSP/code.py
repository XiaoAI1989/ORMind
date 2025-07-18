
import json
import numpy as np
import math

import gurobipy as gp

 # Define model
model = gp.Model('model')

with open("data/complexor/TSP/data.json", "r") as f:
    data = json.load(f)


OriginNum = data["OriginNum"] # scalar parameter
DestinationNum = data["DestinationNum"] # scalar parameter
Supply = np.array(data["Supply"]) # ['OriginNum']
Demand = np.array(data["Demand"]) # ['DestinationNum']
Cost = np.array(data["Cost"]) # ['OriginNum', 'DestinationNum']
QuantityShipped = model.addVars(OriginNum, DestinationNum, vtype=gp.GRB.CONTINUOUS, name="QuantityShipped")

# Add supply limit constraints for each origin
for i in range(OriginNum):
    model.addConstr(gp.quicksum(QuantityShipped[i, j] for j in range(DestinationNum)) <= Supply[i], name=f"supply_limit_{i}")

# Add demand satisfaction constraints
for j in range(DestinationNum):
    model.addConstr(gp.quicksum(QuantityShipped[i, j] for i in range(OriginNum)) >= Demand[j], name=f"demand_satisfaction_{j}")

# The non-negativity constraint for QuantityShipped is already enforced by default in Gurobi
# when the variable is created with vtype=gp.GRB.CONTINUOUS. No additional code is needed.

# Add constraints: total quantity shipped from each origin must not exceed its supply
for i in range(OriginNum):
    model.addConstr(gp.quicksum(QuantityShipped[i, j] for j in range(DestinationNum)) <= Supply[i], name=f"supply_constraint_{i}")

# Add constraints for meeting demand at each destination
for j in range(DestinationNum):
    model.addConstr(
        gp.quicksum(QuantityShipped[i, j] for i in range(OriginNum)) >= Demand[j],
        name=f"meet_demand_{j}"
    )

# The non-negativity constraint is already enforced by default when creating the variables
# QuantityShipped = model.addVars(OriginNum, DestinationNum, vtype=gp.GRB.CONTINUOUS, name="QuantityShipped")
# Gurobi automatically sets lower bounds of continuous variables to 0 unless specified otherwise

# Set objective
model.setObjective(gp.quicksum(Cost[i,j] * QuantityShipped[i,j] for i in range(OriginNum) for j in range(DestinationNum)), gp.GRB.MINIMIZE)

# Optimize model
model.optimize()


# Get model status
status = model.status

obj_val = None
# check whether the model is infeasible, has infinite solutions, or has an optimal solution
if status == gp.GRB.INFEASIBLE:
    obj_val = "infeasible"
elif status == gp.GRB.INF_OR_UNBD:
    obj_val = "infeasible or unbounded"
elif status == gp.GRB.UNBOUNDED:
    obj_val = "unbounded"
elif status == gp.GRB.OPTIMAL:
    obj_val = model.objVal

