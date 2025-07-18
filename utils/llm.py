import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional

from openai import OpenAI

try:
    from openai import BadRequestError
except ImportError:  # very old SDKs
    BadRequestError = Exception


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""


class UsageTracker:
    """Accumulates token usage across all agent calls for one problem.

    The per-problem totals are written into the experiment logs as
    "Prompt Tokens: N" so that data_process/count_token.py can reproduce
    the prompt-length statistics reported in the paper (Table 4).
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.llm_calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        # model name -> completions served by it; more than one key means a
        # fallback model answered part of the run, so the per-problem stats
        # make any model mixing visible instead of silent.
        self.calls_by_model: Dict[str, int] = {}

    def add(self, response: "LLMResponse") -> None:
        self.llm_calls += 1
        self.prompt_tokens += response.prompt_tokens
        self.completion_tokens += response.completion_tokens
        if response.model:
            self.calls_by_model[response.model] = self.calls_by_model.get(response.model, 0) + 1

    def snapshot(self) -> Dict[str, Any]:
        return {
            "llm_calls": self.llm_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "calls_by_model": dict(self.calls_by_model),
        }


class OpenAICompatibleLLM:
    def __init__(
        self,
        model_name: str,
        temperature: float = 0,
        openai_api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 2,
        fallback_model: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        usage_tracker: Optional[UsageTracker] = None,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.fallback_model = fallback_model
        self.usage_tracker = usage_tracker
        # "EMPTY" is the conventional placeholder for OpenAI-compatible
        # endpoints; a genuinely missing key fails at request time with a
        # clear authentication error instead of at client construction.
        self.client = OpenAI(
            api_key=api_key or "EMPTY",
            base_url=openai_api_base,
            max_retries=max_retries,
            default_headers=extra_headers,
        )

    def _request(self, model: str, prompt: str) -> Any:
        messages = [{"role": "user", "content": prompt}]
        try:
            return self.client.chat.completions.create(
                model=model,
                temperature=self.temperature,
                messages=messages,
            )
        except BadRequestError as exc:
            # Some models only accept their default temperature.
            if "temperature" in str(exc):
                return self.client.chat.completions.create(model=model, messages=messages)
            raise

    def invoke(self, prompt: str) -> LLMResponse:
        try:
            response = self._request(self.model_name, prompt)
        except Exception as exc:
            if not self.fallback_model or self.fallback_model == self.model_name:
                raise
            # Opt-in fallback (ORMIND_FALLBACK_MODEL). Never silent: mixing a
            # second model into a benchmark run must be visible in the console
            # and in the per-problem calls_by_model stats.
            print(
                f"[ormind] WARNING: primary model '{self.model_name}' failed "
                f"({type(exc).__name__}); retrying with fallback '{self.fallback_model}'.",
                file=sys.stderr,
            )
            response = self._request(self.fallback_model, prompt)

        usage = getattr(response, "usage", None)
        result = LLMResponse(
            content=response.choices[0].message.content or "",
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            model=getattr(response, "model", "") or self.model_name,
        )
        if self.usage_tracker is not None:
            self.usage_tracker.add(result)
        return result


class StringTemplateChain:
    def __init__(self, template: str, llm: OpenAICompatibleLLM) -> None:
        self.template = template
        self.llm = llm

    def invoke(self, kwargs: Dict[str, Any]) -> LLMResponse:
        prompt = self.template.format(**kwargs)
        return self.llm.invoke(prompt)
