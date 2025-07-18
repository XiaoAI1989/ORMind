import json

from agent_team.base_expert import BaseExpert
from utils.utils import clean_markdown_block, flatten_problem_description


class TerminologyInterpreter(BaseExpert):
    """Ablation module for the "w/ Terminology Interpreter" row of Table 2.

    The prompt template is the Appendix C version, kept verbatim.
    """

    ROLE_DESCRIPTION = 'You are a terminology interpreter who provides additional domain-specific knowledge to enhance problem understanding and formulation.'
    FORWARD_TASK = '''As a domain knowledge terminology interpreter, your role is to provide additional information and insights related to the problem domain.
Here are some relevant background knowledge about this problem: {knowledge}.

You can contribute by sharing your expertise, explaining relevant concepts, and offering suggestions to improve the problem understanding and formulation.
Please provide your input based on the given problem description:
{problem_description}

Your output format should be a JSON like this (choose at most 3 hardest terminology. Please provide your output, ensuring there is no additional text or formatting markers like ```json. The output should be in plain JSON format, directly parsable by json.loads(output).):
[
  {{
    "terminology": "...",
    "interpretation": "..."
  }}
]
'''

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name='Terminology Interpreter',
            description='Provides additional domain-specific knowledge to enhance problem understanding and formulation.',
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def forward(self, problem, comment_pool):
        del comment_pool
        output = self.forward_chain.invoke({
            "problem_description": flatten_problem_description(problem['description']),
            "knowledge": 'None'
        }).content
        try:
            items = json.loads(clean_markdown_block(output))
            answer = '\n'.join(
                f"{item['terminology']}: {item['interpretation']}" for item in items
            )
            return answer.strip()
        except Exception:
            return output.strip()
