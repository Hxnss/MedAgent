"""
core/risk_classifier.py
========================
Rule-Enhanced Risk Severity Classifier untuk MedAgent.

Mengklasifikasikan tingkat urgensi kondisi pasien menjadi 4 level:
  EMERGENCY  → Segera ke IGD
  URGENT     → Ke dokter hari ini
  SEMI-URGENT → Ke dokter 1-2 hari
  NON-URGENT → Bisa ditangani mandiri / konsultasi tidak mendesak

Logika ini sepenuhnya deterministik (rule-based), bukan probabilistik.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional

# ── Load rule files ──────────────────────────────────────────────────────────
_RULES_DIR = os.path.join(os.path.dirname(__file__), "rules")

with open(os.path.join(_RULES_DIR, "disease_severity_map.json"), encoding="utf-8") as f:
    DISEASE_MAP: dict = json.load(f)

with open(os.path.join(_RULES_DIR, "symptom_rules.json"), encoding="utf-8") as f:
    SYMPTOM_RULES: dict = json.load(f)

# ── Severity ordering ─────────────────────────────────────────────────────────
SEVERITY_ORDER = ["EMERGENCY", "URGENT", "SEMI-URGENT", "NON-URGENT"]

SEVERITY_ACTIONS = {
    "EMERGENCY":   "🔴 Segera ke IGD / unit gawat darurat terdekat. Jangan tunda.",
    "URGENT":      "🟠 Kunjungi dokter atau puskesmas hari ini.",
    "SEMI-URGENT": "🟡 Konsultasikan ke dokter dalam 1-2 hari ke depan.",
    "NON-URGENT":  "🟢 Bisa ditangani mandiri. Konsultasi dokter jika tidak membaik dalam 3-5 hari.",
}


@dataclass
class SeverityResult:
    severity_level: str
    source: str                        # "symptom_single" / "symptom_combo" / "disease_map" / "default"
    triggered_rules: list[str] = field(default_factory=list)
    reasoning: str = ""
    recommended_action: str = ""
    disease_rationale: Optional[str] = None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _higher(a: str, b: str) -> str:
    """Return whichever severity is higher (more urgent)."""
    return a if SEVERITY_ORDER.index(a) <= SEVERITY_ORDER.index(b) else b


def _classify_by_symptoms(symptoms: list[str]) -> tuple[str, list[str], str]:
    """
    Returns (severity_level, triggered_rules, source).
    Checks in priority order: EMERGENCY combos → EMERGENCY singles →
    URGENT combos → URGENT singles → SEMI-URGENT → NON-URGENT.
    """
    symptom_set = set(symptoms)
    best_level = "NON-URGENT"
    triggered = []
    source = "symptom_single"

    for level in ["EMERGENCY", "URGENT"]:
        level_rules = SYMPTOM_RULES.get(level, {})

        # Check combinations first (higher signal)
        for combo in level_rules.get("combinations", []):
            required = set(combo["symptoms"])
            if required.issubset(symptom_set):
                rule_label = f"COMBO {level}: {' + '.join(combo['symptoms'])} → {combo['rationale']}"
                triggered.append(rule_label)
                best_level = _higher(best_level, level)
                source = "symptom_combo"

        # Check individual red-flag symptoms
        for sym in level_rules.get("symptoms", []):
            if sym in symptom_set:
                triggered.append(f"SINGLE {level}: {sym}")
                best_level = _higher(best_level, level)

    # If still NON-URGENT, check SEMI-URGENT singles
    if best_level == "NON-URGENT":
        for sym in SYMPTOM_RULES.get("SEMI-URGENT", {}).get("symptoms", []):
            if sym in symptom_set:
                triggered.append(f"SINGLE SEMI-URGENT: {sym}")
                best_level = "SEMI-URGENT"
                break  # one match is enough to elevate to SEMI-URGENT

    return best_level, triggered, source


def _classify_by_disease(disease: str) -> tuple[str, str]:
    """Returns (severity_level, rationale) from disease map. Defaults to SEMI-URGENT."""
    entry = DISEASE_MAP.get(disease)
    if entry:
        return entry["severity"], entry.get("rationale", "")
    return "SEMI-URGENT", "Penyakit tidak ditemukan dalam peta risiko; menggunakan default SEMI-URGENT."


# ── Public API ────────────────────────────────────────────────────────────────

def classify(
    symptoms: list[str],
    predicted_disease: Optional[str] = None,
) -> SeverityResult:
    """
    Klasifikasi utama. Menggabungkan sinyal gejala dan penyakit prediktif.

    Args:
        symptoms:          List gejala dari input user (nama kolom dataset).
        predicted_disease: Nama penyakit dari model Random Forest (opsional).

    Returns:
        SeverityResult dengan level final, reasoning, dan rekomendasi aksi.
    """
    # 1. Symptom-based classification
    sym_level, sym_rules, sym_source = _classify_by_symptoms(symptoms)

    # 2. Disease-based classification (jika tersedia)
    dis_level, dis_rationale = _classify_by_disease(predicted_disease) if predicted_disease else ("NON-URGENT", "")

    # 3. Ambil level tertinggi (paling urgent) dari kedua sumber
    final_level = _higher(sym_level, dis_level)

    # 4. Tentukan sumber utama keputusan
    if SEVERITY_ORDER.index(sym_level) <= SEVERITY_ORDER.index(dis_level):
        primary_source = sym_source
    else:
        primary_source = "disease_map"

    # 5. Bangun reasoning yang bisa diaudit
    reasoning_parts = []
    if sym_rules:
        reasoning_parts.append(f"Gejala memicu aturan: {'; '.join(sym_rules)}")
    if predicted_disease:
        reasoning_parts.append(
            f"Penyakit prediktif '{predicted_disease}' memiliki tingkat risiko {dis_level}"
            + (f": {dis_rationale}" if dis_rationale else "")
        )
    if not reasoning_parts:
        reasoning_parts.append("Tidak ada gejala red-flag yang terdeteksi. Menggunakan level default.")

    # Ambil recommended_action dari disease map jika ada, fallback ke tabel umum
    disease_entry = DISEASE_MAP.get(predicted_disease, {}) if predicted_disease else {}
    specific_action = disease_entry.get("action", "")
    final_action = specific_action if specific_action else SEVERITY_ACTIONS[final_level]

    return SeverityResult(
        severity_level=final_level,
        source=primary_source,
        triggered_rules=sym_rules,
        reasoning=" | ".join(reasoning_parts),
        recommended_action=final_action,
        disease_rationale=dis_rationale or None,
    )


def classify_risk(predicted_disease: str, symptom_dict: dict) -> SeverityResult:
    """
    Mengklasifikasikan tingkat urgensi berdasarkan penyakit prediktif dan gejala aktif.

    Args:
        predicted_disease : Nama penyakit hasil prediksi model ML (top-1).
        symptom_dict      : Dict format {symptom_id: 1} dari input user.

    Returns:
        SeverityResult
    """
    active_symptoms = [sym for sym, val in symptom_dict.items() if val == 1]
    return classify(symptoms=active_symptoms, predicted_disease=predicted_disease)


# Re-export agar core/agent.py bisa import dari sini
__all__ = ["classify_risk", "classify", "SeverityResult", "SEVERITY_ORDER"]
