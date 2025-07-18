"""Record/replay driver: run the ORMind pipeline without an API key.

Every LLM call the pipeline makes is written to
``<session>/call_NNN_prompt.txt``. If ``<session>/call_NNN_response.txt``
exists, it is used as the completion and the run continues; otherwise the
driver stops with exit code 3 and reports which call is pending. Produce
the response with any completion source (another model, a chat UI, a
human) and rerun: completed calls replay deterministically from disk, so
the run resumes exactly where it stopped.

This makes a full pipeline run auditable end to end: the session folder
contains every prompt, every response, all generated artifacts, and the
final grading log.

Usage:
    python tools/replay_driver.py --dataset LPWP --problem prob_0 --session temp/replay/prob_0
    # -> exit 3, produce temp/replay/prob_0/call_000_response.txt, rerun
"""

import argparse
import os
import sys
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils import llm as llm_module

LPWP_ATTENTION = """Note: While certain parameters in the example may not be utilized, it is imperative to include all of them in the function definition.
The function must return a tuple, with the first element being the objective value. A dictionary is not permitted as the return type."""
OR_ATTENTION = """The function name must be "def solve(data):" and the return must be a dict with same key as example.
You need to give your final answer in the Todo domain of example. Don't modify other contents in the example"""


class PendingResponse(BaseException):
    """Control-flow signal, deliberately not an Exception subclass so the
    client's fallback-model retry (``except Exception``) cannot swallow it."""

    def __init__(self, index: int, prompt_path: str) -> None:
        super().__init__(f"call {index} is waiting for a response")
        self.index = index
        self.prompt_path = prompt_path


def install_replay_transport(session_dir: str) -> None:
    counter = {"next": 0}

    def _request(self, model, prompt):
        index = counter["next"]
        counter["next"] += 1
        prompt_path = os.path.join(session_dir, f"call_{index:03d}_prompt.txt")
        with open(prompt_path, "w", encoding="utf8") as handle:
            handle.write(prompt)
        response_path = os.path.join(session_dir, f"call_{index:03d}_response.txt")
        if not os.path.exists(response_path):
            raise PendingResponse(index, prompt_path)
        with open(response_path, "r", encoding="utf8") as handle:
            text = handle.read()
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
            usage=SimpleNamespace(
                prompt_tokens=max(1, len(prompt) // 4),  # estimate; no API usage object
                completion_tokens=max(1, len(text) // 4),
            ),
            model=model,
        )

    llm_module.OpenAICompatibleLLM._request = _request


def main() -> int:
    parser = argparse.ArgumentParser(description="Record/replay runner for the ORMind pipeline.")
    parser.add_argument("--dataset", type=str, required=True, choices=["LPWP", "ComplexOR"])
    parser.add_argument("--problem", type=str, required=True, help="Exact problem name, e.g. prob_0 or Knapsack")
    parser.add_argument("--session", type=str, required=True, help="Session directory for prompts/responses/artifacts")
    parser.add_argument("--mode", type=str, choices=["paper", "standard", "extended"], default="paper")
    parser.add_argument("--max_repair_rounds", type=int, default=1)
    args = parser.parse_args()

    os.makedirs(args.session, exist_ok=True)
    install_replay_transport(args.session)

    from agent_team.ormind_pipeline import PipelineConfig
    from main import solve_problem
    from utils.test_generated_code import read_test_samples, test_generated_code, write_generated_code
    from utils.utils import read_OR_problem, read_problem

    if args.dataset == "LPWP":
        problem = read_problem(args.dataset, args.problem)
        attention = LPWP_ATTENTION
    else:
        problem = read_OR_problem(args.dataset, args.problem)
        attention = OR_ATTENTION
    samples = read_test_samples(args.dataset, args.problem)
    test_inputs = [sample["input"] for sample in samples]

    try:
        code, output, stats = solve_problem(
            problem_name=args.problem,
            problem=problem,
            attention=attention,
            test_inputs=test_inputs,
            path=args.session,
            mode=args.mode,
            config=PipelineConfig(max_repair_rounds=args.max_repair_rounds),
        )
    except PendingResponse as pending:
        print(f"WAITING call {pending.index:03d}")
        print(f"PROMPT  {pending.prompt_path}")
        print(f"Create  {os.path.join(args.session, f'call_{pending.index:03d}_response.txt')} and rerun.")
        return 3

    print("PIPELINE COMPLETED")
    print(f"Pipeline output: {output!r}")
    print(f"LLM calls: {stats['usage']['llm_calls']} | error repairs: {stats['error_repairs']} | "
          f"counterfactual triggered: {stats['counterfactual_triggered']}")

    write_generated_code(code)
    log_path = os.path.join(args.session, f"{args.problem}_test_log.txt")
    with open(log_path, "w", encoding="utf8") as handle:
        result = test_generated_code(args.problem, samples, handle)
    print(f"GRADED: {result.name} (log: {log_path})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
