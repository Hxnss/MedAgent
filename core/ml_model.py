"""
core/ml_model.py
=================
Wrapper untuk model Random Forest MedAgent yang tersimpan di MedAgent_ModelML/.
Mengekspos get_model() dan PredictionResult yang dibutuhkan oleh core/agent.py.
"""

import os
import pickle
import joblib
from dataclasses import dataclass, field
from typing import List

# ── Path ke file model & fitur ────────────────────────────────────────────────
_MODEL_DIR    = os.path.join(os.path.dirname(__file__), "..", "models")
_MODEL_PATH   = os.path.join(_MODEL_DIR, "model_medagent.pkl")
_FEATURE_PATH = os.path.join(_MODEL_DIR, "fitur_gejala.pkl")


# ── Dataclass output ──────────────────────────────────────────────────────────

@dataclass
class DiseaseCandidate:
    name: str
    confidence_pct: str   # contoh: "87.5%"  — sudah include tanda %


@dataclass
class PredictionResult:
    top3: List[DiseaseCandidate]
    active_symptoms: List[str]
    n_active: int
    low_confidence: bool


# ── Model singleton ───────────────────────────────────────────────────────────

class MLModel:
    def __init__(self):
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"Model tidak ditemukan di: {_MODEL_PATH}\n"
                "Pastikan file model_medagent.pkl ada di folder models/"
            )
        if not os.path.exists(_FEATURE_PATH):
            raise FileNotFoundError(
                f"File fitur tidak ditemukan di: {_FEATURE_PATH}\n"
                "Pastikan file fitur_gejala.pkl ada di folder models/"
            )

        # Model disimpan dengan joblib (format sklearn standar)
        with open(_MODEL_PATH, "rb") as f:
            self._model = joblib.load(f)

        # File fitur disimpan dengan pickle biasa
        with open(_FEATURE_PATH, "rb") as f:
            self._features: list = pickle.load(f)

    def predict(self, symptom_dict: dict) -> PredictionResult:
        """
        Melakukan prediksi penyakit berdasarkan dict gejala aktif.

        Args:
            symptom_dict: Dict format {symptom_id: 1/0}

        Returns:
            PredictionResult dengan top3 penyakit beserta confidence score.
        """
        import numpy as np

        # Buat vektor fitur sesuai urutan kolom model
        feature_vector = [symptom_dict.get(feat, 0) for feat in self._features]
        X = [feature_vector]

        # Prediksi probabilitas
        proba = self._model.predict_proba(X)[0]
        classes = self._model.classes_

        # Ambil top-3 berdasarkan probabilitas tertinggi
        top_indices = sorted(range(len(proba)), key=lambda i: proba[i], reverse=True)[:3]

        top3 = [
            DiseaseCandidate(
                name=classes[i],
                confidence_pct=f"{proba[i] * 100:.1f}%"
            )
            for i in top_indices
        ]

        # Gejala yang aktif (nilai = 1)
        active_syms = [sym for sym, val in symptom_dict.items() if val == 1]

        # Low confidence jika penyakit teratas < 40%
        low_conf = bool(proba[top_indices[0]] < 0.40)

        return PredictionResult(
            top3=top3,
            active_symptoms=active_syms,
            n_active=len(active_syms),
            low_confidence=low_conf,
        )


_model_instance: MLModel = None


def get_model() -> MLModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = MLModel()
    return _model_instance


__all__ = ["get_model", "MLModel", "PredictionResult", "DiseaseCandidate"]
