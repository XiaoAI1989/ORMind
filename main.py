"""Entry point used by the experiment scripts.

Modes:
  paper     - the workflow evaluated in the paper (Algorithm 1, Appendix C
              prompts). Default.
  standard  - single-prompt baseline ("w/o All modules" in Table 2).
  extended  - post-publication research extensions; not used for any
              number reported in the paper.
"""

from typing import Any, Dict, List, Optional, Tuple

from agent_team.ormind_pipeline import ORMindPipeline, PipelineConfig, StandardPipeline
from agent_team.reflective_orchestrator import ReflectiveOrchestrator
from utils.config import resolve_runtime_config


def build_pipeline(
    mode: str = "paper",
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0,
    config: Optional[PipelineConfig] = None,
    num_candidates: int = 2,
    memory_file: Optional[str] = None,
):
    runtime_config = resolve_runtime_config(model=model, base_url=base_url, api_key=api_key)
    common = dict(
        model=runtime_config["model"],
        temperature=temperature,
        base_url=runtime_config["base_url"],
        api_key=runtime_config["api_key"],
        fallback_model=runtime_config["fallback_model"],
    )
    if mode == "standard":
        return StandardPipeline(**common)
    if mode == "extended":
        max_repair_rounds = config.max_repair_rounds if config else 2
        return ReflectiveOrchestrator(
            **common,
            memory_file=memory_file,
            max_candidates=num_candidates,
            max_repair_rounds=max_repair_rounds,
        )
    return ORMindPipeline(**common, config=config)


def solve_problem(
    problem_name: str,
    problem: Dict[str, Any],
    attention: str,
    test_inputs: List[dict],
    path: str,
    mode: str = "paper",
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0,
    config: Optional[PipelineConfig] = None,
    num_candidates: int = 2,
    memory_file: Optional[str] = None,
) -> Tuple[str, Any, Dict[str, Any]]:
    """Solve one problem and return (final_code, last_output, stats).

    ``test_inputs`` carries problem inputs only; reference outputs are
    never passed to any pipeline.
    """
    pipeline = build_pipeline(
        mode=mode,
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        config=config,
        num_candidates=num_candidates,
        memory_file=memory_file,
    )
    return pipeline.solve(
        problem_name=problem_name,
        problem=problem,
        attention=attention,
        test_inputs=test_inputs,
        path=path,
    )
