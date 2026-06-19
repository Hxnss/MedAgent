# app.py — MedAgent | Sistem Analisis Kesehatan AI

import streamlit as st
from backend_bridge import BackendController, DATASET_GEJALA, ALL_SYMPTOMS_LIST

# ── Konfigurasi Halaman ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="MedAgent — Asisten Kesehatan AI",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Inisialisasi Session State ────────────────────────────────────────────────
if "backend" not in st.session_state:
    st.session_state.backend = BackendController()

if "selected_symptoms" not in st.session_state:
    st.session_state.selected_symptoms = set()

if "show_report" not in st.session_state:
    st.session_state.show_report = False

if "report_data" not in st.session_state:
    st.session_state.report_data = None

if "user_story" not in st.session_state:
    st.session_state.user_story = ""

# ── TAMBAHAN: Session state untuk follow-up chat ──────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "followup_input" not in st.session_state:
    st.session_state.followup_input = None


# ==============================================================================
# ── HEADER ────────────────────────────────────────────────────────────────────
# ==============================================================================
st.title("🩺 MedAgent")
st.markdown(
    "Halo! Saya adalah asisten kesehatan berbasis AI. "
    "Ceritakan keluhan yang Anda rasakan, dan saya akan membantu menganalisis "
    "kemungkinan kondisi kesehatan Anda serta memberikan saran awal. "
    "*(Catatan: ini bukan pengganti diagnosis dokter)*"
)
st.markdown("---")


# ==============================================================================
# ── BAGIAN 1: INPUT CERITA + TOMBOL DETEKSI OTOMATIS ─────────────────────────
# ==============================================================================
st.subheader("✍️ Langkah 1 — Ceritakan Keluhan Anda")
st.caption("Tulis keluhan dalam bahasa sehari-hari. AI akan mendeteksi gejala secara otomatis.")

col_text, col_btn = st.columns([4, 1], vertical_alignment="bottom")

with col_text:
    user_story_input = st.text_area(
        label="Cerita keluhan:",
        value=st.session_state.user_story,
        placeholder='Contoh: "kepala saya pusing udah 3 hari, trus juga muntah banyak banget dan badan terasa menggigil"',
        height=110,
        label_visibility="collapsed",
        key="story_textarea",
    )
    st.session_state.user_story = user_story_input

with col_btn:
    detect_clicked = st.button(
        "🔍 Deteksi Sekarang",
        type="secondary",
        use_container_width=True,
        key="btn_detect",
    )

if detect_clicked:
    if st.session_state.user_story.strip():
        with st.spinner("🤖 AI sedang menganalisis cerita Anda..."):
            detected = st.session_state.backend.ekstrak_gejala_dari_cerita(
                st.session_state.user_story
            )
        if detected:
            st.session_state.selected_symptoms.update(detected)
            st.toast(
                f"✅ Berhasil mendeteksi {len(detected)} gejala: {', '.join(detected)}",
                icon="✅",
            )
            st.rerun()
        else:
            st.warning("⚠️ AI tidak dapat mendeteksi gejala spesifik dari cerita Anda. Silakan centang manual di bawah.")
    else:
        st.warning("⚠️ Kolom cerita masih kosong! Tulis keluhan Anda terlebih dahulu.")

st.markdown("---")


# ==============================================================================
# ── BAGIAN 2: CHECKBOX GEJALA PER KATEGORI ───────────────────────────────────
# ==============================================================================
st.subheader("☑️ Langkah 2 — Konfirmasi / Pilih Gejala Manual")
st.caption("Gejala yang terdeteksi otomatis sudah tercentang. Anda dapat menambah atau mengurangi secara manual.")

new_selected = set()

tabs = st.tabs(list(DATASET_GEJALA.keys()))

for tab, (kategori, list_gejala) in zip(tabs, DATASET_GEJALA.items()):
    with tab:
        if not list_gejala:
            st.caption("Tidak ada gejala tersedia.")
            continue
        cols = st.columns(2)
        for i, gejala in enumerate(list_gejala):
            is_checked = gejala["id"] in st.session_state.selected_symptoms
            display_label = f"🔍 {gejala['label']}" if is_checked else gejala["label"]
            cb_val = cols[i % 2].checkbox(
                label=display_label,
                value=is_checked,
                key=f"cb_{gejala['id']}",
            )
            if cb_val:
                new_selected.add(gejala["id"])

st.session_state.selected_symptoms = new_selected

st.markdown("---")

# ==============================================================================
# ── BAGIAN 3: TOMBOL ANALISIS (dengan logika disable) ────────────────────────
# ==============================================================================
n_selected = len(st.session_state.selected_symptoms)
button_disabled = n_selected == 0

if button_disabled:
    st.caption(
        "🔒 :red[Tombol analisis terkunci.] "
        "Silakan isi cerita lalu klik *Deteksi Sekarang*, "
        "ATAU centang minimal 1 gejala secara manual di atas."
    )
else:
    st.caption(f"✅ :green[{n_selected} gejala terpilih. Siap untuk dianalisis!]")

analyse_clicked = st.button(
    "⚡ Analisis Sekarang",
    type="primary",
    disabled=button_disabled,
    use_container_width=True,
    key="btn_analyse",
)


# ==============================================================================
# ── LOGIKA ANALISIS: STREAMING + SIMPAN KE SESSION STATE ─────────────────────
# ==============================================================================
if analyse_clicked:
    st.session_state.report_data = None
    st.session_state.show_report = False
    st.session_state.chat_history = []  # reset chat tiap analisis baru

    list_aktif = list(st.session_state.selected_symptoms)

    st.markdown("---")
    st.subheader("📊 Report Card Hasil Analisis")

    with st.spinner("🔬 Menjalankan analisis model ML + risk classifier..."):
        partial_res, stream_gen = st.session_state.backend.proses_analisis_stream(
            list_aktif, st.session_state.user_story
        )

    if not partial_res.success:
        st.error(f"❌ Terjadi kesalahan saat analisis: {partial_res.error}")
        st.stop()

    pred = partial_res.prediction
    sev = partial_res.severity
    d_info = partial_res.disease_info if isinstance(partial_res.disease_info, dict) else {}

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🔮 Top 3 Kandidat Penyakit**")
        if pred and hasattr(pred, "top3") and pred.top3:
            rank_icons = ["🥇", "🥈", "🥉"]
            for idx, disease in enumerate(pred.top3):
                if isinstance(disease.confidence_pct, (int, float)):
                    pct_str = f"{disease.confidence_pct:.1f}%"
                else:
                    pct_str = str(disease.confidence_pct)
                st.markdown(f"{rank_icons[idx]} **{disease.name}**")
                st.caption(pct_str)
        else:
            st.markdown("*Tidak ada data prediksi.*")

    with col2:
        st.markdown("**🚨 Tingkat Urgensi**")
        if sev:
            tingkat = sev.severity_level
            rekomendasi = sev.recommended_action if sev.recommended_action else "Konsultasikan ke dokter."

            high_levels = {"EMERGENCY", "HIGH"}
            moderate_levels = {"URGENT", "SEMI-URGENT", "MODERATE"}
            low_levels = {"NON-URGENT", "LOW"}

            if tingkat in high_levels:
                st.error(f"🔴 {tingkat}")
            elif tingkat in moderate_levels:
                st.warning(f"🟠 {tingkat}")
            elif tingkat in low_levels:
                st.success(f"🟢 {tingkat}")
            else:
                st.info(f"🔵 {tingkat}")

            st.caption(rekomendasi)
        else:
            st.markdown("*Data urgensi tidak tersedia.*")

    with col3:
        st.markdown("**👨‍⚕️ Saran Spesialis**")
        spesialis = d_info.get("specialist", "Dokter Umum")
        deskripsi = d_info.get("description", "")
        emergency = d_info.get("emergency_signs", [])

        st.info(f"**{spesialis}**")
        if deskripsi:
            st.caption(deskripsi[:180] + "..." if len(deskripsi) > 180 else deskripsi)
        if emergency:
            st.markdown("⚠️ **Tanda darurat:**")
            for tanda in emergency[:3]:
                st.markdown(f"- {tanda}")

    st.markdown("---")
    st.markdown("#### 📝 Laporan Kesehatan Lengkap")
    st.caption("Laporan berikut dibuat oleh AI berdasarkan data gejala dan model prediktif Anda.")

    report_placeholder = st.empty()
    full_text_report = ""

    for chunk in stream_gen:
        full_text_report += chunk
        report_placeholder.markdown(full_text_report)

    st.session_state.report_data = {
        "prediction": pred,
        "severity": sev,
        "disease_info": d_info,
        "full_text": full_text_report,
    }
    st.session_state.show_report = True


# ==============================================================================
# ── BAGIAN 4: TAMPILAN REPORT DARI SESSION STATE (setelah re-render) ──────────
# ==============================================================================
elif st.session_state.show_report and st.session_state.report_data:
    data = st.session_state.report_data
    pred = data["prediction"]
    sev = data["severity"]
    d_info = data["disease_info"] if isinstance(data["disease_info"], dict) else {}

    st.markdown("---")
    st.subheader("📊 Ringkasan Analisis Medis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🔮 Top 3 Kandidat Penyakit**")
        if pred and hasattr(pred, "top3") and pred.top3:
            rank_icons = ["🥇", "🥈", "🥉"]
            for idx, disease in enumerate(pred.top3):
                if isinstance(disease.confidence_pct, (int, float)):
                    pct_val = disease.confidence_pct
                    pct_str = f"{pct_val:.1f}%"
                else:
                    pct_val = 0
                    pct_str = str(disease.confidence_pct)
                st.markdown(f"{rank_icons[idx]} **{disease.name}**")
                st.progress(min(pct_val / 100, 1.0))
                st.caption(pct_str)
        else:
            st.markdown("*Tidak ada data prediksi.*")

    with col2:
        st.markdown("**🚨 Tingkat Urgensi**")
        if sev:
            tingkat = sev.severity_level
            rekomendasi = sev.recommended_action if sev.recommended_action else "Konsultasikan ke dokter."

            high_levels = {"EMERGENCY", "HIGH"}
            moderate_levels = {"URGENT", "SEMI-URGENT", "MODERATE"}
            low_levels = {"NON-URGENT", "LOW"}

            if tingkat in high_levels:
                st.error(f"🔴 {tingkat}")
            elif tingkat in moderate_levels:
                st.warning(f"🟠 {tingkat}")
            elif tingkat in low_levels:
                st.success(f"🟢 {tingkat}")
            else:
                st.info(f"🔵 {tingkat}")

            st.caption(rekomendasi)
        else:
            st.markdown("*Data urgensi tidak tersedia.*")

    with col3:
        st.markdown("**👨‍⚕️ Saran Spesialis**")
        spesialis = d_info.get("specialist", "Dokter Umum")
        deskripsi = d_info.get("description", "")
        emergency = d_info.get("emergency_signs", [])

        st.info(f"**{spesialis}**")
        if deskripsi:
            st.caption(deskripsi[:180] + "..." if len(deskripsi) > 180 else deskripsi)
        if emergency:
            st.markdown("⚠️ **Tanda darurat:**")
            for tanda in emergency[:3]:
                st.markdown(f"- {tanda}")

    st.markdown("---")
    st.markdown("#### 📝 Laporan Kesehatan Lengkap")
    st.markdown(data["full_text"])



# ==============================================================================
# ── BAGIAN 6: TOMBOL RESET ────────────────────────────────────────────────────
# ==============================================================================
if st.session_state.show_report:
    st.markdown("---")
    col_reset_l, col_reset_c, col_reset_r = st.columns([2, 1.5, 2])
    with col_reset_c:
        if st.button("🔄 Analisis Ulang / Reset", type="secondary", use_container_width=True, key="btn_reset"):
            st.session_state.selected_symptoms = set()
            st.session_state.show_report = False
            st.session_state.report_data = None
            st.session_state.user_story = ""
            st.session_state.chat_history = []       # reset chat history
            st.session_state.followup_input = None   # reset quick button
            st.rerun()


# ==============================================================================
# ── BAGIAN 5: FOLLOW-UP CHAT ──────────────────────────────────────────────────
# ==============================================================================
if st.session_state.show_report and st.session_state.report_data:
    data = st.session_state.report_data
    pred = data["prediction"]
    sev = data["severity"]
    d_info = data["disease_info"] if isinstance(data["disease_info"], dict) else {}

    st.markdown("---")
    st.subheader("💬 Tanya Lebih Lanjut")
    st.caption("Punya pertanyaan tentang kondisi ini? Tanya langsung ke MedAgent — jawaban disesuaikan dengan hasil analisis Anda.")

    # ── Quick question buttons ────────────────────────────────────────────────
    quick_questions = [
        "Apakah kondisi ini menular?",
        "Berapa lama biasanya sembuh?",
        "Obat apa yang bisa diminum dulu?",
        "Makanan apa yang harus dihindari?",
        "Kapan harus segera ke IGD?",
        "Bagaimana cara mencegahnya?",
    ]

    st.markdown("💡 **Pertanyaan yang sering ditanyakan:**")
    qcol1, qcol2, qcol3 = st.columns(3)
    quick_cols = [qcol1, qcol2, qcol3]

    for i, q in enumerate(quick_questions):
        if quick_cols[i % 3].button(q, key=f"quick_{i}", use_container_width=True):
            st.session_state.followup_input = q

    # ── Riwayat chat ──────────────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Input box ─────────────────────────────────────────────────────────────
    col_input, col_send = st.columns([5, 1], vertical_alignment="bottom")
    with col_input:
        user_question = st.text_input(
            label="input",
            placeholder="Ketik pertanyaan Anda di sini...",
            label_visibility="collapsed",
            key="followup_text_input",
        )
    with col_send:
        send_clicked = st.button("➤ Kirim", use_container_width=True, key="btn_send")

    final_question = None
    if send_clicked and user_question.strip():
        final_question = user_question

    # ── Proses pertanyaan (dari quick button atau ketik manual) ───────────────
    final_question = final_question or st.session_state.get("followup_input")


    if final_question:
        st.session_state.followup_input = None  # reset quick button

        st.session_state.chat_history.append({"role": "user", "content": final_question})

        # Susun konteks analisis untuk dikirim ke agent
        analysis_context = {
            "disease":    pred.top3[0].name if pred and pred.top3 else "Tidak diketahui",
            "confidence": f"{pred.top3[0].confidence_pct:.1f}%" if pred and pred.top3 and isinstance(pred.top3[0].confidence_pct, (int, float)) else str(pred.top3[0].confidence_pct) if pred and pred.top3 else "",
            "disease2":   pred.top3[1].name if pred and len(pred.top3) > 1 else "",
            "disease3":   pred.top3[2].name if pred and len(pred.top3) > 2 else "",
            "severity":   sev.severity_level if sev else "Tidak diketahui",
            "symptoms":   ", ".join(pred.active_symptoms) if pred else "Tidak ada",
            "specialist": d_info.get("specialist", "Dokter Umum"),
        }

        with st.spinner("🤖 MedAgent sedang menjawab..."):
            answer = st.session_state.backend.followup_chat(
                question=final_question,
                chat_history=st.session_state.chat_history[:-1],
                analysis_context=analysis_context,
            )

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "⚠️ **Disclaimer**: MedAgent adalah alat bantu AI dan **bukan pengganti** diagnosis dokter. "
    "Selalu konsultasikan kondisi Anda dengan tenaga medis profesional."
)