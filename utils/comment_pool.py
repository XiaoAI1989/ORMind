from utils.comment import Comment


class CommentPool(object):
    """The shared memory pool P from the paper (Section 3.2).

    Each agent's output O_k is appended as a Comment, so that
    P_k = P_{k-1} U {O_k} and later agents can read the accumulated
    solution context. Entries carry the contributing agent's identifier
    and a creation timestamp (Appendix G); the metadata is for
    traceability only and never enters a prompt.
    """

    def __init__(self, all_experts):
        """A global data structure storing current comments.

        Args:
            all_experts: list of BaseExpert
        """
        self.comments = []
        self.all_experts = all_experts

    def add_comment(self, comment: Comment):
        self.comments.append(comment)

    def get_current_comment_text(self):
        comments_text = ''
        if len(self.comments) == 0:
            comments_text = 'There is no comment available, please ignore this section.\n'
        else:
            for comment in self.comments:
                comments_text += comment.expert.name + ': ```' + comment.comment_text + '```\n'
        return comments_text

    def get_closet_comment_text(self):
        """Render only the newest entry.

        This is the accessor shown in the paper's Appendix A trace
        (``feedback_pool.get_closet_comment_text()``); the released
        Algorithm 1 pipeline passes the counterfactual feedback string to
        the Supervisor directly, which carries the identical text without
        the ``Name: ```...````` wrapper. Kept for fidelity with the
        published listing. (Typo "closet" preserved from the paper.)
        """
        comments_text = ''
        if len(self.comments) == 0:
            comments_text = 'There is no comment available, please ignore this section.\n'
        else:
            comment = self.comments[-1]
            comments_text += comment.expert.name + ': ```' + comment.comment_text + '```\n'
        return comments_text

    def __len__(self):
        return len(self.comments)
