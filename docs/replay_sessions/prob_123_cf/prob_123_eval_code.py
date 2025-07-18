import math

def counterfactual_solution_analysis(obj, var1, var2):
    epsilon = 1e-2
    modifications = {
        "Modification1": {
            "check": lambda: var1 >= 0 - epsilon,
            "message": "Adjust constraint to allow var1 (painkiller pills) to be {:.2f}".format(var1)
        },
        "Modification2": {
            "check": lambda: var2 >= 0 - epsilon,
            "message": "Adjust constraint to allow var2 (sleeping pills) to be {:.2f}".format(var2)
        },
        "Modification3": {
            "check": lambda: 10 * var1 + 6 * var2 <= 3000 + epsilon,
            "message": "Modify morphine constraint to allow 10*var1 + 6*var2 to be {:.2f}".format(10 * var1 + 6 * var2)
        },
        "Modification4": {
            "check": lambda: var1 >= 50 - epsilon,
            "message": "Adjust minimum painkiller requirement to allow var1 to be {:.2f}".format(var1)
        },
        "Modification5": {
            "check": lambda: var2 >= 0.7 * (var1 + var2) - epsilon,
            "message": "Modify sleeping pill percentage constraint to allow var2/(var1+var2) to be {:.2f}".format(var2 / (var1 + var2) if (var1 + var2) > 0 else 0)
        },
        "Modification6": {
            "check": lambda: math.isclose(var1, round(var1)) and math.isclose(var2, round(var2)),
            "message": "Remove integer constraint on variables"
        },
        "Modification7": {
            "check": lambda: math.isclose(obj, round(obj)),
            "message": "Remove integer constraint on objective value"
        }
    }

    results = {}
    all_valid = True

    for name, modification in modifications.items():
        needed = not modification["check"]()
        results[name] = {
            "modification_needed": needed,
            "suggestion": modification["message"] if needed else None
        }
        if needed:
            all_valid = False

    results["solution_valid_without_changes"] = all_valid

    return results
