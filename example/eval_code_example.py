import math

def counterfactual_solution_analysis(obj, var1, var2):
    """
    Analyze what changes would be necessary for the given solution to be valid and optimal.
    The function variable names must remain obj, var1 and var2. Do not alter these names.
    Args:
        obj: The objective value
        var1: Value of variable 1
        var2: Value of variable 2

    Returns:
        dict: Contains suggested modifications for each constraint and overall assessment
    """
    epsilon = 1e-2
    modifications = {
        "Modification1": {
            "check": lambda: var1 >= 0-epsilon,
            "message": "Adjust constraint to allow var1 to be {:.2f}".format(var1)
        },
        "Modification2": {
            "check": lambda: var2 >= 0-epsilon,
            "message": "Adjust constraint to allow var2 to be {:.2f}".format(var2)
        },
        "Modification3": {
            "check": lambda: 2 * var1 + 3 * var2 <= 100+epsilon,
            "message": "Modify resource constraint to allow 2*var1 + 3*var2 to be {:.2f}".format(2*var1 + 3*var2)
        },
        "Modification4": {
            "check": lambda: var1 + var2 <= 35+epsilon,
            "message": "Adjust daily production limit to allow var1 + var2 to be {:.2f}".format(var1 + var2)
        },
        "Modification5": {
            "check": lambda: math.isclose(var1, round(var1)) and math.isclose(var2, round(var2)),
            "message": "Remove integer constraint on variables"
        },
        "Modification6": {
            "check": lambda: math.isclose(obj, round(obj)),
            "message": "Remove integer constraint on objective"
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