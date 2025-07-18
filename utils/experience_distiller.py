import json
import os
import re
import time
from typing import Any, Dict, List


class ExperienceDistiller:
    """Store and retrieve compact experience traces."""

    def __init__(self, path: str) -> None:
        self.path = path

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z_]+", text.lower())

    def _load(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        rows = []
        with open(self.path, "r", encoding="utf8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def _strategy_tags(self, semantic_schema: str, candidate_summaries: List[Dict[str, Any]]) -> List[str]:
        tags = []
        lower_schema = semantic_schema.lower()
        if "capacity" in lower_schema or "resource" in lower_schema:
            tags.append("resource_allocation")
        if "flow" in lower_schema or "routing" in lower_schema:
            tags.append("network_flow")
        if "time" in lower_schema or "schedule" in lower_schema:
            tags.append("temporal_reasoning")
        if any(item.get("static_valid", False) for item in candidate_summaries):
            tags.append("syntax_safe")
        if any("verification" in item.get("style", "") for item in candidate_summaries):
            tags.append("verification_aware")
        return tags[:6]

    def retrieve(self, problem_text: str, problem_family: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = set(self._tokenize(problem_text))
        scored = []
        for record in self._load():
            overlap = len(query_tokens & set(record.get("tokens", [])))
            family_bonus = 0.75 if problem_family and record.get("problem_family") == problem_family else 0.0
            if overlap or family_bonus:
                score = overlap + family_bonus + 0.5 * float(record.get("accepted", False))
                scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:top_k]]

    def format_notes(self, records: List[Dict[str, Any]]) -> str:
        if not records:
            return "No prior distilled experience."
        blocks = []
        for index, record in enumerate(records, start=1):
            lines = [
                f"Memory {index} | accepted={record.get('accepted', False)} | family={record.get('problem_family', 'unknown')}",
                f"Strategy tags: {', '.join(record.get('strategy_tags', [])) or 'none'}",
                *[f"- {lesson}" for lesson in record.get("lessons", [])[:6]],
            ]
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    def record(
        self,
        problem_name: str,
        problem_text: str,
        problem_family: str,
        semantic_schema: str,
        formalizations: List[str],
        candidate_summaries: List[Dict[str, Any]],
        accepted: bool,
        lessons: List[str],
    ) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        row = {
            "problem_name": problem_name,
            "timestamp": int(time.time()),
            "tokens": self._tokenize(problem_text),
            "problem_family": problem_family,
            "semantic_schema": semantic_schema[:2500],
            "formalizations": formalizations[:2],
            "candidate_summaries": candidate_summaries[:4],
            "accepted": accepted,
            "lessons": lessons[:10],
            "strategy_tags": self._strategy_tags(semantic_schema, candidate_summaries),
        }
        with open(self.path, "a", encoding="utf8") as handle:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
