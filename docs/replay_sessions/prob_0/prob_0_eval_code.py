def counterfactual_solution_analysis(obj, var1, var2):
    DOG_CAPACITY = 100
    TRUCK_CAPACITY = 300
    DOG_COST = 50
    TRUCK_COST = 100
    MAX_BUDGET = 1000

    checks = {
        "non_negativity_var1": {
            "check": lambda v1, v2: v1 >= 0,
            "message": "Sled dog trips must be non-negative"
        },
        "non_negativity_var2": {
            "check": lambda v1, v2: v2 >= 0,
            "message": "Truck trips must be non-negative"
        },
        "budget_constraint": {
            "check": lambda v1, v2: DOG_COST * v1 + TRUCK_COST * v2 <= MAX_BUDGET,
            "message": "Budget constraint: 50*var1 + 100*var2 <= 1000"
        },
        "trip_requirement": {
            "check": lambda v1, v2: v1 < v2,
            "message": "Sled dog trips must be strictly less than truck trips (var1 < var2)"
        },
        "integrality_var1": {
            "check": lambda v1, v2: v1 == int(v1),
            "message": "Sled dog trips must be an integer"
        },
        "integrality_var2": {
            "check": lambda v1, v2: v2 == int(v2),
            "message": "Truck trips must be an integer"
        }
    }

    results = {}
    all_valid = True
    for name, spec in checks.items():
        satisfied = spec["check"](var1, var2)
        results[name] = {
            "modification_needed": not satisfied,
            "suggestion": spec["message"] if not satisfied else None
        }
        if not satisfied:
            all_valid = False

    results["solution_valid_without_changes"] = all_valid
    return results
