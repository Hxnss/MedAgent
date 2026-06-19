"""
core/agent.py
==============
Orchestrator utama MedAgent.
Menjalankan semua tools (ML predict, risk classify, symptom score, disease info)
lalu menghasilkan laporan kesehatan via Groq LLM (streaming maupun non-streaming).
"""

import os
import json
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

from groq import Groq


from core.ml_model import get_model, PredictionResult
from core.risk_classifier import classify_risk, SeverityResult
from core.symptom_scorer import score_symptoms, SpecificityResult
from utils.disease_info import get_disease_info



# ── Konstanta ─────────────────────────────────────────────────────────────────

GROQ_MODEL = "llama-3.3-70b-versatile"


# ── Dataclass output ──────────────────────────────────────────────────────────

@dataclass
class ReasoningStep:
    tool_name: str
    tool_input: dict
    tool_output: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentResult:
    prediction: PredictionResult
    severity: SeverityResult
    specificity: SpecificityResult
    disease_info: dict
    health_report: str
    reasoning_log: List[ReasoningStep]
    success: bool
    error: Optional[str] = None


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Kamu adalah MedAgent, asisten kesehatan AI yang membantu pengguna Indonesia memahami gejala mereka.
Kamu memiliki akses ke tools berikut yang SUDAH DIJALANKAN dan hasilnya disediakan untukmu:

1. predict_disease(symptoms) -> Top-3 kandidat penyakit + confidence score
2. classify_risk(disease, symptoms) -> Tingkat urgensi (EMERGENCY/URGENT/SEMI-URGENT/NON-URGENT) + rekomendasi
3. score_symptom_specificity(symptoms) -> Kualitas input gejala pengguna
4. get_disease_info(disease_name) -> Info lengkap penyakit (spesialis, risiko, pencegahan)

Tugasmu: Berdasarkan hasil tools yang sudah tersedia, buat laporan kesehatan yang:
- Komprehensif namun mudah dipahami masyarakat umum
- Ditulis dalam Bahasa Indonesia yang hangat dan empatik
- Mencakup semua aspek penting: kemungkinan kondisi, urgensi, tindakan, dan edukasi
- SELALU sertakan disclaimer bahwa ini bukan diagnosis dokter
- Gunakan format markdown yang rapi
"""


# ── Orchestrator ──────────────────────────────────────────────────────────────

class MedAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Pastikan file .env sudah berisi GROQ_API_KEY=..."
            )
        self._groq = Groq(api_key=api_key)
        self._ml   = get_model()

    # ── Build LLM Prompt ──────────────────────────────────────────────────────
    def _build_prompt(self, user_text, prediction, severity, specificity, d_info):
        top1, top2, top3 = prediction.top3
        return f"""
=== DATA HASIL TOOLS ===

GEJALA AKTIF ({prediction.n_active} gejala):
{', '.join(prediction.active_symptoms) if prediction.active_symptoms else 'Tidak ada'}

KELUHAN USER (teks bebas): "{user_text}"

PREDIKSI PENYAKIT:
- #1: {top1.name} (Confidence: {top1.confidence_pct})
- #2: {top2.name} (Confidence: {top2.confidence_pct})
- #3: {top3.name} (Confidence: {top3.confidence_pct})
- Low confidence warning: {prediction.low_confidence}

TINGKAT URGENSI: {severity.severity_level}
- Rules yang terpicu: {'; '.join(severity.triggered_rules)}
- Rekomendasi: {severity.recommended_action}

KUALITAS INPUT GEJALA:
- Skor: {specificity.score} ({specificity.score_label})
- Jumlah gejala spesifik: {specificity.n_specific}
- Warning: {specificity.warning_message if specificity.warning else 'Tidak ada'}

INFO PENYAKIT ({top1.name}):
- Nama Indonesia: {d_info.get('id', top1.name)}
- Spesialis: {d_info.get('specialist', 'Dokter Umum')}
- Deskripsi: {d_info.get('description', '')}
- Tanda darurat: {', '.join(d_info.get('emergency_signs', []))}
- Pencegahan: {', '.join(d_info.get('prevention', [])[:3])}

=== INSTRUKSI ===

Buatlah laporan kesehatan terstruktur dalam Bahasa Indonesia dengan format berikut:

## Ringkasan Kondisi
[Jelaskan secara singkat dan empatik kondisi yang kemungkinan dialami pengguna]

## Interpretasi Hasil Analisis
[Jelaskan mengapa model memprediksi {top1.name} sebagai kandidat utama]

## Tentang {d_info.get('id', top1.name)}
[Jelaskan penyakit ini dengan bahasa sederhana]

## Panduan Tindak Lanjut
[Panduan konkret: apa yang harus dilakukan, kapan ke dokter, spesialis apa]

## Tanda Bahaya yang Perlu Diwaspadai
[Gejala yang perlu segera ke IGD]

## Tips Perawatan dan Pencegahan
[Saran praktis yang bisa dilakukan pengguna]

---
Disclaimer: Laporan ini dihasilkan oleh sistem AI dan bukan merupakan diagnosis medis. Selalu konsultasikan kondisi Anda dengan tenaga medis profesional.

Gunakan bahasa yang hangat, empatik, dan mudah dipahami masyarakat awam.
"""

    # ── Jalankan Semua Tools ──────────────────────────────────────────────────
    def _run_tools(self, symptom_dict):
        reasoning_log = []

        prediction = self._ml.predict(symptom_dict)
        reasoning_log.append(ReasoningStep(
            tool_name   = "predict_disease",
            tool_input  = {"active_symptoms": prediction.active_symptoms},
            tool_output = json.dumps({
                "top1": {"disease": prediction.top3[0].name, "confidence": prediction.top3[0].confidence_pct},
                "top2": {"disease": prediction.top3[1].name, "confidence": prediction.top3[1].confidence_pct},
                "top3": {"disease": prediction.top3[2].name, "confidence": prediction.top3[2].confidence_pct},
                "low_confidence": prediction.low_confidence,
            }, indent=2),
        ))

        severity = classify_risk(prediction.top3[0].name, symptom_dict)
        reasoning_log.append(ReasoningStep(
            tool_name   = "classify_risk",
            tool_input  = {"disease": prediction.top3[0].name, "n_symptoms": prediction.n_active},
            tool_output = json.dumps({
                "level": severity.severity_level,
                "triggered_rules": severity.triggered_rules,
            }, indent=2),
        ))

        specificity = score_symptoms(symptom_dict)
        reasoning_log.append(ReasoningStep(
            tool_name   = "score_symptom_specificity",
            tool_input  = {"n_active": specificity.n_active},
            tool_output = json.dumps({
                "score": specificity.score,
                "label": specificity.score_label,
                "n_specific": specificity.n_specific,
            }, indent=2),
        ))

        d_info = get_disease_info(prediction.top3[0].name)
        reasoning_log.append(ReasoningStep(
            tool_name   = "get_disease_info",
            tool_input  = {"disease": prediction.top3[0].name},
            tool_output = json.dumps({
                "specialist": d_info.get("specialist"),
                "emergency_signs": d_info.get("emergency_signs", []),
            }, indent=2),
        ))

        return prediction, severity, specificity, d_info, reasoning_log

    # ── Non-Streaming ─────────────────────────────────────────────────────────
    def run(self, symptom_dict: dict, user_text: str = "") -> AgentResult:
        try:
            prediction, severity, specificity, d_info, reasoning_log = self._run_tools(symptom_dict)
            prompt = self._build_prompt(user_text, prediction, severity, specificity, d_info)

            response = self._groq.chat.completions.create(
                model       = GROQ_MODEL,
                messages    = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens  = 2048,
                temperature = 0.7,
            )
            return AgentResult(
                prediction    = prediction,
                severity      = severity,
                specificity   = specificity,
                disease_info  = d_info,
                health_report = response.choices[0].message.content,
                reasoning_log = reasoning_log,
                success       = True,
            )
        except Exception as e:
            return AgentResult(
                prediction=None, severity=None, specificity=None,
                disease_info={}, health_report=f"Terjadi kesalahan: {str(e)}",
                reasoning_log=[], success=False, error=str(e),
            )

    # ── Streaming ─────────────────────────────────────────────────────────────
    def run_stream(self, symptom_dict: dict, user_text: str = ""):
        """
        Menjalankan analisis dan streaming laporan LLM.

        Returns:
            Tuple (AgentResult, Generator[str]) — partial result sudah berisi
            prediction/severity/disease_info yang bisa langsung dipakai frontend,
            generator menghasilkan potongan teks laporan LLM satu per satu.
        """
        try:
            prediction, severity, specificity, d_info, reasoning_log = self._run_tools(symptom_dict)

            partial_result = AgentResult(
                prediction    = prediction,
                severity      = severity,
                specificity   = specificity,
                disease_info  = d_info,
                health_report = "",
                reasoning_log = reasoning_log,
                success       = True,
            )

            prompt = self._build_prompt(user_text, prediction, severity, specificity, d_info)

            stream = self._groq.chat.completions.create(
                model       = GROQ_MODEL,
                messages    = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens  = 2048,
                temperature = 0.7,
                stream      = True,
            )

            def _chunk_generator():
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta

            return partial_result, _chunk_generator()

        except Exception as e:
            err_result = AgentResult(
                prediction=None, severity=None, specificity=None,
                disease_info={}, health_report=f"Error: {e}",
                reasoning_log=[], success=False, error=str(e),
            )
            return err_result, iter([])

    # ── NLP Symptom Extractor ─────────────────────────────────────────────────
    def extract_symptoms_from_text(
        self, user_text: str, available_symptoms: list
    ) -> dict:
        """
        Gunakan LLM untuk memetakan teks keluhan bebas ke daftar gejala dataset.

        Returns:
            dict {symptom_id: 1} untuk gejala yang terdeteksi.
        """
        symptoms_list = "\n".join(f"- {s}" for s in available_symptoms)

        prompt = f"""
Kamu adalah sistem ekstraksi gejala medis. 
Tugasmu: baca keluhan pasien, lalu tentukan gejala mana yang COCOK dari daftar yang tersedia.

KELUHAN PASIEN:
"{user_text}"

DAFTAR GEJALA YANG TERSEDIA:
{symptoms_list}

INSTRUKSI:
- Pilih HANYA gejala dari daftar di atas yang disebutkan atau sangat tersirat dari keluhan pasien
- Jangan menambahkan gejala yang tidak ada di daftar
- Jangan berasumsi berlebihan — hanya yang jelas disebut atau sangat tersirat
- Kembalikan HANYA JSON array berisi nama gejala yang cocok, tanpa penjelasan apapun
- Format: ["symptom_1", "symptom_2", ...]

Contoh output: ["fever", "headache", "nausea"]
"""
        response = self._groq.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = [{"role": "user", "content": prompt}],
            max_tokens  = 512,
            temperature = 0.1,
        )

        raw = response.choices[0].message.content.strip()

        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if not match:
            return {}

        try:
            detected = json.loads(match.group())
        except json.JSONDecodeError:
            return {}

        valid_set = set(available_symptoms)
        return {sym: 1 for sym in detected if sym in valid_set}

    # ── Follow-up Chat ────────────────────────────────────────────────────────
    def followup_chat(
        self,
        question: str,
        chat_history: list,
        analysis_context: dict,
    ) -> str:
        """
        Jawab pertanyaan follow-up user dalam konteks laporan yang sudah dibuat.
        """
        system = f"""
Kamu adalah MedAgent, asisten kesehatan AI yang sudah menganalisis kondisi pasien.

KONTEKS ANALISIS SEBELUMNYA:
- Kandidat penyakit #1: {analysis_context.get('disease', 'Tidak diketahui')} ({analysis_context.get('confidence', '')})
- Kandidat #2: {analysis_context.get('disease2', '')}
- Kandidat #3: {analysis_context.get('disease3', '')}
- Tingkat urgensi: {analysis_context.get('severity', 'Tidak diketahui')}
- Gejala aktif: {analysis_context.get('symptoms', 'Tidak ada')}
- Spesialis: {analysis_context.get('specialist', 'Dokter Umum')}

INSTRUKSI:
- Jawab pertanyaan follow-up berdasarkan konteks analisis di atas
- Gunakan Bahasa Indonesia yang hangat dan mudah dipahami
- Jawaban singkat, padat, dan langsung ke poin (maksimal 3-4 paragraf)
- SELALU ingatkan user untuk konsultasi dokter jika pertanyaan menyangkut keputusan medis penting
- Jangan memberikan dosis obat spesifik
"""
        messages = [{"role": "system", "content": system}]
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": question})

        response = self._groq.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = messages,
            max_tokens  = 1024,
            temperature = 0.7,
        )

        return response.choices[0].message.content


# ── Module-level Singleton ────────────────────────────────────────────────────

_agent: Optional[MedAgent] = None


def get_agent() -> MedAgent:
    global _agent
    if _agent is None:
        _agent = MedAgent()
    return _agent


__all__ = ["MedAgent", "AgentResult", "ReasoningStep", "get_agent"]
