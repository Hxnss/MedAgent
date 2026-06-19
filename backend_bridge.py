# backend_bridge.py
# =============================================================
# PENTING: load_dotenv() HARUS dipanggil SEBELUM import core.agent
# karena MedAgent.__init__() langsung membaca os.getenv("GROQ_API_KEY")
# saat pertama kali diinstansiasi.
# =============================================================
import os
import sys
from dotenv import load_dotenv

# Menentukan path absolut ke file .env menggunakan os.path
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, '.env')

# Memuat file .env secara absolut dengan override=True
load_dotenv(dotenv_path=env_path, override=True)

# Baru sekarang import core (os.getenv sudah terisi)
from core.agent import get_agent

# ── Dataset Gejala ────────────────────────────────────────────────────────────
# backend_bridge.py

DATASET_GEJALA = {
    "Gejala Umum": [
        {"id": "fever",             "label": "Demam / Badan Panas"},
        {"id": "high_fever",        "label": "Demam Sangat Tinggi"},
        {"id": "fatigue",           "label": "Kelelahan / Lemas Ekstrem"},
        {"id": "chills",            "label": "Menggigil"},
        {"id": "night_sweats",      "label": "Keringat Malam"},
        {"id": "weight_loss",       "label": "Penurunan Berat Badan Drastis"},
        {"id": "loss_of_appetite",  "label": "Nafsu Makan Menurun"},
        {"id": "malaise",           "label": "Tidak Enak Badan (Malaise)"},
    ],

    "Sistem Kepala & Saraf": [
        {"id": "headache",          "label": "Sakit Kepala"},
        {"id": "severe_headache",   "label": "Sakit Kepala Sangat Hebat Mendadak"},
        {"id": "dizziness",         "label": "Pusing / Kleyengan / Vertigo"},
        {"id": "confusion",         "label": "Kebingungan / Disorientasi"},
        {"id": "seizure",           "label": "Kejang"},
        {"id": "loss_of_consciousness", "label": "Kesadaran Menurun / Pingsan"},
        {"id": "facial_drooping",   "label": "Wajah Mencong / Mulut Miring"},
        {"id": "speech_difficulty", "label": "Bicara Pelo / Tidak Bisa Bicara"},
        {"id": "visual_disturbance","label": "Pandangan Kabur / Gangguan Penglihatan"},
    ],

    "Sistem Pernapasan": [
        {"id": "cough",             "label": "Batuk"},
        {"id": "chronic_cough",     "label": "Batuk Kronis / Lama (> 2 minggu)"},
        {"id": "bloody_cough",      "label": "Batuk Darah"},
        {"id": "shortness_of_breath","label": "Sesak Napas"},
        {"id": "severe_dyspnea",    "label": "Sesak Napas Berat / Tidak Bisa Berbaring"},
        {"id": "wheezing",          "label": "Napas Berbunyi Mengi"},
        {"id": "rapid_breathing",   "label": "Napas Cepat / Tersengal-sengal"},
        {"id": "sore_throat",       "label": "Nyeri Tenggorokan"},
        {"id": "runny_nose",        "label": "Hidung Tersumbat / Pilek"},
        {"id": "nasal_congestion",  "label": "Hidung Mampet (Sinusitis)"},
        {"id": "loss_of_smell",     "label": "Hilang Penciuman (Anosmia)"},
    ],

    "Sistem Pencernaan": [
        {"id": "nausea",            "label": "Mual"},
        {"id": "vomiting",          "label": "Muntah"},
        {"id": "bloody_vomiting",   "label": "Muntah Darah"},
        {"id": "diarrhea",          "label": "Diare / Mencret"},
        {"id": "bloody_diarrhea",   "label": "Diare Berdarah"},
        {"id": "abdominal_pain",    "label": "Nyeri / Kram Perut"},
        {"id": "severe_abdominal_pain","label": "Nyeri Perut Mendadak Sangat Berat"},
        {"id": "heartburn",         "label": "Rasa Terbakar di Dada / Heartburn"},
        {"id": "acid_regurgitation","label": "Asam Lambung Naik / Regurgitasi"},
        {"id": "bloating",          "label": "Perut Kembung"},
        {"id": "ascites",           "label": "Perut Membesar / Penumpukan Cairan"},
        {"id": "difficulty_swallowing","label": "Kesulitan Menelan"},
    ],

    "Sistem Jantung & Pembuluh Darah": [
        {"id": "chest_pain",        "label": "Nyeri Dada"},
        {"id": "palpitations",      "label": "Jantung Berdebar-debar"},
        {"id": "rapid_heartbeat",   "label": "Detak Jantung Sangat Cepat"},
        {"id": "leg_swelling",      "label": "Kaki / Pergelangan Kaki Bengkak"},
        {"id": "arm_weakness",      "label": "Lengan / Kaki Lemas Sebelah"},
        {"id": "cyanosis",          "label": "Bibir / Kuku Membiru (Sianosis)"},
    ],

    "Sistem Kemih & Reproduksi": [
        {"id": "painful_urination", "label": "Nyeri / Perih Saat BAK"},
        {"id": "frequent_urination","label": "BAK Sering / Anyang-anyangan"},
        {"id": "blood_in_urine",    "label": "Urin Berdarah"},
        {"id": "decreased_urination","label": "BAK Berkurang / Tidak BAK (Oliguria)"},
        {"id": "lower_back_pain",   "label": "Nyeri Punggung Bawah / Pinggang"},
    ],

    "Kulit & Jaringan": [
        {"id": "rash",              "label": "Ruam / Bintik Merah di Kulit"},
        {"id": "fluid_filled_rash", "label": "Ruam Berisi Cairan / Bintil Air"},
        {"id": "petechiae",         "label": "Bintik Perdarahan Kecil (Petekie)"},
        {"id": "jaundice",          "label": "Kuning (Mata / Kulit Menguning)"},
        {"id": "skin_itching",      "label": "Gatal di Kulit"},
        {"id": "bruising",          "label": "Mudah Memar / Lebam"},
    ],

    "Mata, Hidung & THT": [
        {"id": "red_eye",           "label": "Mata Merah"},
        {"id": "eye_discharge",     "label": "Mata Berair / Keluar Kotoran"},
        {"id": "eye_pain",          "label": "Nyeri Mata"},
        {"id": "facial_pain",       "label": "Nyeri Wajah / Sekitar Hidung & Mata"},
        {"id": "nosebleed",         "label": "Mimisan"},
        {"id": "bleeding_gums",     "label": "Gusi Berdarah"},
    ],

    "Sendi, Otot & Gerak": [
        {"id": "joint_pain",        "label": "Nyeri Sendi"},
        {"id": "severe_joint_pain", "label": "Nyeri Sendi Sangat Hebat"},
        {"id": "joint_swelling",    "label": "Sendi Bengkak"},
        {"id": "muscle_pain",       "label": "Nyeri Otot / Pegal Linu"},
        {"id": "muscle_weakness",   "label": "Otot Lemas / Tidak Bertenaga"},
        {"id": "back_pain",         "label": "Nyeri Punggung"},
    ],

    "Metabolik & Endokrin": [
        {"id": "excessive_thirst",  "label": "Rasa Haus Berlebihan (Polidipsi)"},
        {"id": "excessive_urination_dm","label": "BAK Sangat Banyak (Poliuria)"},
        {"id": "excessive_hunger",  "label": "Lapar Terus / Makan Banyak (Polifagi)"},
        {"id": "blurred_vision_dm", "label": "Penglihatan Buram (terkait DM)"},
        {"id": "slow_wound_healing","label": "Luka Sulit Sembuh"},
        {"id": "tingling_numbness", "label": "Kesemutan / Kebas di Tangan atau Kaki"},
        {"id": "acetone_breath",    "label": "Napas Berbau Aseton / Buah"},
    ],

    "Perdarahan & Syok": [
        {"id": "internal_bleeding", "label": "Perdarahan Internal (feses hitam / darah)"},
        {"id": "external_bleeding", "label": "Perdarahan dari Tubuh / Luka Tidak Berhenti"},
        {"id": "shock_signs",       "label": "Tanda Syok (lemas ekstrem, kulit dingin, nadi lemah)"},
        {"id": "dehydration",       "label": "Dehidrasi (mata cekung, tidak BAK, bibir kering)"},
    ],
}

ALL_SYMPTOMS_LIST = [
    item["id"] for sublist in DATASET_GEJALA.values() for item in sublist
]

class BackendController:
    def __init__(self):
        self.agent = get_agent()

    def ekstrak_gejala_dari_cerita(self, teks_cerita: str) -> list:
        if not teks_cerita.strip():
            return []
        symptom_dict = self.agent.extract_symptoms_from_text(teks_cerita, ALL_SYMPTOMS_LIST)
        return [symptom for symptom, status in symptom_dict.items() if status == 1]

    def proses_analisis_stream(self, list_gejala_aktif: list, teks_cerita: str):
        symptom_dict = {sym: 1 for sym in list_gejala_aktif}
        return self.agent.run_stream(symptom_dict, teks_cerita)
    
    def followup_chat(self, question: str, chat_history: list, analysis_context: dict) -> str:
        return self.agent.followup_chat(
        question=question,
        chat_history=chat_history,
        analysis_context=analysis_context,
    )