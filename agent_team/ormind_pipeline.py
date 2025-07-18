"""Paper-faithful implementation of the ORMind workflow (Algorithm 1).

Control flow, mirroring Algorithm 1 of the paper:

  1. Theta_t <- SemanticEncoder(D_t)                       (Type 1)
  2. M_t     <- FormalizationThinking(D_t, Theta_t)        (Type 1)
  3. C_t     <- ExecutiveCompiler(M_t)
  4. F_t     <- Supervisor_forward(D_t, Theta_t, M_t, C_t)
  5. S_t     <- Run(F_t)                                    on inputs only
  6. if S_t indicates an error:
         R_t <- Reasoner_syntax(S_t, F_t)                  (Type 2)
         F_t <- Supervisor_backward(..., R_t); rerun       (<= max_repair_rounds times)
  7. R_t <- Reasoner_counterfactual(S_t, D_t)              (Type 2)
     if R_t indicates discrepancies with the problem facts:
         F_t <- Supervisor_backward(..., R_t); rerun

All intermediate outputs are exchanged through the shared CommentPool
(the memory pool P of Section 3.2).

Data hygiene: the pipeline receives raw problem inputs only. Reference
outputs (ground truth) live exclusively in the post-hoc grader
(utils.test_generated_code.test_generated_code), so no label information
can leak into any prompt, repair decision, or stored artifact.

Table 2 ablations are exposed through PipelineConfig:
  w/ Conductor                -> with_conductor=True
  w/ Terminology Interpreter  -> with_terminology_interpreter=True
  w/ Code Reviewer            -> with_code_reviewer=True
  w/o Semantic Encoder        -> use_semantic_encoder=False
  w/o Formalization Thinking  -> use_formalization_thinking=False
  w/o Counterfactual Analysis -> use_counterfactual_analysis=False
  w/o Syntax Error Analysis   -> use_syntax_error_analysis=False
  w/o All modules             -> StandardPipeline (mode "standard")
"""

import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from agent_team.code_reviewer import CodeReviewer
from agent_team.conductor import Conductor
from agent_team.executive_compiler import ExecutiveCompiler
from agent_team.formalization_thinking import FormalizationThinking
from agent_team.reasoner import System2Reasoner
from agent_team.semantic_encoder import SemanticEncoder
from agent_team.supervisor import MetacognitiveSupervisor
from agent_team.terminology_interpreter import TerminologyInterpreter
from utils.comment import Comment
from utils.comment_pool import CommentPool
from utils.llm import UsageTracker
from utils.test_generated_code import run_eval_code, run_generated_code, write_generated_code
from utils.utils import (
    extract_code_from_string,
    flatten_problem_description,
    format_constraint_results,
    get_dict_values_as_string,
)

NO_MODIFICATION_NEEDED = "Don't need to modify any constraints!"


@dataclass
class PipelineConfig:
    use_semantic_encoder: bool = True
    use_formalization_thinking: bool = True
    use_counterfactual_analysis: bool = True
    use_syntax_error_analysis: bool = True
    with_conductor: bool = False
    with_terminology_interpreter: bool = False
    with_code_reviewer: bool = False
    # Algorithm 1 contains a single error-triggered revision (lines 7-11).
    max_repair_rounds: int = 1


class ORMindPipeline:
    def __init__(
        self,
        model: str,
        temperature: float = 0,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        fallback_model: Optional[str] = None,
        config: Optional[PipelineConfig] = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.usage = UsageTracker()
        expert_kwargs = dict(
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=self.usage,
        )
        self.semantic_encoder = SemanticEncoder(**expert_kwargs)
        self.formalization_thinking = FormalizationThinking(**expert_kwargs)
        self.executive_compiler = ExecutiveCompiler(**expert_kwargs)
        self.metacognitive_supervisor = MetacognitiveSupervisor(**expert_kwargs)
        self.system2_reasoner = System2Reasoner(**expert_kwargs)
        self.terminology_interpreter = (
            TerminologyInterpreter(**expert_kwargs) if self.config.with_terminology_interpreter else None
        )
        self.code_reviewer = CodeReviewer(**expert_kwargs) if self.config.with_code_reviewer else None
        self.conductor = Conductor(**expert_kwargs) if self.config.with_conductor else None

    # ------------------------------------------------------------------
    # Thinking stage (Algorithm 1 lines 2-4): populate the memory pool.
    # ------------------------------------------------------------------
    def _thinking_experts(self) -> List[Any]:
        experts: List[Any] = []
        if self.terminology_interpreter is not None:
            experts.append(self.terminology_interpreter)
        if self.config.use_semantic_encoder:
            experts.append(self.semantic_encoder)
        if self.config.use_formalization_thinking:
            experts.append(self.formalization_thinking)
        experts.append(self.executive_compiler)
        if self.code_reviewer is not None:
            experts.append(self.code_reviewer)
        return experts

    def _run_thinking_stage(self, problem: Dict[str, Any], pool: CommentPool, trace: Dict[str, Any]) -> None:
        experts = pool.all_experts
        if self.conductor is not None:
            for _ in range(len(experts)):
                expert = self.conductor.forward(problem, pool, max_collaborate_nums=len(experts))
                if expert is None:
                    break
                self._consult(expert, problem, pool, trace)
        else:
            for expert in experts:
                self._consult(expert, problem, pool, trace)

    @staticmethod
    def _consult(expert: Any, problem: Dict[str, Any], pool: CommentPool, trace: Dict[str, Any]) -> None:
        comment_text = expert.forward(problem, pool)
        comment = Comment(expert, comment_text)
        pool.add_comment(comment)
        # Memory-pool update metadata (paper Appendix G): agent identifier
        # plus creation timestamp, recorded in the trace for traceability.
        trace["comments"].append(
            {"expert": expert.name, "text": comment_text, "created_at": comment.created_at}
        )

    # ------------------------------------------------------------------
    # Counterfactual analysis (Section 3.3.4): the System 2 Reasoner
    # writes a checker that asks which constraints would have to change
    # for the current solution to be valid. The checker is built from the
    # problem description and the solution values only.
    # ------------------------------------------------------------------
    def _build_counterfactual_feedback(
        self,
        problem_name: str,
        problem: Dict[str, Any],
        output: Any,
        test_inputs: List[dict],
        path: str,
    ) -> Tuple[str, str]:
        """Returns (feedback, status). Empty feedback means no revision needed."""
        if output is None or isinstance(output, str):
            return "", "skipped_no_solution"

        if problem_name.startswith("prob_"):
            if not isinstance(output, tuple) or len(output) < 2:
                return "", "skipped_unsupported_output"
            values: Dict[str, Any] = {"obj": output[0]}
            for index, value in enumerate(output[1:], start=1):
                values[f"var{index}"] = value
            eval_samples = [values]
            eval_example_path = os.path.join("example", "eval_code_example.py")
            input_content = get_dict_values_as_string(values)
        else:
            if not isinstance(output, dict) or "optimized_vars" not in output:
                return "", "skipped_unsupported_output"
            checker_kwargs = dict(output["optimized_vars"])
            # run_generated_code returns the output of the LAST input, so the
            # checker must receive that same input's data. (Every shipped
            # problem has exactly one test sample, but a multi-sample problem
            # would otherwise pair a solution with the wrong instance data.)
            checker_kwargs["data"] = test_inputs[-1] if test_inputs else {}
            eval_samples = [checker_kwargs]
            eval_example_path = os.path.join("example", "OR_eval_code_example.py")
            input_content = get_dict_values_as_string(checker_kwargs)

        with open(eval_example_path, "r", encoding="utf8") as handle:
            eval_code_example = handle.read()

        checker_response = self.system2_reasoner.build_counterfactual_checker(
            problem=problem,
            code_example=eval_code_example,
            input_content=input_content,
        )
        checker_code = extract_code_from_string(checker_response)

        os.makedirs("temp", exist_ok=True)
        with open(os.path.join("temp", "eval_code.py"), "w", encoding="utf8") as handle:
            handle.write(checker_code)
        with open(os.path.join(path, f"{problem_name}_eval_code.py"), "w", encoding="utf8") as handle:
            handle.write(checker_code)

        try:
            result = run_eval_code(eval_samples)
        except BaseException:
            return "", "checker_failed"

        if not isinstance(result, dict):
            return "", "checker_invalid_output"

        try:
            feedback = format_constraint_results(result)
        except Exception:
            return "", "checker_invalid_output"

        with open(os.path.join(path, f"{problem_name}_eval_result.txt"), "w", encoding="utf8") as handle:
            handle.write(feedback)

        if feedback != NO_MODIFICATION_NEEDED:
            return feedback, "discrepancy"
        return "", "clean"

    def _revise(self, problem: Dict[str, Any], previous_code: str, feedback: str, attention: str) -> str:
        revised = self.metacognitive_supervisor.backward(
            problem=problem,
            previous_code=previous_code,
            feedback=feedback,
            attention=attention,
        )
        return extract_code_from_string(revised).strip() or previous_code

    # ------------------------------------------------------------------
    # Algorithm 1 main loop.
    # ------------------------------------------------------------------
    def solve(
        self,
        problem_name: str,
        problem: Dict[str, Any],
        attention: str,
        test_inputs: List[dict],
        path: str,
    ) -> Tuple[str, Any, Dict[str, Any]]:
        config = self.config
        self.usage.reset()
        os.makedirs(path, exist_ok=True)

        trace: Dict[str, Any] = {
            "mode": "paper",
            "config": asdict(config),
            "comments": [],
            "repairs": [],
            "counterfactual": None,
        }

        pool = CommentPool(self._thinking_experts())
        self._run_thinking_stage(problem, pool, trace)

        raw_program = self.metacognitive_supervisor.forward(
            comment_text=pool.get_current_comment_text(),
            code_example=problem["code_example"],
            attention=attention,
        )
        code = extract_code_from_string(raw_program).strip()
        trace["initial_code"] = code

        error_repairs = 0
        counterfactual_done = False
        output: Any = None

        while True:
            write_generated_code(code)
            output = run_generated_code(problem_name, test_inputs)

            if isinstance(output, str):  # compile or runtime failure
                if error_repairs >= config.max_repair_rounds:
                    break
                if config.use_syntax_error_analysis:
                    diagnosis = self.system2_reasoner.diagnose_failure(code, output)
                    feedback = f"{output}\n\nSyntax error analysis:\n{diagnosis}"
                else:
                    feedback = output
                code = self._revise(problem, code, feedback, attention)
                error_repairs += 1
                trace["repairs"].append({"trigger": "execution_error", "feedback": feedback, "code": code})
                continue

            if config.use_counterfactual_analysis and not counterfactual_done:
                counterfactual_done = True
                feedback, status = self._build_counterfactual_feedback(
                    problem_name, problem, output, test_inputs, path
                )
                trace["counterfactual"] = {"status": status, "feedback": feedback}
                if feedback:
                    code = self._revise(problem, code, feedback, attention)
                    trace["repairs"].append({"trigger": "counterfactual", "feedback": feedback, "code": code})
                    continue
            break

        write_generated_code(code)

        stats = {
            "usage": self.usage.snapshot(),
            "error_repairs": error_repairs,
            "counterfactual_triggered": bool(
                trace["counterfactual"] and trace["counterfactual"]["status"] == "discrepancy"
            ),
            # Surfaced so the runner can report how often the checker ran
            # clean, found a discrepancy, or soft-failed.
            "counterfactual_status": trace["counterfactual"]["status"] if trace["counterfactual"] else "not_run",
        }
        trace["final_output_repr"] = repr(output)
        trace["usage"] = stats["usage"]
        with open(os.path.join(path, f"{problem_name}_ormind_trace.json"), "w", encoding="utf8") as handle:
            json.dump(trace, handle, ensure_ascii=False, indent=2)

        return code, output, stats


class StandardPipeline:
    """The "w/o All modules" baseline: a single direct prompt, no agents,
    no repair loop. Used for the last row of Table 2."""

    PROMPT = '''You are an operations research expert. Solve the following optimization problem by writing Python code with the PuLP library.

Problem:
{problem_description}

Your code must implement exactly the function interface from this code example, with the same function name, input arguments, and return style:
{code_example}

{attention}

Provide only the final Python code.'''

    def __init__(
        self,
        model: str,
        temperature: float = 0,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        fallback_model: Optional[str] = None,
        config: Optional[PipelineConfig] = None,
    ) -> None:
        del config
        from utils.llm import OpenAICompatibleLLM

        self.usage = UsageTracker()
        self.llm = OpenAICompatibleLLM(
            model_name=model,
            temperature=temperature,
            openai_api_base=base_url,
            api_key=api_key,
            max_retries=2,
            fallback_model=fallback_model,
            usage_tracker=self.usage,
        )

    def solve(
        self,
        problem_name: str,
        problem: Dict[str, Any],
        attention: str,
        test_inputs: List[dict],
        path: str,
    ) -> Tuple[str, Any, Dict[str, Any]]:
        self.usage.reset()
        os.makedirs(path, exist_ok=True)
        prompt = self.PROMPT.format(
            problem_description=flatten_problem_description(problem["description"]),
            code_example=problem["code_example"],
            attention=attention,
        )
        response = self.llm.invoke(prompt).content
        code = extract_code_from_string(response).strip()
        write_generated_code(code)
        output = run_generated_code(problem_name, test_inputs)
        stats = {
            "usage": self.usage.snapshot(),
            "error_repairs": 0,
            "counterfactual_triggered": False,
            "counterfactual_status": "not_run",
        }
        return code, output, stats
