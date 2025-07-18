from agent_team.base_expert import BaseExpert
from utils.utils import flatten_problem_description


class System2Reasoner(BaseExpert):
    """Type 2 (analytical) processing.

    Forward: generates the counterfactual checker function described in
    Section 3.3.4 — a program that asks which constraints would need to be
    modified for the candidate solution to become valid. The template is
    the Appendix C prompt, kept verbatim.

    Backward: syntax error analysis. The paper does not publish this
    template; the one below reproduces the behaviour shown in the
    Appendix B case study (root cause + problematic code section).
    """

    ROLE_DESCRIPTION = (
        "You are the System 2 Reasoner in ORMind. You provide deliberate verification "
        "through counterfactual reasoning and syntax error analysis."
    )

    FORWARD_TASK = '''Analyze the following optimization problem:
{problem_description}

Task: Write a Python function that identifies which specific constraints or conditions in the given problem are not satisfied. This condition will need modification to achieve a valid and optimal solution.

Function specifications:
- Input arguments and their types: {input_content}
- Adhere to the given data types.
- Reference this code structure: {code_example}
- Import the necessary libraries.

Notes:
The code example is only for reference in terms of format and structure. Generate code specifically for the given problem, not based on any examples.
All specific constraints should be determined based on the problem description provided.
Make sure to include checks for all constraints mentioned in the problem description. Don't give any Example usages.'''

    BACKWARD_TASK = '''The generated optimization code failed to execute.
Previous code:
{previous_code}

Error message:
{feedback}

Please identify:
1. The likely root cause of the error.
2. The specific problematic code section.

Keep the answer concise and implementation-oriented.'''

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="System 2 Reasoner",
            description="Performs counterfactual verification and syntax error analysis.",
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def build_counterfactual_checker(self, problem, code_example: str, input_content: str) -> str:
        return self.forward_chain.invoke(
            {
                "problem_description": flatten_problem_description(problem["description"]),
                "code_example": code_example,
                "input_content": input_content,
            }
        ).content

    def diagnose_failure(self, previous_code: str, feedback: str) -> str:
        return self.invoke_backward(
            previous_code=previous_code,
            feedback=feedback,
        )


Reasoner = System2Reasoner
