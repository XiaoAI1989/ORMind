from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SearchPlan:
    complexity_score: float
    candidate_styles: List[str]
    repair_rounds: int
    use_dual_formalization: bool
    trigger_formalization_synthesis: bool
    exploration_weight: float
    search_rationale: List[str]


class AdaptiveSearchController:
    """Allocate search budget by problem difficulty."""

    STYLE_BANK = [
        "faithful mathematical translation with explicit constraint coverage",
        "robust solver implementation with defensive indexing and stable formulations",
        "verification-aware implementation that anticipates counterfactual checks",
        "decomposition-oriented implementation with helper variables and solver-safe transformations",
    ]

    def create_plan(self, problem_text: str, memory_hits: int, max_candidates: int = 4) -> SearchPlan:
        token_count = len(problem_text.split())
        constraint_mentions = sum(problem_text.lower().count(marker) for marker in ["constraint", "subject to", "must", "at least", "at most"])
        array_mentions = sum(problem_text.lower().count(marker) for marker in ["array", "matrix", "vector", "shape", "index"])
        complexity_score = token_count / 120.0 + constraint_mentions * 0.35 + array_mentions * 0.4 - memory_hits * 0.25
        rationale = []
        if token_count >= 180:
            rationale.append("long natural-language specification")
        if constraint_mentions >= 3:
            rationale.append("dense constraint structure")
        if array_mentions >= 2:
            rationale.append("index-heavy formulation")
        if memory_hits:
            rationale.append("retrieved experience allows partial search pruning")

        if complexity_score >= 5.0:
            candidate_count = 4
            repair_rounds = 4
            use_dual_formalization = True
            trigger_synthesis = True
            exploration_weight = 0.35
        elif complexity_score >= 3.0:
            candidate_count = 3
            repair_rounds = 3
            use_dual_formalization = True
            trigger_synthesis = False
            exploration_weight = 0.25
        else:
            candidate_count = 2
            repair_rounds = 2
            use_dual_formalization = False
            trigger_synthesis = False
            exploration_weight = 0.15

        candidate_count = min(candidate_count, max(2, max_candidates))

        return SearchPlan(
            complexity_score=complexity_score,
            candidate_styles=self.STYLE_BANK[:candidate_count],
            repair_rounds=repair_rounds,
            use_dual_formalization=use_dual_formalization,
            trigger_formalization_synthesis=trigger_synthesis,
            exploration_weight=exploration_weight,
            search_rationale=rationale or ["default balanced search"],
        )

    def refine_plan(
        self,
        base_plan: SearchPlan,
        semantic_payload: Dict[str, object],
        formalization_consistency: float,
        max_candidates: int = 4,
    ) -> SearchPlan:
        complexity_score = base_plan.complexity_score
        candidate_styles = list(base_plan.candidate_styles)
        repair_rounds = base_plan.repair_rounds
        use_dual_formalization = base_plan.use_dual_formalization
        trigger_synthesis = base_plan.trigger_formalization_synthesis
        exploration_weight = base_plan.exploration_weight
        rationale = list(base_plan.search_rationale)

        ambiguities = semantic_payload.get("ambiguities", [])
        complexity_signals = semantic_payload.get("complexity_signals", [])
        decomposition_axes = semantic_payload.get("decomposition_axes", [])

        ambiguity_count = len(ambiguities) if isinstance(ambiguities, list) else 0
        complexity_count = len(complexity_signals) if isinstance(complexity_signals, list) else 0
        decomposition_count = len(decomposition_axes) if isinstance(decomposition_axes, list) else 0

        complexity_score += ambiguity_count * 0.25 + complexity_count * 0.2
        if ambiguity_count >= 2:
            trigger_synthesis = True
            use_dual_formalization = True
            rationale.append("semantic ambiguities trigger reflective synthesis")
        if decomposition_count >= 1 and len(candidate_styles) < max_candidates:
            candidate_styles.append(self.STYLE_BANK[min(len(candidate_styles), len(self.STYLE_BANK) - 1)])
            rationale.append("decomposition hint expands candidate search")

        if formalization_consistency < 0.55:
            trigger_synthesis = True
            use_dual_formalization = True
            repair_rounds += 1
            exploration_weight = min(0.45, exploration_weight + 0.1)
            rationale.append("low dual-formalization consistency increases deliberation")
        elif formalization_consistency > 0.8:
            exploration_weight = max(0.1, exploration_weight - 0.05)
            rationale.append("high consistency allows tighter exploitation")

        candidate_styles = candidate_styles[: max(2, max_candidates)]
        return SearchPlan(
            complexity_score=complexity_score,
            candidate_styles=candidate_styles,
            repair_rounds=repair_rounds,
            use_dual_formalization=use_dual_formalization,
            trigger_formalization_synthesis=trigger_synthesis,
            exploration_weight=exploration_weight,
            search_rationale=rationale,
        )
