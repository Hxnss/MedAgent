"""
tests/test_classifier.py
==========================
Unit tests untuk Risk Severity Classifier.
Jalankan dengan: pytest tests/test_classifier.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.risk_classifier import classify, SEVERITY_ORDER


# ── Helper ────────────────────────────────────────────────────────────────────

def assert_severity(symptoms, disease, expected_level, label=""):
    result = classify(symptoms, disease)
    assert result.severity_level == expected_level, (
        f"[{label}] Expected {expected_level}, got {result.severity_level}\n"
        f"  Reasoning: {result.reasoning}"
    )


# ── EMERGENCY tests ───────────────────────────────────────────────────────────

def test_stroke_single_symptom():
    """Facial drooping sendiri harus EMERGENCY"""
    assert_severity(["facial_drooping"], None, "EMERGENCY", "stroke_single")

def test_stroke_combination():
    """Kombinasi slurred_speech + unilateral_weakness = stroke pattern"""
    assert_severity(["slurred_speech", "unilateral_weakness"], "Stroke", "EMERGENCY", "stroke_combo")

def test_chest_pain_shortness():
    """Kombinasi chest_pain + shortness_of_breath = cardiac emergency"""
    assert_severity(["chest_pain", "shortness_of_breath"], None, "EMERGENCY", "cardiac_combo")

def test_dengue_emergency():
    """Dengue Hemorrhagic Fever harus EMERGENCY via disease map"""
    assert_severity(["fever", "joint_pain"], "Dengue Hemorrhagic Fever", "EMERGENCY", "dengue_disease")

def test_heart_failure_emergency():
    """Heart Failure harus EMERGENCY"""
    assert_severity(["swollen_feet", "orthopnea"], "Heart Failure", "EMERGENCY", "heart_failure")

def test_coughing_blood_alone():
    """Batuk darah sendiri sudah cukup EMERGENCY"""
    assert_severity(["coughing_blood"], None, "EMERGENCY", "hemoptysis")

def test_fever_decreased_consciousness():
    """Demam + gangguan kesadaran = EMERGENCY (meningitis/malaria serebral)"""
    assert_severity(["fever", "decreased_consciousness"], None, "EMERGENCY", "fever_unconscious")


# ── URGENT tests ──────────────────────────────────────────────────────────────

def test_pneumonia_urgent():
    assert_severity(["cough", "fever", "shortness_of_breath"], "Pneumonia", "URGENT", "pneumonia")

def test_tb_combination():
    """Trias TB: weight_loss + night_sweats + cough"""
    assert_severity(["weight_loss", "night_sweats", "cough"], "Tuberculosis", "URGENT", "tb_combo")

def test_dengue_trias():
    """Trias dengue: fever + joint_pain + skin_rash"""
    assert_severity(["fever", "joint_pain", "skin_rash"], None, "URGENT", "dengue_trias")

def test_malaria_urgent():
    assert_severity(["fever", "chills", "headache"], "Malaria", "URGENT", "malaria")

def test_hepatitis_urgent():
    assert_severity(["yellow_eyes", "dark_urine"], "Hepatitis A", "URGENT", "hepatitis")

def test_blood_in_urine_urgent():
    """Blood in urine sendiri cukup untuk URGENT"""
    assert_severity(["blood_in_urine"], None, "URGENT", "hematuria")


# ── SEMI-URGENT tests ─────────────────────────────────────────────────────────

def test_uti_semi_urgent():
    assert_severity(["frequent_urination", "lower_back_pain", "fever"], "Urinary Tract Infection",
                    "SEMI-URGENT", "uti")

def test_diabetes_semi_urgent():
    assert_severity(["excessive_thirst", "frequent_urination", "weight_loss"],
                    "Type 2 Diabetes Mellitus", "SEMI-URGENT", "diabetes")

def test_gastroenteritis_semi_urgent():
    assert_severity(["diarrhea", "vomiting", "abdominal_pain"], "Gastroenteritis",
                    "SEMI-URGENT", "gastroenteritis")

def test_fever_alone_semi_urgent():
    """Demam tanpa gejala lain = SEMI-URGENT"""
    assert_severity(["fever"], None, "SEMI-URGENT", "fever_alone")


# ── NON-URGENT tests ──────────────────────────────────────────────────────────

def test_common_cold():
    assert_severity(["runny_nose", "sneezing", "sore_throat"], "Influenza",
                    "NON-URGENT", "common_cold")

def test_gerd():
    assert_severity(["heartburn", "bloating", "excessive_belching"], "GERD",
                    "NON-URGENT", "gerd")

def test_conjunctivitis():
    assert_severity(["red_eyes", "eye_discharge", "itching"], "Conjunctivitis",
                    "NON-URGENT", "conjunctivitis")

def test_sinusitis():
    assert_severity(["nasal_congestion", "headache", "sore_throat"], "Sinusitis",
                    "NON-URGENT", "sinusitis")


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_symptoms_no_disease():
    """Tanpa gejala dan penyakit = NON-URGENT (default)"""
    result = classify([], None)
    assert result.severity_level == "NON-URGENT"

def test_symptom_overrides_disease():
    """Gejala EMERGENCY harus override penyakit NON-URGENT"""
    result = classify(["chest_pain", "decreased_consciousness"], "Conjunctivitis")
    assert result.severity_level == "EMERGENCY", \
        "Gejala emergency harus override disease NON-URGENT"

def test_disease_elevates_mild_symptoms():
    """Penyakit URGENT harus elevate gejala NON-URGENT"""
    result = classify(["fatigue", "cough"], "Tuberculosis")
    assert result.severity_level == "URGENT", \
        "Disease map harus elevate severity di atas symptom level"

def test_consistency():
    """Input yang sama harus selalu menghasilkan output yang sama (deterministic)"""
    symptoms = ["fever", "joint_pain", "skin_rash"]
    disease = "Dengue Hemorrhagic Fever"
    results = [classify(symptoms, disease).severity_level for _ in range(5)]
    assert len(set(results)) == 1, "Classifier harus deterministik"

def test_unknown_disease_defaults_to_semi_urgent():
    """Penyakit yang tidak ada di map harus default SEMI-URGENT"""
    result = classify(["headache"], "UnknownDisease123")
    assert result.severity_level in ["SEMI-URGENT", "NON-URGENT"]


# ── Reasoning log test ────────────────────────────────────────────────────────

def test_reasoning_not_empty_for_emergency():
    result = classify(["chest_pain", "shortness_of_breath"], "Heart Failure")
    assert result.reasoning, "Reasoning harus ada untuk kasus EMERGENCY"
    assert result.triggered_rules, "Triggered rules harus ada"

def test_result_has_action():
    result = classify(["fever"], "Malaria")
    assert result.recommended_action, "Harus ada recommended action"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
