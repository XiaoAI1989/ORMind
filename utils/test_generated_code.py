"""Execution and grading utilities.

The two roles in this module are intentionally separated:

* ``run_generated_code`` executes the generated program on raw problem
  inputs only. It never sees reference outputs, so it is safe to call
  from inside the solving pipeline (Algorithm 1, line 6 "Run the code").

* ``test_generated_code`` compares program outputs against the reference
  optimum from ``data.json``. It must only be called once, after the
  pipeline has finished, by the experiment runner. Calling it inside the
  pipeline would leak ground-truth labels into the repair loop.
"""

import json
import math
import os
import types
from typing import Any, Iterable, List, Optional

from utils.result import Result

REL_TOL = 1e-3
ABS_TOL = 2e-1

GENERATED_CODE_PATH = os.path.join("temp", "generated_code.py")
EVAL_CODE_PATH = os.path.join("temp", "eval_code.py")


class NullWriter:
    def write(self, text: str) -> None:
        _ = text


def _load_module_from_file(module_name: str, file_path: str):
    """Execute a generated source file into a fresh module object.

    This bypasses the import system on purpose: importlib caches modules
    by mtime+size, which can silently serve stale code when a regenerated
    file happens to have the same length within one timestamp tick.
    """
    with open(file_path, "r", encoding="utf8") as handle:
        source = handle.read()
    module = types.ModuleType(module_name)
    module.__file__ = file_path
    code_object = compile(source, file_path, "exec")
    exec(code_object, module.__dict__)
    return module


def _resolve_solver_function(problem_name: str):
    generated_code = _load_module_from_file("ormind_generated_code", GENERATED_CODE_PATH)
    function_name = problem_name if problem_name.startswith("prob_") else "solve"
    return getattr(generated_code, function_name)


def _call_solver(problem_name: str, func, problem_input: dict) -> Any:
    if problem_name.startswith("prob_"):
        return func(**problem_input)
    return func(problem_input)


def write_generated_code(code: str) -> None:
    os.makedirs("temp", exist_ok=True)
    with open(os.path.join("temp", "generated_code.py"), "w", encoding="utf8") as handle:
        handle.write(code)


def run_generated_code(problem_name: str, problem_inputs: List[dict]):
    """Execute the generated program on problem inputs (labels are never passed in).

    Returns the output of the last input on success, or an error string on
    compile/runtime failure.
    """
    try:
        func = _resolve_solver_function(problem_name)
    except BaseException as exc:
        return f"The previous code has compile error: {exc}, you need to fix it."

    last_output = None
    for problem_input in problem_inputs:
        try:
            last_output = _call_solver(problem_name, func, problem_input)
        except BaseException as exc:
            return f"The previous code has running-time error: {exc}, you need to fix it."
    return last_output


def _classify_solution(problem_name: str, output: Any):
    """Return (comparable_value, model_failed).

    ``model_failed`` is True when the program ran but the formulated model
    produced no valid optimum (non-Optimal solver status or missing
    objective), which maps to the paper's MFFR metric.
    """
    if output is None:
        return None, True
    if problem_name.startswith("prob_"):
        comparable = output[0] if isinstance(output, tuple) else output
        return comparable, comparable is None
    if isinstance(output, dict):
        if output.get("status") != "Optimal":
            return output.get("status"), True
        objective = output.get("objective_value")
        return objective, objective is None
    return output, False


def test_generated_code(
    problem_name: str,
    samples: Iterable[dict],
    log_file: Optional[NullWriter] = None,
    *,
    rel_tol: float = REL_TOL,
    abs_tol: float = ABS_TOL,
    accept_infeasible: bool = False,
) -> Result:
    """Grade the final program against reference outputs.

    Post-hoc grading only. This is the single place where ground-truth
    outputs are read; the solving pipeline never imports this function.

    The defaults reproduce the published protocol exactly:

    * ``rel_tol`` / ``abs_tol``: numeric tolerance on the objective value.
    * ``accept_infeasible=False``: a program whose solver reports a
      non-Optimal status is graded MODEL_FAILURE even when the reference
      output is that same status string. 11 of the 37 ComplexOR problems
      ship ``"Infeasible"`` as their reference output, so under the
      published protocol the maximum reachable SR on ComplexOR is 26/37.
      Setting ``accept_infeasible=True`` grades a status string that
      exactly matches the reference as ACCEPT instead. Numbers produced
      with this flag are not comparable to the paper's tables.
    """
    log_file = log_file or NullWriter()

    try:
        func = _resolve_solver_function(problem_name)
    except BaseException as exc:
        log_file.write("There is grammar error in generated code or the solver entry point is missing.\n")
        log_file.write(str(exc) + "\n")
        log_file.write(f"Final Result: {Result.COMPILE_ERROR.name}\n")
        return Result.COMPILE_ERROR

    total_num = len(samples)
    passed_num = 0
    has_runtime_error = False
    has_model_failure = False

    for index, sample in enumerate(samples):
        log_file.write("=" * 15 + f"test sample {index}" + "=" * 15 + "\n")
        try:
            output = _call_solver(problem_name, func, sample["input"])
        except BaseException as exc:
            has_runtime_error = True
            log_file.write("Runtime Error\n")
            log_file.write(str(exc) + "\n\n")
            continue

        comparable_output, model_failed = _classify_solution(problem_name, output)
        ground_truth = sample["output"][0] if len(sample["output"]) == 1 else tuple(sample["output"])

        if model_failed:
            if accept_infeasible and isinstance(ground_truth, str) and comparable_output == ground_truth:
                passed_num += 1
                log_file.write(f"Solver status {comparable_output!r} matches the reference status.\n")
                log_file.write("Is passed: True (accept_infeasible)\n\n")
                continue
            has_model_failure = True
            log_file.write("Model Formulation Failure\n")
            log_file.write(f"The program ran but produced no valid optimum: {comparable_output!r}\n\n")
            continue

        log_file.write("Program Output:\n")
        log_file.write(str(output) + "\n\n")
        log_file.write("Ground Truth:\n")
        log_file.write(str(ground_truth) + "\n")

        try:
            if isinstance(comparable_output, (int, float, complex)):
                is_passed = math.isclose(comparable_output, ground_truth, rel_tol=rel_tol, abs_tol=abs_tol)
            else:
                is_passed = comparable_output == ground_truth
        except BaseException:
            is_passed = False

        if is_passed:
            passed_num += 1
        log_file.write(f"Is passed: {is_passed}\n\n")

    log_file.write("\n\n")
    log_file.write(f"{passed_num}/{total_num} passed\n")
    is_correct = total_num > 0 and passed_num == total_num
    log_file.write(f"is correct: {is_correct}\n")

    if has_runtime_error:
        result = Result.RUNTIME_ERROR
    elif has_model_failure:
        result = Result.MODEL_FAILURE
    elif is_correct:
        result = Result.ACCEPT
    else:
        result = Result.WRONG_ANSWER
    log_file.write(f"Final Result: {result.name}\n")
    return result


def run_eval_code(samples: Iterable[dict], code_path: str = EVAL_CODE_PATH):
    """Run a generated counterfactual checker on the candidate solution."""
    eval_code = _load_module_from_file("ormind_eval_code", code_path)
    func = getattr(eval_code, "counterfactual_solution_analysis")
    for sample in samples:
        return func(**sample)
    return None


def read_test_samples(dataset: str, problem_name: str):
    with open(os.path.join("dataset", dataset, problem_name, "data.json"), "r", encoding="utf8") as handle:
        return json.load(handle)
