import json
import math
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


@dataclass
class PreferencePrediction:
    score: float
    uncertainty: float
    features: Dict[str, float]


class OnlinePreferenceModel:
    """Online ranker for candidate programs."""

    def __init__(self, model_path: str, learning_rate: float = 0.08) -> None:
        self.model_path = model_path
        self.learning_rate = learning_rate
        self.weights = self._load_weights()

    def _load_weights(self) -> Dict[str, float]:
        if not os.path.exists(self.model_path):
            return {}
        try:
            with open(self.model_path, "r", encoding="utf8") as handle:
                payload = json.load(handle)
            return {key: float(value) for key, value in payload.get("weights", {}).items()}
        except Exception:
            return {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "w", encoding="utf8") as handle:
            json.dump({"weights": self.weights}, handle, ensure_ascii=True, indent=2)

    def predict(self, features: Dict[str, float]) -> PreferencePrediction:
        logit = 0.0
        for key, value in features.items():
            logit += self.weights.get(key, 0.0) * value
        probability = sigmoid(logit)
        uncertainty = 1.0 - abs(probability - 0.5) * 2.0
        return PreferencePrediction(
            score=probability,
            uncertainty=uncertainty,
            features=features,
        )

    def score_candidate(self, features: Dict[str, float], exploration_weight: float = 0.0) -> PreferencePrediction:
        prediction = self.predict(features)
        adjusted_score = prediction.score + exploration_weight * prediction.uncertainty
        return PreferencePrediction(
            score=adjusted_score,
            uncertainty=prediction.uncertainty,
            features=prediction.features,
        )

    def update(self, features: Dict[str, float], label: int) -> None:
        prediction = self.predict(features).score
        error = float(label) - prediction
        for key, value in features.items():
            self.weights[key] = self.weights.get(key, 0.0) + self.learning_rate * error * value
        self._save()

    def update_preference_pair(
        self,
        positive_features: Dict[str, float],
        negative_features: Dict[str, float],
    ) -> None:
        self.update(positive_features, 1)
        self.update(negative_features, 0)

    def batch_update(self, examples: Iterable[Dict[str, object]]) -> None:
        changed = False
        for example in examples:
            self.update(example["features"], int(example["label"]))
            changed = True
        if changed:
            self._save()
