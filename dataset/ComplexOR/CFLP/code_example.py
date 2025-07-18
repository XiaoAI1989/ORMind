from pulp import *
import numpy as np

def solve(data):
    NumberOfFacilities = data["NumberOfFacilities"]
    NumberOfCustomers = data["NumberOfCustomers"]
    FacilityFixedCost = np.array(data["FacilityFixedCost"])
    FacilityCapacity = np.array(data["FacilityCapacity"])
    CustomerDemand = np.array(data["CustomerDemand"])
    FacilityToCustomerTransportCost = np.array(data["FacilityToCustomerTransportCost"])

    prob = LpProblem("Capacitated_Facility_Location_Problem", LpMinimize)
    facility_vars = LpVariable.dicts("Facility", range(NumberOfFacilities), lowBound=0, upBound=1, cat='Integer')
    transport_vars = LpVariable.dicts("Transport", ((i, j) for i in range(NumberOfFacilities) for j in range(NumberOfCustomers)), lowBound=0, cat='Continuous')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "facility_vars": {i: facility_vars[i].varValue for i in range(NumberOfFacilities)},
            "transport_vars": {(i, j): transport_vars[(i, j)].varValue
                               for i in range(NumberOfFacilities)
                               for j in range(NumberOfCustomers)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}