"""
utils/disease_info.py
======================
Database informasi penyakit untuk MedAgent.
Digunakan oleh core/agent.py untuk mengambil detail penyakit (spesialis, tanda darurat, dll.)
yang kemudian disertakan dalam laporan kesehatan.
"""

# ── Database Penyakit ─────────────────────────────────────────────────────────
# Setiap entry berisi informasi yang akan ditampilkan di Report Card frontend.

_DISEASE_DB: dict = {
    "Stroke": {
        "id":               "Stroke",
        "specialist":       "Dokter Saraf (Neurologi)",
        "description":      "Kondisi darurat yang terjadi ketika pasokan darah ke otak terganggu, menyebabkan kerusakan sel otak secara cepat.",
        "emergency_signs":  ["Wajah mencong / tidak simetris", "Lengan tiba-tiba lemah", "Bicara pelo atau tidak jelas", "Pandangan kabur mendadak", "Sakit kepala hebat tiba-tiba"],
        "prevention":       ["Kontrol tekanan darah rutin", "Hindari merokok", "Olahraga teratur", "Diet rendah garam dan lemak"],
    },
    "Dengue Hemorrhagic Fever": {
        "id":               "Demam Berdarah Dengue (DBD)",
        "specialist":       "Dokter Penyakit Dalam / Dokter Anak",
        "description":      "Infeksi virus dengue yang ditularkan nyamuk Aedes aegypti. Dapat menyebabkan perdarahan serius dan syok.",
        "emergency_signs":  ["Perdarahan dari hidung/gusi", "Muntah darah", "Kulit memar tanpa sebab", "Nyeri perut hebat", "Tekanan darah turun drastis"],
        "prevention":       ["Berantas sarang nyamuk (3M Plus)", "Gunakan lotion anti nyamuk", "Pasang kelambu"],
    },
    "Pneumonia": {
        "id":               "Pneumonia (Radang Paru)",
        "specialist":       "Dokter Paru / Dokter Penyakit Dalam",
        "description":      "Infeksi yang menyebabkan peradangan pada kantong udara di paru-paru, yang bisa terisi cairan atau nanah.",
        "emergency_signs":  ["Sesak napas berat", "Bibir atau kuku membiru", "Demam sangat tinggi > 39°C", "Penurunan kesadaran"],
        "prevention":       ["Vaksinasi pneumokokus dan flu", "Cuci tangan rutin", "Hindari paparan asap rokok"],
    },
    "Malaria": {
        "id":               "Malaria",
        "specialist":       "Dokter Penyakit Dalam / Dokter Tropis",
        "description":      "Infeksi parasit Plasmodium yang ditularkan nyamuk Anopheles. Menyebabkan demam periodik, menggigil, dan kelemahan.",
        "emergency_signs":  ["Penurunan kesadaran", "Kejang", "Demam sangat tinggi", "Urin berwarna sangat gelap"],
        "prevention":       ["Gunakan kelambu berinsektisida", "Obat anti-malaria profilaksis", "Hindari gigitan nyamuk saat senja"],
    },
    "Tuberculosis": {
        "id":               "Tuberkulosis (TBC)",
        "specialist":       "Dokter Paru (Pulmonologi)",
        "description":      "Infeksi bakteri Mycobacterium tuberculosis yang terutama menyerang paru-paru. Dapat menyebar ke organ lain.",
        "emergency_signs":  ["Batuk darah", "Sesak napas berat", "Nyeri dada hebat"],
        "prevention":       ["Vaksinasi BCG", "Ventilasi rumah yang baik", "Deteksi dini dan pengobatan OAT lengkap"],
    },
    "Typhoid Fever": {
        "id":               "Demam Tifoid (Tipes)",
        "specialist":       "Dokter Penyakit Dalam",
        "description":      "Infeksi bakteri Salmonella typhi melalui makanan/minuman yang terkontaminasi. Menyebabkan demam tinggi berkepanjangan.",
        "emergency_signs":  ["Perforasi usus", "Pendarahan saluran cerna", "Penurunan kesadaran", "Perut kaku seperti papan"],
        "prevention":       ["Cuci tangan sebelum makan", "Konsumsi air matang", "Vaksinasi tifoid", "Pilih makanan higienis"],
    },
    "COVID-19": {
        "id":               "COVID-19",
        "specialist":       "Dokter Penyakit Dalam / Dokter Paru",
        "description":      "Infeksi virus SARS-CoV-2 yang menyerang sistem pernapasan dengan gejala bervariasi dari ringan hingga berat.",
        "emergency_signs":  ["Sesak napas berat", "Saturasi oksigen < 94%", "Nyeri dada terus-menerus", "Kebingungan mendadak"],
        "prevention":       ["Vaksinasi COVID-19", "Cuci tangan rutin", "Gunakan masker di keramaian", "Hindari kerumunan"],
    },
    "Heart Failure": {
        "id":               "Gagal Jantung",
        "specialist":       "Dokter Jantung (Kardiologi)",
        "description":      "Kondisi di mana jantung tidak dapat memompa darah dengan cukup untuk memenuhi kebutuhan tubuh.",
        "emergency_signs":  ["Sesak napas tiba-tiba", "Bengkak kaki yang cepat memburuk", "Nyeri dada", "Batuk berdarah"],
        "prevention":       ["Kontrol hipertensi dan diabetes", "Hindari alkohol dan rokok", "Olahraga teratur sesuai kemampuan"],
    },
    "Asthma": {
        "id":               "Asma",
        "specialist":       "Dokter Paru / Dokter Alergi-Imunologi",
        "description":      "Penyakit kronis saluran napas yang menyebabkan peradangan dan penyempitan sehingga sulit bernapas.",
        "emergency_signs":  ["Tidak bisa berbicara karena sesak", "Bibir/kuku membiru", "Inhaler tidak menolong setelah 15 menit"],
        "prevention":       ["Identifikasi dan hindari pemicu", "Selalu bawa inhaler relief", "Flu shot tahunan"],
    },
    "Hepatitis A": {
        "id":               "Hepatitis A",
        "specialist":       "Dokter Penyakit Dalam / Gastroenterologi",
        "description":      "Infeksi virus pada hati yang menyebar melalui makanan atau minuman yang terkontaminasi.",
        "emergency_signs":  ["Kulit/mata sangat kuning", "Urin sangat gelap", "Penurunan kesadaran", "Perdarahan"],
        "prevention":       ["Vaksinasi Hepatitis A", "Sanitasi air dan makanan", "Cuci tangan setelah toilet"],
    },
    "Hepatitis B": {
        "id":               "Hepatitis B",
        "specialist":       "Dokter Gastroenterologi / Hepatologi",
        "description":      "Infeksi virus Hepatitis B yang menyerang hati dan bisa menjadi kronis, menyebabkan sirosis atau kanker hati.",
        "emergency_signs":  ["Kulit/mata sangat kuning mendadak", "Nyeri perut kanan atas", "Pembengkakan perut"],
        "prevention":       ["Vaksinasi Hepatitis B", "Hindari berbagi jarum suntik", "Gunakan kondom"],
    },
    "Leptospirosis": {
        "id":               "Leptospirosis",
        "specialist":       "Dokter Penyakit Dalam / Tropik",
        "description":      "Infeksi bakteri Leptospira melalui kontak dengan air atau tanah yang terkontaminasi urin hewan.",
        "emergency_signs":  ["Kuning mendadak", "Urin berkurang/tidak ada", "Perdarahan", "Penurunan kesadaran"],
        "prevention":       ["Gunakan pelindung saat banjir", "Hindari berenang di air tergenang", "Vaksinasi hewan peliharaan"],
    },
    "Chikungunya": {
        "id":               "Chikungunya",
        "specialist":       "Dokter Penyakit Dalam",
        "description":      "Infeksi virus chikungunya melalui gigitan nyamuk Aedes. Menyebabkan demam dan nyeri sendi yang parah.",
        "emergency_signs":  ["Demam > 40°C", "Pembengkakan sendi parah", "Ruam kulit meluas"],
        "prevention":       ["Berantas sarang nyamuk", "Gunakan lotion anti nyamuk", "Kenakan pakaian panjang"],
    },
    "Influenza": {
        "id":               "Influenza (Flu)",
        "specialist":       "Dokter Umum",
        "description":      "Infeksi virus influenza yang menyerang saluran pernapasan. Umumnya sembuh sendiri dalam 7-10 hari.",
        "emergency_signs":  ["Sesak napas berat", "Nyeri dada", "Kebingungan mendadak", "Demam > 39°C lebih dari 3 hari"],
        "prevention":       ["Vaksinasi flu tahunan", "Cuci tangan rutin", "Tutup mulut saat batuk/bersin"],
    },
    "Gastroenteritis": {
        "id":               "Gastroenteritis",
        "specialist":       "Dokter Umum / Gastroenterologi",
        "description":      "Peradangan lambung dan usus yang biasanya disebabkan infeksi virus/bakteri. Menyebabkan diare dan muntah.",
        "emergency_signs":  ["Tanda dehidrasi berat (tidak BAK > 8 jam)", "Tidak bisa minum sama sekali", "Penurunan kesadaran"],
        "prevention":       ["Cuci tangan sebelum makan", "Masak makanan hingga matang", "Gunakan air bersih"],
    },
    "Urinary Tract Infection": {
        "id":               "Infeksi Saluran Kemih (ISK)",
        "specialist":       "Dokter Umum / Dokter Urologi",
        "description":      "Infeksi pada bagian saluran kemih, bisa di kandung kemih (sistitis) atau ginjal (pielonefritis).",
        "emergency_signs":  ["Demam tinggi disertai nyeri pinggang", "Urin berdarah", "Nyeri sangat hebat"],
        "prevention":       ["Minum air putih cukup (8 gelas/hari)", "Jangan menahan BAK", "Jaga kebersihan area genital"],
    },
    "Hypertension": {
        "id":               "Hipertensi (Tekanan Darah Tinggi)",
        "specialist":       "Dokter Umum / Dokter Jantung",
        "description":      "Kondisi di mana tekanan darah secara konsisten di atas 140/90 mmHg. Sering disebut 'silent killer'.",
        "emergency_signs":  ["Sakit kepala hebat tiba-tiba", "Gangguan penglihatan", "Nyeri dada", "Tekanan darah > 180/120"],
        "prevention":       ["Kurangi garam", "Olahraga teratur", "Hindari rokok dan alkohol", "Kelola stres"],
    },
    "Type 2 Diabetes Mellitus": {
        "id":               "Diabetes Mellitus Tipe 2",
        "specialist":       "Dokter Penyakit Dalam / Endokrinologi",
        "description":      "Kondisi metabolik dengan kadar gula darah tinggi akibat resistensi insulin atau produksi insulin tidak cukup.",
        "emergency_signs":  ["Penurunan kesadaran", "Napas bau buah (ketoasidosis)", "Luka yang tidak sembuh-sembuh"],
        "prevention":       ["Diet sehat dan seimbang", "Olahraga rutin", "Kontrol berat badan", "Cek gula darah berkala"],
    },
    "Anemia": {
        "id":               "Anemia",
        "specialist":       "Dokter Penyakit Dalam / Hematologi",
        "description":      "Kondisi di mana tubuh kekurangan sel darah merah atau hemoglobin yang sehat untuk mengangkut oksigen.",
        "emergency_signs":  ["Sesak napas berat", "Nyeri dada", "Penurunan kesadaran", "Detak jantung sangat cepat"],
        "prevention":       ["Konsumsi makanan kaya zat besi", "Suplemen asam folat dan vitamin B12", "Cek darah rutin"],
    },
    "GERD": {
        "id":               "GERD (Asam Lambung Naik)",
        "specialist":       "Dokter Gastroenterologi",
        "description":      "Kondisi di mana asam lambung naik ke kerongkongan secara berulang, menyebabkan rasa terbakar.",
        "emergency_signs":  ["Muntah darah", "Nyeri dada yang tidak kunjung hilang", "Kesulitan menelan yang parah"],
        "prevention":       ["Makan porsi kecil tapi sering", "Hindari berbaring setelah makan", "Kurangi kafein dan makanan pedas"],
    },
    "Chickenpox": {
        "id":               "Cacar Air (Varisela)",
        "specialist":       "Dokter Umum / Dokter Anak",
        "description":      "Infeksi virus varicella-zoster yang sangat menular, menyebabkan ruam gatal berisi cairan.",
        "emergency_signs":  ["Lesi menyebar ke mata", "Demam > 39°C tidak turun", "Tanda infeksi bakteri sekunder", "Sesak napas"],
        "prevention":       ["Vaksinasi varisela", "Hindari kontak dengan penderita aktif"],
    },
    "Sinusitis": {
        "id":               "Sinusitis",
        "specialist":       "Dokter THT (Telinga Hidung Tenggorokan)",
        "description":      "Peradangan pada rongga sinus yang biasanya disebabkan infeksi virus atau bakteri setelah flu.",
        "emergency_signs":  ["Demam tinggi dengan nyeri wajah berat", "Pembengkakan sekitar mata", "Gangguan penglihatan"],
        "prevention":       ["Atasi alergi dan flu dengan cepat", "Gunakan humidifier", "Hindari paparan asap"],
    },
    "Conjunctivitis": {
        "id":               "Konjungtivitis (Mata Merah)",
        "specialist":       "Dokter Mata (Oftalmologi)",
        "description":      "Peradangan pada lapisan bening yang melapisi kelopak mata dan bola mata. Sangat menular jika karena infeksi.",
        "emergency_signs":  ["Nyeri mata hebat", "Penurunan tajam penglihatan", "Sangat sensitif cahaya"],
        "prevention":       ["Jangan sentuh mata dengan tangan kotor", "Jangan berbagi handuk/tetes mata", "Cuci tangan sering"],
    },
    "Acute Diarrhea": {
        "id":               "Diare Akut",
        "specialist":       "Dokter Umum / Gastroenterologi",
        "description":      "Buang air besar encer > 3 kali sehari yang berlangsung kurang dari 14 hari.",
        "emergency_signs":  ["Tidak BAK > 8 jam", "Mulut/kulit sangat kering", "Penurunan kesadaran", "Darah dalam feses"],
        "prevention":       ["Cuci tangan pakai sabun", "Konsumsi air matang", "Hindari makanan mentah di tempat tidak higienis"],
    },
}

# Default untuk penyakit yang tidak ada di database
_DEFAULT_INFO = {
    "id":               "Tidak Diketahui",
    "specialist":       "Dokter Umum",
    "description":      "Informasi detail penyakit ini belum tersedia di database kami.",
    "emergency_signs":  ["Sesak napas berat", "Penurunan kesadaran", "Perdarahan tidak terkontrol"],
    "prevention":       ["Konsultasikan ke dokter untuk informasi lebih lanjut"],
}


def get_disease_info(disease_name: str) -> dict:
    """
    Ambil informasi lengkap penyakit berdasarkan nama Inggrisnya.

    Args:
        disease_name: Nama penyakit hasil prediksi model (bahasa Inggris).

    Returns:
        Dict berisi: id, specialist, description, emergency_signs, prevention.
    """
    return _DISEASE_DB.get(disease_name, _DEFAULT_INFO)


__all__ = ["get_disease_info"]
