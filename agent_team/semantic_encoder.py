from agent_team.base_expert import BaseExpert
from utils.utils import flatten_problem_description


class SemanticEncoder(BaseExpert):
    """Type 1 (intuitive) processing: parameter recognition and typing.

    The forward task below is the prompt template published in Appendix C
    of the paper, kept verbatim.
    """

    ROLE_DESCRIPTION = (
        "You are the Semantic Encoder in ORMind. You transform unstructured problem text "
        "into structured knowledge representations, recognizing and categorizing parameters "
        "to reduce the working memory load of your colleagues."
    )
    FORWARD_TASK = '''Please review the following example and extract the parameters along with their concise definitions:
{problem_example}
The comment from your colleague is:
{comment_text}
Your output should be in JSON format as follows:
{{
    "Parameter1": {{"Type": "The parameter's data type or shape", "Definition": "A brief definition of the parameter"}},
    "Parameter2": {{"Type": "The parameter's data type or shape", "Definition": "A brief definition of the parameter"}},
    ...
}}
Provide only the requested JSON output without any additional information.'''

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name="Semantic Encoder",
            description="Extracts typed parameters and their definitions from the problem text.",
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
                "problem_example": flatten_problem_description(problem["description"]),
                "comment_text": comment_pool.get_current_comment_text(),
            }
        ).content
