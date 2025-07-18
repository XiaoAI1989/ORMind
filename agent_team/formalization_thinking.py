from agent_team.base_expert import BaseExpert
from utils.utils import flatten_problem_description


class FormalizationThinking(BaseExpert):
    """Type 1 processing: constructs the mathematical model.

    The forward task below is the prompt template published in Appendix C
    of the paper, kept verbatim.
    """

    ROLE_DESCRIPTION = (
        "You are the Formalization Thinking module in ORMind. You execute deep analytical "
        "thinking to construct mathematical models: defining variables, formulating "
        "constraints, and constructing the objective function."
    )

    FORWARD_TASK = '''Now the origin problem is as follows:
{problem_description}
You can use the parameters information from your colleague:
{comments_text}
The order of given parameters is random. You should clarify the meaning of each parameter to choose proper parameter to construct constraint.
Give your Mathematical model of this problem.
Your output format should be a JSON like this:
{{
    "VARIABLES": "A concise description about variables and its shape or type",
    "CONSTRAINTS": "A mathematical Formula about constraints",
    "OBJECTIVE": "A mathematical Formula about objective"
}}
Don't give any other information.'''

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="Formalization Thinking",
            description="Builds the mathematical model: variables, constraints, and objective.",
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def forward(self, problem, comment_pool):
        return self.forward_chain.invoke(
            {
                "problem_description": flatten_problem_description(problem["description"]),
                "comments_text": comment_pool.get_current_comment_text(),
            }
        ).content


ModelingExpert = FormalizationThinking
