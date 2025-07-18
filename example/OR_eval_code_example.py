import numpy as np

def counterfactual_solution_analysis(alloys_used, data):
    """
    Analyze what changes would be necessary for the given solution to be valid and optimal.

    Returns:
        dict: Contains suggested modifications for each constraint and overall assessment
    """
    AlloysOnMarket = data["AlloysOnMarket"]
    RequiredElements = data["RequiredElements"]
    CompositionDataPercentage = np.array(data["CompositionDataPercentage"])
    DesiredBlendPercentage = np.array(data["DesiredBlendPercentage"])
    AlloyPrice = np.array(data["AlloyPrice"])

    alloys_used_array = np.array([alloys_used[a] for a in range(AlloysOnMarket)])

    modifications = {
        "Modification1": {
            "check": lambda: all(alloys_used_array >= 0),
            "message": "Adjust non-negativity constraint to allow negative quantities: {}".format(alloys_used_array)
        },
        "Modification2": {
            "check": lambda: all(np.dot(CompositionDataPercentage, alloys_used_array) >= DesiredBlendPercentage * np.sum(alloys_used_array)),
            "message": "Modify desired blend percentages to: {}".format(np.dot(CompositionDataPercentage, alloys_used_array) / np.sum(alloys_used_array))
        },
        "Modification3": {
            "check": lambda: all(alloys_used_array <= 1),
            "message": "Increase market availability to allow quantities: {}".format(alloys_used_array)
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