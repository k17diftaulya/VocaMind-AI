# Voice-Powered Smart Assistant (Prototype)

Prototype sistem pengenalan suara berbasis AI untuk mengelola jadwal, deadline,
tugas, ujian, catatan, dan organisasi secara otomatis dari perintah suara.

## Fitur

1. **Speech-to-Text** — Google Speech API (online), mendukung campuran
   Bahasa Indonesia & Inggris (coba `id-ID` dulu, fallback ke `en-US`).
2. **Deteksi Konteks** — rule-based keyword matching untuk kategori:
   `jadwal`, `deadline`, `tugas`, `ujian`, `catatan`, `organisasi`.
3. **Smart Schedule Generator** — otomatis membuat jadwal dari ucapan +
   **deteksi bentrok** (overlap check) dengan jadwal lain.
4. **Smart To-Do List Generator** — otomatis membuat tugas dengan
   **skor prioritas** dari kombinasi kedekatan deadline + urgensi + kategori.
5. **Study Planner** — otomatis membagi sesi belajar/pengerjaan dari
   sekarang sampai H-1 deadline (untuk kategori tugas/ujian).
6. **Recommender** — urutan pengerjaan tugas (berdasar skor prioritas)
   + saran slot waktu kosong untuk mengerjakannya.

## Instalasi

```bash
cd voice_assistant
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> Catatan: `PyAudio` kadang butuh dependency sistem tambahan.
> - **Windows**: biasanya langsung `pip install pyaudio` berhasil.
> - **macOS**: `brew install portaudio` sebelum `pip install pyaudio`.
> - **Linux (Debian/Ubuntu)**: `sudo apt install portaudio19-dev python3-pyaudio`
>   sebelum `pip install pyaudio`.

## Menjalankan

```bash
python main_gui.py
```

Aplikasi butuh **koneksi internet** karena speech-to-text memakai Google
Speech API (gratis, tanpa API key, tapi ada rate limit dari Google — cukup
untuk prototype/testing, bukan untuk skala produksi).

## Cara Pakai

1. Klik tombol **"🎙 Rekam & Proses"**, lalu ucapkan perintah. Contoh:
   - *"Tugas laporan praktikum deadline besok jam 5 sore, penting"*
   - *"Jadwal rapat organisasi hari senin jam 10 pagi durasi 2 jam"*
   - *"Ujian kalkulus tanggal 10 juli"*
   - *"Catatan beli buku baru"*
2. Kalau microphone belum siap / mau testing cepat tanpa suara, ketik
   teks manual di kolom **"Atau ketik manual"** lalu klik **"Proses Teks"**.
3. Cek tab **Jadwal**, **To-Do List**, **Study Plan**, dan **Rekomendasi**
   untuk melihat hasil otomatisasi.
4. Klik **"Generate Study Plan Otomatis"** di tab Study Plan untuk membuat
   sesi belajar dari semua tugas/ujian yang punya deadline.

## Struktur Proyek

```
voice_assistant/
├── main_gui.py                 # GUI utama (Tkinter)
├── requirements.txt
├── data/
│   └── assistant_data.json      # penyimpanan data (auto-generated)
└── modules/
    ├── speech_module.py          # speech-to-text (Google Speech API)
    ├── nlp_context.py             # deteksi konteks (rule-based)
    ├── entity_extractor.py         # ekstraksi tanggal/waktu/urgensi/judul
    ├── schedule_manager.py          # smart schedule + deteksi bentrok
    ├── todo_manager.py               # smart to-do + skor prioritas
    ├── study_planner.py               # study planner otomatis
    ├── recommender.py                  # urutan & saran waktu pengerjaan
    └── data_store.py                    # persistence JSON
```

## Keterbatasan Prototype & Saran Pengembangan Lanjutan

- **Deteksi konteks rule-based** cukup untuk prototype, tapi rentan salah
  kalau kalimat tidak memuat keyword yang terdaftar. Untuk versi lanjutan,
  bisa upgrade ke model NLP (mis. fine-tune IndoBERT / pakai LLM) supaya
  lebih robust terhadap variasi kalimat.
- **Ekstraksi tanggal** pakai `dateparser`, umumnya cukup baik untuk frasa
  umum ("besok", "senin depan", "10 juli"), tapi kalimat yang ambigu bisa
  salah tangkap — perlu konfirmasi ke user sebelum disimpan (bisa ditambah
  dialog konfirmasi di GUI).
- **Google Speech API** gratis tapi ada rate limit & butuh internet stabil.
  Untuk kebutuhan produksi/offline, bisa diganti ke Whisper atau Vosk.
- Rekomendasi waktu kosong saat ini masih sederhana (jam kerja 08:00-22:00
  tetap/hardcoded); bisa dikembangkan agar preferensi jam belajar/kerja
  pengguna bisa diatur sendiri.
