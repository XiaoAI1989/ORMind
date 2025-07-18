from pulp import *
import numpy as np

def solve(data):
    Locations = data["Locations"]
    Commodities = data["Commodities"]
    ProductPlants = data["ProductPlants"]
    DistributionCenters = data["DistributionCenters"]
    CustomerZones = data["CustomerZones"]
    Supply = np.array(data["Supply"])
    Demand = np.array(data["Demand"])
    MaxThroughput = np.array(data["MaxThroughput"])
    MinThroughput = np.array(data["MinThroughput"])
    UnitThroughputCost = np.array(data["UnitThroughputCost"])
    FixedThroughputCost = np.array(data["FixedThroughputCost"])
    VariableCost = np.array(data["VariableCost"])

    prob = LpProblem("Main_Facility_Location", LpMinimize)
    shipment = LpVariable.dicts("shipment", (range(Commodities), range(ProductPlants), range(DistributionCenters), range(CustomerZones)), lowBound=0)
    open_distribution_center = LpVariable.dicts("open_distribution_center", (range(DistributionCenters)), cat='Binary')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "shipment": {(c, p, d, z): shipment[c][p][d][z].varValue
                         for c in range(Commodities)
                         for p in range(ProductPlants)
                         for d in range(DistributionCenters)
                         for z in range(CustomerZones)},
            "open_distribution_center": {d: open_distribution_center[d].varValue
                                         for d in range(DistributionCenters)}
        }

        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}