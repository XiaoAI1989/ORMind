from agent_team.base_expert import BaseExpert
from utils.utils import flatten_problem_description


class CodeReviewer(BaseExpert):
    """Ablation module for the "w/ Code Reviewer" row of Table 2.

    The prompt template is the Appendix C version, kept verbatim.
    """

    ROLE_DESCRIPTION = 'You are a code reviewer that conducts thorough reviews of the implemented code to identify any errors, inefficiencies, or areas for improvement.'
    FORWARD_TASK = '''As a Code Reviewer, your responsibility is to conduct thorough reviews of implemented code related to optimization problems.
You will identify possible errors, inefficiencies, or areas for improvement in the code, ensuring that it adheres to best practices and delivers optimal results. Now, here is the problem:
{problem_description}.

You are supposed to refer to the codes given by your colleagues from other aspects: {comments_text}'''

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name='Code Reviewer',
            description='Skilled in programming and coding, reviews the implemented optimization code.',
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
                "problem_description": flatten_problem_description(problem['description']),
                "comments_text": comment_pool.get_current_comment_text(),
            }
        ).content
