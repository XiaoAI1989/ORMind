from pulp import *
import numpy as np

def solve(data):
    Crops = data['Crops']
    Months = data['Months']
    ConsumptionBundles = data['ConsumptionBundles']
    Yield = np.array(data['Yield'])
    Price = np.array(data['Price'])
    AmountInBundle = np.array(data['AmountInBundle'])
    LandAvailable = data['LandAvailable']
    LaborRequired = np.array(data['LaborRequired'])
    AnnualWageRateFamilyLabor = data['AnnualWageRateFamilyLabor']
    AnnualWageRatePermanentLabor = data['AnnualWageRatePermanentLabor']
    HourlyWageRateTemporaryLabor = data['HourlyWageRateTemporaryLabor']
    WorkingHours = np.array(data['WorkingHours'])
    FamilyLaborAvailable = data['FamilyLaborAvailable']
    AnnualAmountOfWaterAvailable = data['AnnualAmountOfWaterAvailable']
    WaterLimit = np.array(data['WaterLimit'])
    WaterRequirement = np.array(data['WaterRequirement'])
    PriceOfWater = data['PriceOfWater']

    prob = LpProblem("Farm Planning Optimization", LpMaximize)
    Land_planted = LpVariable.dicts("Land_planted", ((c, t) for c in range(Crops) for t in range(Months)), lowBound=0)
    Harvest = LpVariable.dicts("Harvest", (c for c in range(Crops)), lowBound=0)
    BP_land = LpVariable.dicts("BP_land", (c for c in range(Crops)), cat='Binary')

    ###########TODO##########

    prob.solve()

    if prob.status == LpStatusOptimal:
        # Extract the optimized variables as values
        optimized_vars = {
            "Land_planted": {(c, t): Land_planted[c, t].varValue for c in range(Crops) for t in range(Months)},
            "Harvest": {c: Harvest[c].varValue for c in range(Crops)},
            "BP_land": {c: BP_land[c].varValue for c in range(Crops)}
        }
        return {
            "status": "Optimal",
            "objective_value": value(prob.objective),
            "optimized_vars": optimized_vars
        }
    else:
        return {"status": LpStatus[prob.status]}