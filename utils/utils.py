import json
import os
import re

import numpy as np


def extract_code_from_string(input_string):
    # Match code within ```python ... ``` or ``` ... ``` blocks
    pattern = r'```(?:python)?\s*(.*?)(?:```|\Z)'
    # Find all matches in the input string
    code_blocks = re.findall(pattern, input_string, re.DOTALL)

    if len(code_blocks) == 0:
        return input_string
    elif len(code_blocks) == 1:
        return code_blocks[0]

    code_blocks = [code for code in code_blocks if 'pip' not in code]
    return '\n'.join(code_blocks)


def clean_markdown_block(text):
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json|python)?", "", stripped).strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    return stripped


def flatten_problem_description(description):
    if isinstance(description, dict):
        return "\n".join(f"{key}: {value}" for key, value in description.items())
    return str(description)


def read_problem(dataset, problem_name):
    base_dir = 'dataset'
    with open(os.path.join(base_dir, dataset, problem_name, 'description.txt'), 'r', encoding='utf8') as f:
        description = f.read()

    with open(os.path.join(base_dir, dataset, problem_name, 'code_example.py'), 'r', encoding='utf8') as f:
        code_example = f.read()

    return {
        'description': description,
        'code_example': code_example
    }


def read_OR_problem(dataset, problem_name):
    base_dir = 'dataset'
    with open(os.path.join(base_dir, dataset, problem_name, 'input_targets.json'), 'r', encoding='utf8') as f:
        data = json.load(f)

    parameters_str = "Parameters:\n"
    for param in data['parameters']:
        parameters_str += f"- {param['symbol']}: {param['definition']}\n"
        if param['shape']:
            parameters_str += f"  Shape: {' x '.join(map(str, param['shape']))}\n"

    description = {
        'background': data['background'],
        'objective': data['objective'],
        'constraints': '\n'.join(f"{i + 1}. {constraint}" for i, constraint in enumerate(data['constraints'])),
        'problem_description': data['description'],
        'parameters': parameters_str.strip()
    }

    with open(os.path.join(base_dir, dataset, problem_name, 'code_example.py'), 'r', encoding='utf8') as f:
        code_example = f.read()

    return {
        'description': description,
        'code_example': code_example
    }


def format_constraint_results(results):
    if results["solution_valid_without_changes"]:
        return "Don't need to modify any constraints!"

    output = []
    for name, result in results.items():
        if name != "solution_valid_without_changes":
            if result["modification_needed"]:
                output.append(f"{result['suggestion']}")

    return "\n".join(output)


def extract_number(filename):
    match = re.search(r'\d+', filename)
    if match:
        return int(match.group())
    return 0


def get_dict_values_as_string(input_dict):
    if not isinstance(input_dict, dict):
        return f"Error: Input is not a dictionary, it's a {type(input_dict).__name__}"

    def get_value_repr(value):
        if isinstance(value, np.ndarray):
            return f"numpy.ndarray(shape={value.shape}, dtype={value.dtype})"
        elif np.isscalar(value):
            return str(value)
        else:
            return str(type(value).__name__)

    key_value_pairs = [f"{key}: {get_value_repr(value)}" for key, value in input_dict.items()]
    return ', '.join(key_value_pairs)
