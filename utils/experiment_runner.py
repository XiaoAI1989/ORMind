"""Experiment harness.

Protocol (kept deliberately strict so results are auditable):

  1. The pipeline solves each problem given the problem text, the
     interface code example, and raw test inputs. It never receives
     reference outputs.
  2. After the pipeline finishes, the final program is graded exactly
     once against the reference outputs (utils.test_generated_code).
  3. Results are reported with the paper's metrics:
       SR    = ACCEPT rate
       MFFR  = MODEL_FAILURE rate (invalid formulated model)
       IEFR  = COMPILE_ERROR + RUNTIME_ERROR rate
       WA    = residual wrong-answer rate
  4. Per-problem token usage is appended to the test log as
     "Prompt Tokens: N" so data_process/count_token.py reproduces the
     prompt-length statistics (Table 4).
"""

import argparse
import os
import re
import time
import traceback
from pathlib import Path
from typing import Callable

from agent_team.ormind_pipeline import PipelineConfig
from main import solve_problem
from utils.result import Result
from utils.test_generated_code import ABS_TOL, REL_TOL, read_test_samples, test_generated_code, write_generated_code
from utils.utils import extract_number


def build_parser(default_dataset: str, default_problem: str, default_attention: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and test ORMind solutions.")
    parser.add_argument("--dataset", type=str, default=default_dataset, help='Dataset name, "LPWP" or "ComplexOR"')
    parser.add_argument("--problem", type=str, default=default_problem, help="Problem name or regex")
    parser.add_argument("--log_dir", type=str, default="log", help="Directory for logs (default: ./log, gitignored)")
    parser.add_argument("--model", type=str, default="", help="Base large language model")
    parser.add_argument("--temperature", type=float, default=0, help="Temperature for the LLM")
    parser.add_argument("--attention", type=str, default=default_attention, help="Task-specific interface attention")
    parser.add_argument("--base_url", type=str, default="", help="OpenAI-compatible base URL")
    parser.add_argument("--api_key", type=str, default="", help="OpenAI-compatible API key")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["paper", "standard", "extended"],
        default="paper",
        help='"paper" = Algorithm 1 as published (default); "standard" = single-prompt baseline '
        '("w/o All modules"); "extended" = post-publication extensions.',
    )
    parser.add_argument(
        "--max_repair_rounds",
        type=int,
        default=1,
        help="Error-triggered revision rounds. Algorithm 1 uses a single revision (default 1).",
    )
    # Table 2 ablations (paper mode only).
    parser.add_argument("--with_conductor", action="store_true", help='Ablation "w/ Conductor"')
    parser.add_argument("--with_terminology_interpreter", action="store_true", help='Ablation "w/ Terminology Interpreter"')
    parser.add_argument("--with_code_reviewer", action="store_true", help='Ablation "w/ Code Reviewer"')
    parser.add_argument("--without_semantic_encoder", action="store_true", help='Ablation "w/o Semantic Encoder"')
    parser.add_argument("--without_formalization", action="store_true", help='Ablation "w/o Formalization Thinking"')
    parser.add_argument("--without_counterfactual", action="store_true", help='Ablation "w/o Counterfactual Analysis"')
    parser.add_argument("--without_syntax_analysis", action="store_true", help='Ablation "w/o Syntax Error Analysis"')
    # Grading options. The defaults are the published protocol; changing any
    # of them produces numbers that are NOT comparable to the paper's tables.
    parser.add_argument(
        "--accept_infeasible",
        action="store_true",
        help="Grade a solver status that exactly matches a string reference output "
        '(e.g. "Infeasible") as ACCEPT. Off by default: the published protocol '
        "grades these as MODEL_FAILURE, which caps SR at 26/37 on ComplexOR.",
    )
    parser.add_argument("--rel_tol", type=float, default=REL_TOL, help=f"Relative tolerance on the objective (published: {REL_TOL})")
    parser.add_argument("--abs_tol", type=float, default=ABS_TOL, help=f"Absolute tolerance on the objective (published: {ABS_TOL})")
    # Extended-mode options.
    parser.add_argument("--num_candidates", type=int, default=2, help="Candidate programs (extended mode only)")
    parser.add_argument("--memory_file", type=str, default="", help="Experience memory file (extended mode only)")
    parser.add_argument("--sleep", type=float, default=1.0, help="Pause between problems in seconds")
    return parser


def _pipeline_config(args) -> PipelineConfig:
    return PipelineConfig(
        use_semantic_encoder=not args.without_semantic_encoder,
        use_formalization_thinking=not args.without_formalization,
        use_counterfactual_analysis=not args.without_counterfactual,
        use_syntax_error_analysis=not args.without_syntax_analysis,
        with_conductor=args.with_conductor,
        with_terminology_interpreter=args.with_terminology_interpreter,
        with_code_reviewer=args.with_code_reviewer,
        max_repair_rounds=args.max_repair_rounds,
    )


def run_experiment(args, problem_reader: Callable[[str, str], dict]):
    config = _pipeline_config(args)

    matched_problems = [
        name
        for name in os.listdir(os.path.join("dataset", args.dataset))
        if re.match(args.problem, name)
    ]
    matched_problems.sort(key=extract_number)
    if not matched_problems:
        print("No problem matched! Please check arguments.")
        return

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    run_dir = os.path.join(args.log_dir, f"run_{args.dataset}_{round(time.time())}")
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    print(f"Save log to {run_dir}")

    counts = {result: 0 for result in Result}
    counterfactual_statuses: dict = {}
    accepted_without_solver = []
    models_used: dict = {}

    for index, problem_name in enumerate(matched_problems, start=1):
        problem_data = problem_reader(args.dataset, problem_name)
        test_samples = read_test_samples(args.dataset, problem_name)
        # The pipeline only ever receives the inputs; reference outputs
        # stay inside this runner for the final grading step.
        test_inputs = [sample["input"] for sample in test_samples]

        stats = {"usage": {"llm_calls": 0, "prompt_tokens": 0, "completion_tokens": 0}}
        try:
            code, _, stats = solve_problem(
                problem_name=problem_name,
                problem=problem_data,
                attention=args.attention,
                test_inputs=test_inputs,
                path=run_dir,
                mode=args.mode,
                model=args.model or None,
                base_url=args.base_url or None,
                api_key=args.api_key or None,
                temperature=args.temperature,
                config=config,
                num_candidates=args.num_candidates,
                memory_file=args.memory_file or None,
            )
        except Exception:
            code = ""
            with open(os.path.join(run_dir, f"{problem_name}_pipeline_error.txt"), "w", encoding="utf8") as handle:
                handle.write(traceback.format_exc())

        with open(os.path.join(run_dir, f"{problem_name}_generated_code.py"), "w", encoding="utf8") as handle:
            handle.write(code)
        write_generated_code(code)

        # Echo-args guard: on LPWP, data.json inputs encode the
        # reference optimum for many problems, so a program that computes its
        # answer from the call arguments instead of solving would be graded
        # correct. Flag any final program that never references the solver.
        solver_used = bool(re.search(r"\bpulp\b", code, re.IGNORECASE))

        with open(os.path.join(run_dir, f"{problem_name}_test_log.txt"), "w", encoding="utf8") as handle:
            result = test_generated_code(
                problem_name,
                test_samples,
                handle,
                rel_tol=args.rel_tol,
                abs_tol=args.abs_tol,
                accept_infeasible=args.accept_infeasible,
            )
            usage = stats.get("usage", {})
            handle.write(f"Prompt Tokens: {usage.get('prompt_tokens', 0)}\n")
            handle.write(f"Completion Tokens: {usage.get('completion_tokens', 0)}\n")
            handle.write(f"LLM Calls: {usage.get('llm_calls', 0)}\n")
            handle.write(f"Models Used: {usage.get('calls_by_model', {})}\n")
            handle.write(f"Solver Used: {solver_used}\n")
            handle.write(f"Counterfactual Status: {stats.get('counterfactual_status', 'unknown')}\n")

        counts[result] += 1
        cf_status = stats.get("counterfactual_status", "unknown")
        counterfactual_statuses[cf_status] = counterfactual_statuses.get(cf_status, 0) + 1
        for model_name, model_calls in stats.get("usage", {}).get("calls_by_model", {}).items():
            models_used[model_name] = models_used.get(model_name, 0) + model_calls
        if result == Result.ACCEPT and not solver_used:
            accepted_without_solver.append(problem_name)
            print(f"  WARNING: {problem_name} was ACCEPTed but the final program never references the solver.")

        success_rate = counts[Result.ACCEPT] / index * 100
        mffr = counts[Result.MODEL_FAILURE] / index * 100
        iefr = (counts[Result.COMPILE_ERROR] + counts[Result.RUNTIME_ERROR]) / index * 100
        wrong_rate = counts[Result.WRONG_ANSWER] / index * 100
        print(
            f"[{index}/{len(matched_problems)}] {problem_name} -> {result.name} | "
            f"SR: {success_rate:.2f}% | MFFR: {mffr:.2f}% | IEFR: {iefr:.2f}% | WA: {wrong_rate:.2f}%"
        )
        if args.sleep > 0:
            time.sleep(args.sleep)

    total_num = len(matched_problems)
    print(f"Passed: {counts[Result.ACCEPT]}/{total_num}")
    print(f"SR   (Success Rate):                      {counts[Result.ACCEPT] / total_num * 100:.2f}%")
    print(f"MFFR (Model Formulation Failure Rate):    {counts[Result.MODEL_FAILURE] / total_num * 100:.2f}%")
    print(
        "IEFR (Implementation Execution Failure):  "
        f"{(counts[Result.COMPILE_ERROR] + counts[Result.RUNTIME_ERROR]) / total_num * 100:.2f}%"
    )
    print(f"WA   (Wrong Answer):                      {counts[Result.WRONG_ANSWER] / total_num * 100:.2f}%")
    if args.accept_infeasible or args.rel_tol != REL_TOL or args.abs_tol != ABS_TOL:
        print("NOTE: non-default grading options were used; these numbers are not comparable to the paper's tables.")
    print(f"Counterfactual checker statuses: {counterfactual_statuses}")
    if models_used:
        print(f"LLM completions by model: {models_used}")
        if len(models_used) > 1:
            print("WARNING: more than one model served this run (fallback fired); attribute the numbers accordingly.")
    if accepted_without_solver:
        print(
            f"WARNING: {len(accepted_without_solver)} ACCEPTed program(s) never reference the solver "
            f"(possible echo-args shortcut, see README 'Known protocol caveats'): {accepted_without_solver}"
        )
