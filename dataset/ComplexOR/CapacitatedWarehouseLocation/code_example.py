from pulp import *
import numpy as np

def solve(data):
    NumberOfLocations = data["NumberOfLocations"]
    NumberOfCustomers = data["NumberOfCustomers"]
    CustomerDemand = np.array(data["CustomerDemand"])
    ServiceAllocationCost = np.array(data["ServiceAllocationCost"])
    WarehouseCapacity = np.array(data["WarehouseCapacity"])
    MinimumDemandFromWarehouse = np.array(data["MinimumDemandFromWarehouse"])
    MinimumOpenWarehouses = data["MinimumOpenWarehouses"]
    MaximumOpenWarehouses = data["MaximumOpenWarehouses"]
    WarehouseFixedCost = np.array(data["WarehouseFixedCost"])

    prob = LpProblem("Capacitated_Warehouse_Location", LpMinimize)

    warehouse_open = LpVariable.dicts("warehouse_open", range(NumberOfLocations), 0, 1, LpBinary)
    service_allocation = LpVariable.dicts("service_allocation",
                                         ((i, j) for i in range(NumberOfLocations) for j in range(NumberOfCustomers)),
                                         0, None, LpContinuous)


  ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables
        optimized_vars = {
            "open_warehouse": {i: warehouse_open[i].varValue for i in range(NumberOfLocations)},
            "allocate_service": {(i, j): service_allocation[(i, j)].varValue
                                 for i in range(NumberOfLocations)
                                 for j in range(NumberOfCustomers)}}
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}
