from typing import Any, Optional

from utils.llm import OpenAICompatibleLLM, StringTemplateChain, UsageTracker


class BaseExpert:
    ROLE_DESCRIPTION = ""
    FORWARD_TASK = ""

    def __init__(
        self,
        name: str,
        description: str,
        model: str,
        temperature: float = 0,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        fallback_model: Optional[str] = None,
        usage_tracker: Optional[UsageTracker] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.model = model
        self.llm = OpenAICompatibleLLM(
            model_name=model,
            temperature=temperature,
            openai_api_base=base_url,
            api_key=api_key,
            max_retries=2,
            fallback_model=fallback_model,
            usage_tracker=usage_tracker,
        )
        self.forward_chain = StringTemplateChain(
            self.ROLE_DESCRIPTION + "\n" + self.FORWARD_TASK,
            self.llm,
        )

        if hasattr(self, "BACKWARD_TASK"):
            self.backward_chain = StringTemplateChain(
                self.ROLE_DESCRIPTION + "\n" + self.BACKWARD_TASK,
                self.llm,
            )

    def invoke_forward(self, **kwargs: Any) -> str:
        return self.forward_chain.invoke(kwargs).content

    def invoke_backward(self, **kwargs: Any) -> str:
        if not hasattr(self, "backward_chain"):
            raise NotImplementedError("Backward method not implemented for this expert.")
        return self.backward_chain.invoke(kwargs).content

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"
