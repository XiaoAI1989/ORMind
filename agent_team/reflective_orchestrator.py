"""Extended ORMind pipeline (post-publication research extensions).

This mode is NOT the configuration evaluated in the paper. It layers
adaptive search, dual-view formalization, an online preference verifier,
and an experience memory on top of the paper's backbone. It is disabled
by default and enabled with ``--mode extended``.

Data hygiene matches the paper pipeline: the orchestrator receives raw
problem inputs only. Acceptance signals used for the online preference
model and the experience memory are derived exclusively from execution
status and counterfactual checks — never from reference outputs.
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from agent_team.extended_experts import (
    ExtendedCompiler,
    ExtendedFormalization,
    ExtendedReasoner,
    ExtendedSemanticEncoder,
    ExtendedSupervisor,
)
from agent_team.reasoner import System2Reasoner
from utils.adaptive_search import AdaptiveSearchController
from utils.experience_distiller import ExperienceDistiller
from utils.llm import UsageTracker
from utils.online_preference import OnlinePreferenceModel
from utils.test_generated_code import run_eval_code, run_generated_code, write_generated_code
from utils.utils import (
    clean_markdown_block,
    extract_code_from_string,
    flatten_problem_description,
    format_constraint_results,
    get_dict_values_as_string,
)

NO_MODIFICATION_NEEDED = "Don't need to modify any constraints!"


def safe_json_loads(text: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = clean_markdown_block(text)
    try:
        loaded = json.loads(cleaned)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass
    return fallback


@dataclass
class CandidateProgram:
    name: str
    style: str
    raw_response: str
    code: str
    formalization: str
    static_valid: bool
    preference_score: float = 0.5
    selection_score: float = 0.5
    preference_uncertainty: float = 1.0
    feature_vector: Optional[Dict[str, float]] = None


class ReflectiveOrchestrator:
    def __init__(
        self,
        model: str,
        temperature: float = 0,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        fallback_model: Optional[str] = None,
        memory_file: Optional[str] = None,
        max_repair_rounds: int = 2,
        max_candidates: int = 4,
    ) -> None:
        self.usage = UsageTracker()
        expert_kwargs = dict(
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=self.usage,
        )
        self.semantic_encoder = ExtendedSemanticEncoder(**expert_kwargs)
        self.formalization = ExtendedFormalization(**expert_kwargs)
        self.executive_compiler = ExtendedCompiler(**expert_kwargs)
        self.metacognitive_supervisor = ExtendedSupervisor(**expert_kwargs)
        self.system2_reasoner = System2Reasoner(**expert_kwargs)
        self.counterfactual_reasoner = ExtendedReasoner(**expert_kwargs)
        memory_root = memory_file or os.path.join("temp", "agent_experience_memory.jsonl")
        model_root = os.path.splitext(memory_root)[0]
        self.memory_bank = ExperienceDistiller(memory_root)
        self.preference_model = OnlinePreferenceModel(model_root + "_preference_model.json")
        self.search_controller = AdaptiveSearchController()
        self.max_repair_rounds = max(1, max_repair_rounds)
        self.max_candidates = max(2, max_candidates)

    def _compile_check(self, code: str) -> bool:
        try:
            compile(code, "<candidate>", "exec")
            return True
        except Exception:
            return False

    def _semantic_payload(self, semantic_schema: str) -> Dict[str, Any]:
        return safe_json_loads(semantic_schema, {})

    def _extract_problem_family(self, semantic_schema: str) -> str:
        payload = self._semantic_payload(semantic_schema)
        explicit_family = str(payload.get("problem_family", "")).strip()
        if explicit_family:
            return explicit_family
        entities = payload.get("entities", [])
        objective_signals = payload.get("objective_signals", [])
        if isinstance(entities, list) and isinstance(objective_signals, list):
            return "|".join((entities[:2] + objective_signals[:1])) or "generic_or"
        return "generic_or"

    def _formalization_consistency(self, formalizations: List[str]) -> float:
        """Jaccard agreement over the *values* of the parsed formalizations.

        Schema keys are excluded on purpose: they are shared by
        construction and would otherwise inflate the score.
        """
        if len(formalizations) <= 1:
            return 1.0
        token_sets = []
        for formalization in formalizations:
            payload = safe_json_loads(formalization, {})
            source = json.dumps(list(payload.values()), ensure_ascii=True) if payload else formalization
            tokens = set(re.findall(r"[a-zA-Z_]+", source.lower()))
            if tokens:
                token_sets.append(tokens)
        if len(token_sets) <= 1:
            return 1.0
        intersections = []
        for left_index in range(len(token_sets)):
            for right_index in range(left_index + 1, len(token_sets)):
                left = token_sets[left_index]
                right = token_sets[right_index]
                union = left | right
                intersections.append(len(left & right) / max(1, len(union)))
        return sum(intersections) / max(1, len(intersections))

    def _normalize_selected_candidate(
        self,
        selected_candidate: str,
        primary_candidate: CandidateProgram,
        secondary_candidate: CandidateProgram,
    ) -> str:
        normalized = str(selected_candidate).strip()
        alias_map = {
            "A": primary_candidate.name,
            "B": secondary_candidate.name,
            "Candidate A": primary_candidate.name,
            "Candidate B": secondary_candidate.name,
            primary_candidate.name: primary_candidate.name,
            secondary_candidate.name: secondary_candidate.name,
        }
        return alias_map.get(normalized, primary_candidate.name)

    def _candidate_features(
        self,
        problem_text: str,
        formalization: str,
        code: str,
        style: str,
        memory_hits: int,
        static_valid: bool,
        formalization_consistency: float,
    ) -> Dict[str, float]:
        lower_code = code.lower()
        lower_problem = problem_text.lower()
        return {
            "bias": 1.0,
            "problem_length": min(len(problem_text.split()) / 300.0, 3.0),
            "formalization_length": min(len(formalization.split()) / 220.0, 3.0),
            "code_length": min(len(code.splitlines()) / 120.0, 3.0),
            "uses_lpvariable_dicts": 1.0 if "lpvariable.dicts" in lower_code else 0.0,
            "uses_lpSum": 1.0 if "lpsum" in lower_code else 0.0,
            "uses_numpy": 1.0 if "numpy" in lower_code or "np." in lower_code else 0.0,
            "uses_helper_functions": 1.0 if code.count("def ") > 1 else 0.0,
            "unsafe_variable_division": 1.0 if re.search(r"[A-Za-z_]\w*\s*/\s*[A-Za-z_]\w*", code) else 0.0,
            "static_valid": 1.0 if static_valid else 0.0,
            "style_robust": 1.0 if "robust" in style else 0.0,
            "style_verify": 1.0 if "verification" in style else 0.0,
            "style_decompose": 1.0 if "decomposition" in style else 0.0,
            "problem_has_arrays": 1.0 if any(token in lower_problem for token in ["array", "matrix", "vector", "shape"]) else 0.0,
            "memory_hits": float(memory_hits),
            "formalization_consistency": formalization_consistency,
        }

    def _diagnostics_text(
        self,
        candidates: List[CandidateProgram],
        search_plan,
        formalization_consistency: float,
    ) -> str:
        lines = [
            f"Adaptive search complexity score: {search_plan.complexity_score:.2f}",
            f"Dual-formalization consistency: {formalization_consistency:.3f}",
            f"Exploration weight: {search_plan.exploration_weight:.2f}",
            f"Search rationale: {'; '.join(search_plan.search_rationale)}",
        ]
        for candidate in candidates[:3]:
            lines.append(
                f"{candidate.name}: verifier_score={candidate.preference_score:.3f}, "
                f"selection_score={candidate.selection_score:.3f}, "
                f"uncertainty={candidate.preference_uncertainty:.3f}, static_valid={candidate.static_valid}, "
                f"style={candidate.style}"
            )
        return "\n".join(lines)

    def _build_candidates(
        self,
        problem_text: str,
        semantic_schema: str,
        formalizations: List[str],
        memory_notes: str,
        code_example: str,
        attention: str,
        candidate_styles: List[str],
        memory_hits: int,
        exploration_weight: float,
        formalization_consistency: float,
    ) -> List[CandidateProgram]:
        candidates: List[CandidateProgram] = []
        for index, style in enumerate(candidate_styles, start=1):
            formalization = formalizations[(index - 1) % len(formalizations)]
            name = f"Candidate-{chr(64 + index)}"
            raw = self.executive_compiler.compile_candidate(
                problem_description=problem_text,
                semantic_schema=semantic_schema,
                formalization=formalization,
                candidate_style=style,
                memory_notes=memory_notes,
                code_example=code_example,
                attention=attention,
            )
            code = extract_code_from_string(raw).strip()
            static_valid = self._compile_check(code)
            features = self._candidate_features(
                problem_text=problem_text,
                formalization=formalization,
                code=code,
                style=style,
                memory_hits=memory_hits,
                static_valid=static_valid,
                formalization_consistency=formalization_consistency,
            )
            prediction = self.preference_model.score_candidate(features, exploration_weight=exploration_weight)
            candidates.append(
                CandidateProgram(
                    name=name,
                    style=style,
                    raw_response=raw,
                    code=code,
                    formalization=formalization,
                    static_valid=static_valid,
                    preference_score=self.preference_model.predict(features).score,
                    selection_score=prediction.score,
                    preference_uncertainty=prediction.uncertainty,
                    feature_vector=features,
                )
            )
        candidates.sort(
            key=lambda item: (item.selection_score, item.preference_score, item.static_valid, -item.preference_uncertainty),
            reverse=True,
        )
        return candidates

    def _supervise_initial_program(
        self,
        problem_text: str,
        semantic_schema: str,
        formalization: str,
        candidates: List[CandidateProgram],
        candidate_diagnostics: str,
        code_example: str,
        attention: str,
    ) -> Dict[str, Any]:
        fallback = {
            "selected_candidate": candidates[0].name,
            "selection_rationale": "Fallback selection.",
            "must_fix_before_run": [],
            "final_code": candidates[0].code,
        }
        second_candidate = candidates[1] if len(candidates) > 1 else candidates[0]
        response = self.metacognitive_supervisor.select_and_format(
            problem_description=problem_text,
            semantic_schema=semantic_schema,
            formalization=formalization,
            candidate_a=candidates[0].raw_response,
            candidate_b=second_candidate.raw_response,
            candidate_diagnostics=candidate_diagnostics,
            code_example=code_example,
            attention=attention,
        )
        decision = safe_json_loads(response, fallback)
        decision["selected_candidate"] = self._normalize_selected_candidate(
            decision.get("selected_candidate", ""),
            candidates[0],
            second_candidate,
        )
        decision["final_code"] = clean_markdown_block(decision.get("final_code", "")).strip() or candidates[0].code
        return decision

    def _revise_program(
        self,
        problem_text: str,
        semantic_schema: str,
        formalization: str,
        code_example: str,
        attention: str,
        previous_code: str,
        feedback: str,
    ) -> str:
        revised = self.metacognitive_supervisor.revise(
            problem_description=problem_text,
            semantic_schema=semantic_schema,
            formalization=formalization,
            code_example=code_example,
            attention=attention,
            previous_code=previous_code,
            feedback=feedback,
        )
        return clean_markdown_block(revised).strip() or previous_code

    CHECKER_LENSES = [
        "resource, capacity and budget constraints",
        "ratio, ordering, bound and integrality constraints",
    ]

    @staticmethod
    def _violation_key(entry: Dict[str, Any]) -> str:
        source = entry.get("constraint") or entry.get("suggestion") or ""
        return re.sub(r"\s+", "", str(source)).lower()

    def _build_counterfactual_feedback(
        self,
        problem_name: str,
        problem: Dict[str, Any],
        output: Any,
        test_inputs: List[dict],
        path: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Consensus counterfactual verification.

        Generates one checker per verification lens, executes each on the
        candidate solution, and keeps only violations confirmed by at
        least two independent checkers (cross-validated by canonical
        constraint expression). Confirmed violations are ranked by
        magnitude. A violation flagged by a single checker is logged as
        unconfirmed and does NOT trigger a revision, which suppresses
        checker hallucinations.

        Returns (feedback, status, detail); empty feedback means no
        revision is needed.
        """
        detail: Dict[str, Any] = {"confirmed": [], "unconfirmed": [], "valid_reports": 0}
        if output is None or isinstance(output, str):
            return "", "skipped_no_solution", detail

        if problem_name.startswith("prob_"):
            if not isinstance(output, tuple) or len(output) < 2:
                return "", "skipped_unsupported_output", detail
            values: Dict[str, Any] = {"obj": output[0]}
            for index, value in enumerate(output[1:], start=1):
                values[f"var{index}"] = value
            eval_samples = [values]
            eval_example_path = os.path.join("example", "eval_code_example.py")
            input_content = get_dict_values_as_string(values)
        else:
            if not isinstance(output, dict) or "optimized_vars" not in output:
                return "", "skipped_unsupported_output", detail
            checker_kwargs = dict(output["optimized_vars"])
            # Pair the checker with the LAST input's data, matching the output
            # that run_generated_code returned (see ormind_pipeline).
            checker_kwargs["data"] = test_inputs[-1] if test_inputs else {}
            eval_samples = [checker_kwargs]
            eval_example_path = os.path.join("example", "OR_eval_code_example.py")
            input_content = get_dict_values_as_string(checker_kwargs)

        with open(eval_example_path, "r", encoding="utf8") as handle:
            eval_code_example = handle.read()

        os.makedirs("temp", exist_ok=True)
        reports: List[Dict[str, Any]] = []
        for lens_index, lens in enumerate(self.CHECKER_LENSES):
            checker_response = self.counterfactual_reasoner.build_counterfactual_checker(
                problem_description=flatten_problem_description(problem["description"]),
                code_example=eval_code_example,
                input_content=input_content,
                verification_lens=lens,
            )
            checker_code = extract_code_from_string(checker_response)
            checker_path = os.path.join("temp", f"eval_code_k{lens_index}.py")
            with open(checker_path, "w", encoding="utf8") as handle:
                handle.write(checker_code)
            with open(os.path.join(path, f"{problem_name}_eval_code_k{lens_index}.py"), "w", encoding="utf8") as handle:
                handle.write(checker_code)
            try:
                result = run_eval_code(eval_samples, code_path=checker_path)
            except BaseException:
                continue
            if isinstance(result, dict):
                reports.append(result)

        detail["valid_reports"] = len(reports)
        if not reports:
            return "", "checker_failed", detail

        # Collect violations per report, keyed by canonical constraint.
        per_report_keys: List[set] = []
        violation_info: Dict[str, Dict[str, Any]] = {}
        for report in reports:
            keys = set()
            for name, entry in report.items():
                if name == "solution_valid_without_changes" or not isinstance(entry, dict):
                    continue
                if not entry.get("modification_needed"):
                    continue
                key = self._violation_key(entry)
                if not key:
                    continue
                keys.add(key)
                magnitude = entry.get("violated_by")
                try:
                    magnitude = abs(float(magnitude))
                except (TypeError, ValueError):
                    magnitude = 0.0
                known = violation_info.get(key)
                if known is None or magnitude > known["violated_by"]:
                    violation_info[key] = {
                        "suggestion": entry.get("suggestion") or key,
                        "constraint": entry.get("constraint", ""),
                        "violated_by": magnitude,
                    }
            per_report_keys.append(keys)

        all_keys = set().union(*per_report_keys) if per_report_keys else set()
        if not all_keys:
            return "", "clean", detail

        if len(reports) == 1:
            confirmed_keys = all_keys
        else:
            confirmed_keys = {key for key in all_keys if sum(key in keys for keys in per_report_keys) >= 2}
        unconfirmed_keys = all_keys - confirmed_keys

        ranked = sorted(
            (violation_info[key] for key in confirmed_keys),
            key=lambda item: item["violated_by"],
            reverse=True,
        )
        detail["confirmed"] = ranked
        detail["unconfirmed"] = [violation_info[key] for key in unconfirmed_keys]

        report_lines = [f"Valid checker reports: {len(reports)}"]
        for item in ranked:
            report_lines.append(f"CONFIRMED (violated_by={item['violated_by']}): {item['suggestion']}")
        for item in detail["unconfirmed"]:
            report_lines.append(f"unconfirmed (single checker, no revision): {item['suggestion']}")
        with open(os.path.join(path, f"{problem_name}_eval_result.txt"), "w", encoding="utf8") as handle:
            handle.write("\n".join(report_lines) if ranked or detail["unconfirmed"] else NO_MODIFICATION_NEEDED)

        if ranked:
            feedback = "\n".join(item["suggestion"] for item in ranked)
            return feedback, "discrepancy", detail
        return "", "unconfirmed_only", detail

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
        problem_text = flatten_problem_description(problem["description"])
        code_example = problem["code_example"]
        initial_memory_records = self.memory_bank.retrieve(problem_text)
        memory_notes = self.memory_bank.format_notes(initial_memory_records)
        search_plan = self.search_controller.create_plan(problem_text, len(initial_memory_records), self.max_candidates)

        semantic_schema = self.semantic_encoder.encode(problem_text, code_example, memory_notes)
        semantic_payload = self._semantic_payload(semantic_schema)
        problem_family = self._extract_problem_family(semantic_schema)

        refined_memory_records = self.memory_bank.retrieve(problem_text, problem_family=problem_family)
        if refined_memory_records and refined_memory_records != initial_memory_records:
            memory_notes = self.memory_bank.format_notes(refined_memory_records)
            semantic_schema = self.semantic_encoder.encode(problem_text, code_example, memory_notes)
            semantic_payload = self._semantic_payload(semantic_schema)
            problem_family = self._extract_problem_family(semantic_schema)
        memory_records = refined_memory_records or initial_memory_records

        formalizations = [
            self.formalization.formalize(
                problem_text,
                semantic_schema,
                memory_notes,
                reasoning_lens="constraint-first feasibility lens",
            )
        ]
        if search_plan.use_dual_formalization:
            formalizations.append(
                self.formalization.formalize(
                    problem_text,
                    semantic_schema,
                    memory_notes,
                    reasoning_lens="objective-first utility lens with solver-safe transformations",
                )
            )
        formalization_consistency = self._formalization_consistency(formalizations)
        search_plan = self.search_controller.refine_plan(
            search_plan,
            semantic_payload,
            formalization_consistency,
            self.max_candidates,
        )
        if search_plan.use_dual_formalization and len(formalizations) == 1:
            formalizations.append(
                self.formalization.formalize(
                    problem_text,
                    semantic_schema,
                    memory_notes,
                    reasoning_lens="objective-first utility lens with solver-safe transformations",
                )
            )
            formalization_consistency = self._formalization_consistency(formalizations)
            if formalization_consistency < 0.55:
                search_plan.trigger_formalization_synthesis = True
        if search_plan.trigger_formalization_synthesis:
            synthesis_formalization = self.formalization.formalize(
                problem_text,
                semantic_schema,
                memory_notes,
                reasoning_lens="consensus synthesis over competing formalizations with explicit verifier targets",
            )
            if synthesis_formalization not in formalizations:
                formalizations.append(synthesis_formalization)
                formalization_consistency = self._formalization_consistency(formalizations)

        candidates = self._build_candidates(
            problem_text,
            semantic_schema,
            formalizations,
            memory_notes,
            code_example,
            attention,
            search_plan.candidate_styles,
            len(memory_records),
            search_plan.exploration_weight,
            formalization_consistency,
        )
        fused_formalization = "\n\n".join(formalizations)
        candidate_diagnostics = self._diagnostics_text(candidates, search_plan, formalization_consistency)
        supervisor_decision = self._supervise_initial_program(
            problem_text,
            semantic_schema,
            fused_formalization,
            candidates,
            candidate_diagnostics,
            code_example,
            attention,
        )

        code = supervisor_decision["final_code"]
        lessons = [str(item) for item in supervisor_decision.get("must_fix_before_run", [])]
        repair_budget = max(self.max_repair_rounds, search_plan.repair_rounds)

        error_repairs = 0
        counterfactual_done = False
        counterfactual_status = "not_run"
        counterfactual_detail: Dict[str, Any] = {}
        output: Any = None

        while True:
            write_generated_code(code)
            output = run_generated_code(problem_name, test_inputs)

            if isinstance(output, str):  # compile or runtime failure
                if error_repairs >= repair_budget:
                    break
                diagnosis = self.system2_reasoner.diagnose_failure(code, output)
                feedback = f"{output}\n\nSystem 2 diagnosis:\n{diagnosis}"
                lessons.append(feedback[:1000])
                code = self._revise_program(
                    problem_text,
                    semantic_schema,
                    fused_formalization,
                    code_example,
                    attention,
                    code,
                    feedback,
                )
                error_repairs += 1
                continue

            if not counterfactual_done:
                counterfactual_done = True
                feedback, counterfactual_status, counterfactual_detail = self._build_counterfactual_feedback(
                    problem_name, problem, output, test_inputs, path
                )
                if feedback:
                    lessons.append(f"Counterfactual feedback: {feedback}"[:1000])
                    code = self._revise_program(
                        problem_text,
                        semantic_schema,
                        fused_formalization,
                        code_example,
                        attention,
                        code,
                        feedback,
                    )
                    continue
            break

        write_generated_code(code)

        # Success signal for online learning: clean execution plus a clean
        # (or at least non-failing) counterfactual check. Reference outputs
        # are never consulted here.
        executed_cleanly = output is not None and not isinstance(output, str)
        success = executed_cleanly and counterfactual_status in ("clean", "skipped_unsupported_output", "not_run")

        winning_candidate = supervisor_decision.get("selected_candidate", candidates[0].name)
        selected_program = next(
            (candidate for candidate in candidates if candidate.name == winning_candidate), candidates[0]
        )
        if success and selected_program.feature_vector:
            for candidate in candidates:
                if candidate is selected_program or not candidate.feature_vector:
                    continue
                self.preference_model.update_preference_pair(selected_program.feature_vector, candidate.feature_vector)
        else:
            for candidate in candidates:
                if candidate.feature_vector:
                    self.preference_model.update(candidate.feature_vector, 0)

        self.memory_bank.record(
            problem_name=problem_name,
            problem_text=problem_text,
            problem_family=problem_family,
            semantic_schema=semantic_schema,
            formalizations=formalizations,
            candidate_summaries=[
                {
                    "name": candidate.name,
                    "style": candidate.style,
                    "preference_score": candidate.preference_score,
                    "uncertainty": candidate.preference_uncertainty,
                    "static_valid": candidate.static_valid,
                }
                for candidate in candidates
            ],
            accepted=success,
            lessons=lessons + [f"Search rationale: {'; '.join(search_plan.search_rationale)}"],
        )

        stats = {
            "usage": self.usage.snapshot(),
            "error_repairs": error_repairs,
            "counterfactual_triggered": counterfactual_status == "discrepancy",
            "counterfactual_status": counterfactual_status,
        }
        with open(os.path.join(path, f"{problem_name}_ormind_trace.json"), "w", encoding="utf8") as handle:
            json.dump(
                {
                    "mode": "extended",
                    "semantic_schema": semantic_schema,
                    "formalizations": formalizations,
                    "search_plan": {
                        "complexity_score": search_plan.complexity_score,
                        "candidate_styles": search_plan.candidate_styles,
                        "repair_rounds": repair_budget,
                        "use_dual_formalization": search_plan.use_dual_formalization,
                        "trigger_formalization_synthesis": search_plan.trigger_formalization_synthesis,
                        "exploration_weight": search_plan.exploration_weight,
                        "search_rationale": search_plan.search_rationale,
                    },
                    "formalization_consistency": formalization_consistency,
                    "supervisor_decision": supervisor_decision,
                    "candidate_scores": [
                        {
                            "name": candidate.name,
                            "style": candidate.style,
                            "preference_score": candidate.preference_score,
                            "selection_score": candidate.selection_score,
                            "uncertainty": candidate.preference_uncertainty,
                            "static_valid": candidate.static_valid,
                        }
                        for candidate in candidates
                    ],
                    "counterfactual_status": counterfactual_status,
                    "counterfactual_detail": counterfactual_detail,
                    "executed_cleanly": executed_cleanly,
                    "usage": stats["usage"],
                },
                handle,
                ensure_ascii=False,
                indent=2,
            )

        return code, output, stats
