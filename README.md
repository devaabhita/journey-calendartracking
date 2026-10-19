# 🧭 Journey Tracker

Aplikasi to-do list berbasis **perjalanan (journey)**. Bukan sekadar mencatat kegiatan, tetapi juga melacak perkembangan menuju target besar melalui checklist interaktif, pelacak waktu, streak harian, heatmap aktivitas, dan rekapitulasi statistik otomatis.

---

## 📌 Konsep Utama

```
Journey (tujuan besar, mis: "Mastering Python & AI 3 Bulan")
  └── Task (kegiatan + tanggal + jam + prioritas + kategori)
        └── Checklist (selesai / belum + repeat rule)
              └── Rekap & Statistik (harian, mingguan, bulanan, streak, heatmap)
```

---

## ✨ Fitur Lengkap

### MVP (Fase 1)
- [x] **CRUD Journey**: Buat, lihat, ubah, dan hapus Journey (target besar, deskripsi, tanggal mulai, target selesai).
- [x] **CRUD Task**: Tambah kegiatan harian dengan tanggal, jam mulai & selesai, kategori, dan tingkat prioritas (Tinggi, Sedang, Rendah).
- [x] **Checklist Interaktif**: Centang atau batal centang kegiatan secara real-time dengan animasi strikethrough dan pencatatan `done_at`.
- [x] **Penyimpanan Database**: Mendukung **MySQL** (database: `todolist`, user: `root`, port: 3306) dengan auto-create database otomatis dan graceful fallback ke SQLite lokal jika MySQL belum aktif.
- [x] **Rekapitulasi Progres**: Persentase progres per journey dan per periode (Mingguan/Bulanan).

### Fase 2 & Ekstra
- [x] **Task Berulang (Repeating Tasks)**: Mendukung aturan `daily` (harian) dan `weekly` (mingguan) yang otomatis menjadwalkan task berikutnya saat ditandai selesai.
- [x] **Streak System**: Melacak streak harian berjalan (`current_streak`), streak terpanjang (`longest_streak`), serta mempertahankan status jika dikerjakan hari ini atau kemarin.
- [x] **Heatmap Aktivitas**: Tampilan grid ala GitHub 60 hari terakhir dengan visualisasi intensitas kegiatan dan filter instan saat kotak tanggal diklik.
- [x] **Catatan Harian & Mood Tracker**: Pilihan mood emoji (1 😞 s.d. 5 🤩), jurnal harian, dan riwayat refleksi.
- [x] **Filter & Pencarian**: Filter tanggal, pencarian judul real-time, filter journey, kategori, dan status (Semua / Belum Selesai / Selesai).
- [x] **Visualisasi Grafik**: Chart.js interaktif untuk perbandingan tugas selesai vs total dan distribusi kategori kegiatan.

---

## 🛠️ Tech Stack

| Bagian | Teknologi | Alasan |
|---|---|---|
| **Bahasa** | Python 3.11+ / 3.14 | Fleksibel, modern, dan ekosistem kaya |
| **Backend** | FastAPI | Cepat, async, otomatis membuat dokumentasi OpenAPI & Swagger UI |
| **Database** | MySQL / SQLite fallback | Didukung dengan koneksi SQLAlchemy + PyMySQL |
| **ORM** | SQLAlchemy 2.0 | Akses database yang aman dan modular |
| **Validasi** | Pydantic v2 | Validasi skema request dan response otomatis |
| **Frontend** | Vanilla HTML5 + CSS3 + Modern JavaScript + Chart.js | UI modern bertema gelap, glassmorphism, responsif, dan ringan tanpa build step |
| **Testing** | pytest + httpx | Pengujian unit test untuk logika formula statistik dan endpoint API |

---

## 📁 Struktur Proyek

```
journey-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py            # Titik masuk FastAPI & static mount
│   ├── database.py        # Koneksi database (MySQL auto-create + SQLite fallback)
│   ├── models.py          # Definisi tabel (SQLAlchemy)
│   ├── schemas.py         # Skema request & response (Pydantic)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── journeys.py    # Endpoint CRUD Journey & progres
│   │   ├── tasks.py       # Endpoint Task, checklist toggle & repeat rule
│   │   ├── stats.py       # Endpoint rekapitulasi, streak, heatmap
│   │   └── notes.py       # Endpoint refleksi harian & mood tracker
│   └── services/
│       ├── __init__.py
│       └── stats.py       # Logika hitung progres, jam fokus, streak, konsistensi
├── frontend/
│   ├── index.html         # Antarmuka dashboard
│   ├── style.css          # Desain sistem modern, dark-mode & glassmorphism
│   └── app.js             # Logika interaksi, Chart.js, filter & modal
├── tests/
│   ├── __init__.py
│   ├── test_stats.py      # Tes formula progres, jam fokus, dan streak
│   └── test_tasks.py      # Tes integrasi endpoint API (FastAPI TestClient)
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

---

## 🚀 Panduan Menjalankan

### 1. Masuk ke direktori & aktifkan virtual environment

```bash
# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Pasang dependensi (jika baru kloning)

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Database (MySQL)

Pastikan layanan MySQL (Laragon / XAMPP / MySQL Service) sudah berjalan pada port `3306`.
Secara default, aplikasi akan:
1. Terhubung ke `localhost:3306` user `root` (tanpa password).
2. Menjalankan `CREATE DATABASE IF NOT EXISTS todolist` secara otomatis jika database belum ada.
3. Membuat tabel `journeys`, `tasks`, dan `daily_notes` otomatis via SQLAlchemy.
4. Jika MySQL tidak berjalan, aplikasi akan memberikan pemberitahuan dan otomatis menggunakan SQLite lokal (`journey_tracker.db`) sehingga aplikasi tetap bisa langsung dicoba!

Untuk mengubah konfigurasi MySQL, salin `.env.example` ke `.env`:
```env
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sesuaikan dengan nama database
```

### 4. Jalankan Server FastAPI

```bash
python -m uvicorn app.main:app --reload --port 8000
```

- **Aplikasi Web**: Buka [http://localhost:8000](http://localhost:8000) pada browser.
- **Dokumentasi API Interaktif (Swagger UI)**: Buka [http://localhost:8000/docs](http://localhost:8000/docs).
- **Dokumentasi ReDoc**: Buka [http://localhost:8000/redoc](http://localhost:8000/redoc).

---

## 🧪 Menjalankan Tes Otomatis

Untuk memastikan semua formula matematika progres, perhitungan jam fokus, kalkulasi streak, dan endpoint API berfungsi dengan akurat:

```bash
.\venv\Scripts\pytest -v
```

Hasil tes:
```
tests/test_stats.py::test_calculate_progress PASSED
tests/test_stats.py::test_calculate_focus_hours PASSED
tests/test_stats.py::test_calculate_streaks PASSED
tests/test_tasks.py::test_journey_crud PASSED
tests/test_tasks.py::test_task_creation_and_toggle PASSED
tests/test_tasks.py::test_stats_summary_endpoint PASSED
============================== 6 passed ==============================
```

---

## 📊 Rumus Perhitungan Rekap

- **Progres Journey (%)** = $\frac{\text{Task Selesai}}{\text{Total Task}} \times 100\%$
- **Total Jam Fokus** = $\sum (\text{Jam Selesai} - \text{Jam Mulai})$ pada seluruh task berstatus selesai
- **Streak Aktif** = Jumlah hari beruntun dengan minimal 1 task selesai (memiliki toleransi ke hari kemarin jika hari ini baru dimulai)
- **Konsistensi Mingguan (%)** = $\frac{\text{Hari Aktif}}{7} \times 100\%$

---

## 📄 Lisensi

Proyek ini dirilis di bawah lisensi [MIT](LICENSE).
