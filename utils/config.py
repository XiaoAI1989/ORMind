import os
from typing import Dict, Optional


# Paper configuration (Section 5.2 / Appendix E): GPT-3.5-turbo on the
# OpenAI API. A fresh clone with no env.local therefore runs the published
# backbone, not a substitute model.
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_PRIMARY_MODEL = "gpt-3.5-turbo"


def load_env_file(path: str = "env.local") -> Dict[str, str]:
    loaded = {}
    if not os.path.exists(path):
        return loaded

    with open(path, "r", encoding="utf8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            os.environ.setdefault(key, value)
            loaded[key] = value
    return loaded


def resolve_runtime_config(
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    load_env_file()

    resolved_model = (
        model
        or os.getenv("ORMIND_MODEL")
        or os.getenv("OPENROUTER_MODEL")
        or DEFAULT_PRIMARY_MODEL
    )
    resolved_base_url = (
        base_url
        or os.getenv("OPENROUTER_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or DEFAULT_BASE_URL
    )
    resolved_api_key = (
        api_key
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )

    # The fallback is strictly opt-in: silently mixing a second model into a
    # benchmark run would make the numbers unattributable. When enabled via
    # ORMIND_FALLBACK_MODEL, every fallback completion is logged by the LLM
    # client and counted in the per-problem usage stats.
    return {
        "model": resolved_model,
        "base_url": resolved_base_url,
        "api_key": resolved_api_key,
        "fallback_model": os.getenv("ORMIND_FALLBACK_MODEL") or None,
    }
