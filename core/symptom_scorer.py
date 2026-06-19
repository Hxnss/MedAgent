"""
core/symptom_scorer.py
=======================
Modul untuk menilai kualitas (spesifisitas) input gejala dari pengguna.
Mengekspos score_symptoms() dan SpecificityResult yang dibutuhkan oleh core/agent.py.
"""

from dataclasses import dataclass

# ── Gejala yang dianggap "spesifik" (membedakan penyakit dengan baik) ─────────
# Gejala generik seperti headache/fatigue mendapat bobot rendah.
# Gejala spesifik seperti chest_pain/seizures mendapat bobot tinggi.

HIGHLY_SPECIFIC = {
    "chest_pain", "decreased_consciousness", "seizures", "slurred_speech",
    "facial_drooping", "unilateral_weakness", "coughing_blood",
    "blood_in_urine", "bloody_stool", "yellow_eyes", "yellowish_skin",
    "pain_behind_eyes", "orthopnea", "shortness_of_breath",
    "rapid_breathing", "palpitations", "cold_feet",
}

SEMI_SPECIFIC = {
    "vomiting", "diarrhea", "abdominal_pain", "lower_back_pain",
    "swelling", "swollen_feet", "dark_urine", "cloudy_urine",
    "red_spots_on_skin", "skin_rash", "joint_pain", "night_sweats",
    "weight_loss", "excessive_thirst", "frequent_urination", "fever",
}

# Semua lainnya dianggap NON_SPECIFIC (headache, fatigue, chills, dst.)


# ── Dataclass output ──────────────────────────────────────────────────────────

@dataclass
class SpecificityResult:
    score: int           # 0–100
    score_label: str     # "Sangat Baik" / "Baik" / "Cukup" / "Kurang"
    n_active: int        # total gejala aktif
    n_specific: int      # gejala yang spesifik (highly + semi)
    warning: bool        # True jika kualitas input kurang
    warning_message: str


# ── Fungsi utama ──────────────────────────────────────────────────────────────

def score_symptoms(symptom_dict: dict) -> SpecificityResult:
    """
    Menilai kualitas input gejala berdasarkan spesifisitasnya.

    Args:
        symptom_dict: Dict {symptom_id: 1/0}

    Returns:
        SpecificityResult dengan skor 0-100 dan label kualitas.
    """
    active = [sym for sym, val in symptom_dict.items() if val == 1]
    n_active = len(active)

    if n_active == 0:
        return SpecificityResult(
            score=0, score_label="Tidak Ada Gejala",
            n_active=0, n_specific=0,
            warning=True,
            warning_message="Tidak ada gejala yang dipilih."
        )

    # Hitung bobot: highly_specific = 2 poin, semi_specific = 1 poin, lainnya = 0
    raw_score = sum(
        2 if sym in HIGHLY_SPECIFIC else (1 if sym in SEMI_SPECIFIC else 0)
        for sym in active
    )

    # Normalisasi ke 0-100 (maks teoritis: semua gejala highly specific)
    max_possible = 2 * n_active
    normalized = int((raw_score / max_possible) * 100) if max_possible > 0 else 0

    # Label
    if normalized >= 70:
        label = "Sangat Baik"
        warn = False
        msg = ""
    elif normalized >= 40:
        label = "Baik"
        warn = False
        msg = ""
    elif normalized >= 20:
        label = "Cukup"
        warn = True
        msg = "Gejala yang dipilih cukup umum. Tambahkan gejala yang lebih spesifik jika ada."
    else:
        label = "Kurang Spesifik"
        warn = True
        msg = "Gejala yang dipilih sangat umum. Prediksi mungkin kurang akurat."

    # Hitung jumlah gejala spesifik (untuk laporan)
    n_specific = sum(1 for sym in active if sym in HIGHLY_SPECIFIC or sym in SEMI_SPECIFIC)

    return SpecificityResult(
        score=normalized,
        score_label=label,
        n_active=n_active,
        n_specific=n_specific,
        warning=warn,
        warning_message=msg,
    )


__all__ = ["score_symptoms", "SpecificityResult"]
