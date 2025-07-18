"""Prompt variants used only by the extended (post-publication) pipeline.

These templates are NOT the ones from the paper. The paper's templates
live in the canonical agent modules (semantic_encoder.py, etc.). Keeping
the extended variants in a separate module makes it impossible to confuse
the two when auditing the paper-faithful path.
"""

from agent_team.base_expert import BaseExpert


class ExtendedSemanticEncoder(BaseExpert):
    ROLE_DESCRIPTION = (
        "You are the Semantic Encoder in ORMind. "
        "Your task is to transform an optimization problem description into a concise structured schema."
    )
    FORWARD_TASK = """
Problem description:
{problem_description}

Reference code interface:
{code_example}

Retrieved experience:
{memory_notes}

Return JSON only with this schema:
{{
  "problem_family": "...",
  "parameters": [
    {{
      "name": "...",
      "type": "...",
      "shape": "...",
      "definition": "..."
    }}
  ],
  "entities": ["..."],
  "decision_signals": ["..."],
  "objective_signals": ["..."],
  "constraint_signals": ["..."],
  "edge_cases": ["..."],
  "complexity_signals": ["..."],
  "ambiguities": ["..."],
  "decomposition_axes": ["..."]
}}
"""

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="Semantic Encoder (extended)",
            description="Extracts typed parameters, entities, and high-risk signals from natural language.",
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def encode(self, problem_description: str, code_example: str, memory_notes: str) -> str:
        return self.invoke_forward(
            problem_description=problem_description,
            code_example=code_example,
            memory_notes=memory_notes,
        )


class ExtendedFormalization(BaseExpert):
    ROLE_DESCRIPTION = (
        "You are the Formalization Thinking module in ORMind. "
        "Translate business language into an explicit optimization formulation."
    )

    FORWARD_TASK = """
Problem description:
{problem_description}

Semantic encoding:
{semantic_schema}

Retrieved experience:
{memory_notes}

Reasoning lens:
{reasoning_lens}

Return JSON only:
{{
  "variables": ["..."],
  "objective": "...",
  "constraints": ["..."],
  "assumptions": ["..."],
  "solver_notes": ["..."],
  "verification_targets": ["..."]
}}
"""

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="Formalization Thinking (extended)",
            description="Builds the mathematical model, constraint set, and solver notes.",
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def formalize(
        self,
        problem_description: str,
        semantic_schema: str,
        memory_notes: str,
        reasoning_lens: str = "balanced formulation",
    ) -> str:
        return self.invoke_forward(
            problem_description=problem_description,
            semantic_schema=semantic_schema,
            memory_notes=memory_notes,
            reasoning_lens=reasoning_lens,
        )


class ExtendedCompiler(BaseExpert):
    ROLE_DESCRIPTION = (
        "You are the Executive Compiler in ORMind. "
        "Transform the mathematical model into executable, reusable optimization code."
    )
    FORWARD_TASK = """
Problem description:
{problem_description}

Semantic encoding:
{semantic_schema}

Formalization:
{formalization}

Candidate style:
{candidate_style}

Retrieved experience:
{memory_notes}

Code example:
{code_example}

Attention:
{attention}

Requirements:
1. Follow the exact function name, input arguments, and return style from the code example.
2. Use PuLP.
3. Avoid unsupported PuLP patterns such as direct division of LpVariable objects.
4. Add only minimal comments where they improve readability.
5. Do not include example usage.

Return exactly:
SUMMARY:
<brief summary>

RISKS:
- <risk>
- <risk>

```python
<code>
```
"""

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="Executive Compiler (extended)",
            description="Generates executable solver code from the formalized model.",
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def compile_candidate(
        self,
        problem_description: str,
        semantic_schema: str,
        formalization: str,
        candidate_style: str,
        memory_notes: str,
        code_example: str,
        attention: str,
    ) -> str:
        return self.invoke_forward(
            problem_description=problem_description,
            semantic_schema=semantic_schema,
            formalization=formalization,
            candidate_style=candidate_style,
            memory_notes=memory_notes,
            code_example=code_example,
            attention=attention,
        )


class ExtendedReasoner(BaseExpert):
    """Counterfactual checker generator with a verification lens and a
    structured, quantified output contract.

    Extends the paper's Section 3.3.4 mechanism (which constraints would
    need to change for the solution to be valid) in two directions:
    each checker instance audits the problem through a different lens,
    and every reported modification carries a canonical constraint
    expression plus a violation magnitude so that reports from multiple
    checkers can be cross-validated and ranked.
    """

    ROLE_DESCRIPTION = (
        "You are the System 2 Reasoner in ORMind. You provide deliberate verification "
        "through counterfactual reasoning: you determine which conditions would need to "
        "change for a candidate solution to become valid, and quantify each violation."
    )

    FORWARD_TASK = '''Analyze the following optimization problem:
{problem_description}

Task: Write a Python function that identifies which specific constraints or conditions in the given problem are not satisfied by the candidate solution. Each unsatisfied condition would need modification for the solution to become valid and optimal.

Verification lens (focus your audit accordingly, but still cover every constraint):
{verification_lens}

Function specifications:
- Input arguments and their types: {input_content}
- Adhere to the given data types.
- Reference this code structure: {code_example}
- The function must return a dict with one entry per checked condition plus a top-level "solution_valid_without_changes" boolean.
- Each condition entry must be a dict of the form:
  {{"modification_needed": <bool>, "suggestion": <str or None>, "constraint": "<canonical constraint expression using the input argument names>", "violated_by": <float, absolute amount by which the condition is violated, 0.0 if satisfied>}}
- Import the necessary libraries.

Notes:
The code example is only for reference in terms of format and structure. Generate code specifically for the given problem, not based on any examples.
All specific constraints should be determined based on the problem description provided.
Make sure to include checks for all constraints mentioned in the problem description. Don't give any Example usages.'''

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="System 2 Reasoner (extended)",
            description="Generates lens-specific, quantified counterfactual checkers.",
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def build_counterfactual_checker(
        self,
        problem_description: str,
        code_example: str,
        input_content: str,
        verification_lens: str,
    ) -> str:
        return self.invoke_forward(
            problem_description=problem_description,
            code_example=code_example,
            input_content=input_content,
            verification_lens=verification_lens,
        )


class ExtendedSupervisor(BaseExpert):
    ROLE_DESCRIPTION = (
        "You are the Metacognitive Supervisor in ORMind. "
        "You monitor intermediate outputs, select the most reliable program candidate, "
        "and revise code after feedback."
    )
    FORWARD_TASK = """
Problem description:
{problem_description}

Semantic encoding:
{semantic_schema}

Formalization:
{formalization}

Candidate A:
{candidate_a}

Candidate B:
{candidate_b}

Candidate diagnostics:
{candidate_diagnostics}

Code example:
{code_example}

Attention:
{attention}

Return JSON only:
{{
  "selected_candidate": "A or B",
  "selection_rationale": "...",
  "must_fix_before_run": ["..."],
  "final_code": "<python code only, no markdown fences>"
}}
"""

    BACKWARD_TASK = """
Problem description:
{problem_description}

Semantic encoding:
{semantic_schema}

Formalization:
{formalization}

Code example:
{code_example}

Attention:
{attention}

Previous code:
{previous_code}

Feedback:
{feedback}

Requirements:
1. Preserve the exact function signature and return style from the code example.
2. Repair the actual issue.
3. Do not add example usage.
4. Return Python code only without markdown fences.
"""

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="Metacognitive Supervisor (extended)",
            description="Selects, normalizes, and revises executable solutions.",
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def select_and_format(
        self,
        problem_description: str,
        semantic_schema: str,
        formalization: str,
        candidate_a: str,
        candidate_b: str,
        candidate_diagnostics: str,
        code_example: str,
        attention: str,
    ) -> str:
        return self.invoke_forward(
            problem_description=problem_description,
            semantic_schema=semantic_schema,
            formalization=formalization,
            candidate_a=candidate_a,
            candidate_b=candidate_b,
            candidate_diagnostics=candidate_diagnostics,
            code_example=code_example,
            attention=attention,
        )

    def revise(
        self,
        problem_description: str,
        semantic_schema: str,
        formalization: str,
        code_example: str,
        attention: str,
        previous_code: str,
        feedback: str,
    ) -> str:
        return self.invoke_backward(
            problem_description=problem_description,
            semantic_schema=semantic_schema,
            formalization=formalization,
            code_example=code_example,
            attention=attention,
            previous_code=previous_code,
            feedback=feedback,
        )
