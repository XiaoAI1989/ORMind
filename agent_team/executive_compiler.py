from agent_team.base_expert import BaseExpert
from utils.utils import flatten_problem_description


class ExecutiveCompiler(BaseExpert):
    """Operationalization: turns the abstract model into executable code.

    The forward task below is the prompt template published in Appendix C
    of the paper, kept verbatim.
    """

    ROLE_DESCRIPTION = (
        "You are the Executive Compiler in ORMind. You transform abstract mathematical "
        "models into executable code snippets with precise operational details."
    )
    FORWARD_TASK = '''You are presented with a specific problem and tasked with developing an efficient Python program to solve it.
The original problem is as follows:
{problem_description}
Your colleague has constructed a mathematical model for reference:
{comments_text}
Please note that this model may contain errors and is used as a reference.
You can analyze the problem step by step and provide your own code.
Requirements:
1. Use the PuLP library for implementation.
2. Provide a function that solves the problem.
3. Do not include code usage examples or specific variable values.
4. Focus on creating a general, reusable solution.'''

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="Executive Compiler",
            description="Generates executable PuLP solver code from the formalized model.",
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


Compiler = ExecutiveCompiler
