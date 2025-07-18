from agent_team.base_expert import BaseExpert
from utils.utils import flatten_problem_description


class Conductor(BaseExpert):
    """Ablation module for the "w/ Conductor" row of Table 2.

    When enabled, the Conductor dynamically chooses the next thinking
    expert to consult instead of following the fixed Algorithm 1 order.
    The prompt template is the Appendix C version, kept verbatim.
    """

    ROLE_DESCRIPTION = '''you will take on the role of the conductor for a multi-expert system.'''
    FORWARD_TASK = '''Now, you are presented with an operational optimization-related problem:
{problem_description}

In this multi-expert system, there are many agent_team, each of whom is responsible for solving part of the problem.
Your task is to CHOOSE THE NEXT EXPERT TO CONSULT.

The names of the agent_team and their capabilities are listed below:
{experts_info}

Experts that have already been commented include:
{commented_experts}

Please select an expert to consult from the remaining expert names {remaining_experts}.

Please note that the maximum number of asked agent_team is {max_collaborate_nums}, and you can ask {remaining_collaborate_nums} more times.

You should output the name of expert directly. The next expert is:'''

    def __init__(self, model, temperature=0, base_url=None, api_key=None, fallback_model=None, usage_tracker=None):
        super().__init__(
            name='Conductor',
            description='A special expert that coordinates all other agent_team.',
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )

    def forward(self, problem, comment_pool, max_collaborate_nums):
        all_experts = comment_pool.all_experts
        commented_experts_name = [c.expert.name for c in comment_pool.comments]
        remaining = [e for e in all_experts if e.name not in commented_experts_name]
        if not remaining or len(commented_experts_name) >= max_collaborate_nums:
            return None

        experts_info = '\n'.join([str(e) for e in all_experts])
        answer = self.forward_chain.invoke({
            "problem_description": flatten_problem_description(problem['description']),
            "experts_info": experts_info,
            "commented_experts": str(commented_experts_name),
            "remaining_experts": str([e.name for e in remaining]),
            "max_collaborate_nums": max_collaborate_nums,
            "remaining_collaborate_nums": max_collaborate_nums - len(commented_experts_name)
        }).content

        for expert in remaining:
            if expert.name in answer:
                return expert
        # The LLM named no remaining expert. Fall back to the first one in
        # the fixed Algorithm 1 order; deterministic so that "w/ Conductor"
        # ablation runs are reproducible at temperature 0 (an unseeded
        # random.choice here would inject run-to-run variance).
        return remaining[0]
