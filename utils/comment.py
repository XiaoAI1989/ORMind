import time


class Comment(object):
    """One memory-pool entry O_k.

    Per Appendix G of the paper, every update to the memory pool is tagged
    with the contributing agent's identifier and a timestamp for
    traceability. The identifier lives in ``expert.name``; ``created_at``
    is a Unix timestamp recorded when the comment is created. Neither field
    is ever rendered into prompts (see CommentPool.get_current_comment_text),
    so this metadata cannot change model behaviour.
    """

    def __init__(self, expert, comment_text, created_at=None):
        self.expert = expert
        self.comment_text = comment_text
        self.created_at = time.time() if created_at is None else created_at
