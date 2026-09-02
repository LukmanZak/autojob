# 🤖 AutoJob — Daily MLE & AI Engineer Hunter

> Scrape lowongan **Machine Learning & AI Engineer** otomatis tiap hari dari 3 portal, tanpa ribet. Hasil rapi di CSV, siap auto-lamar.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Playwright](https://img.shields.io/badge/Playwright-Stealth-green) ![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## ✨ Fitur

| Portal | Mode | Halaman | Filter |
|--------|------|---------|--------|
| **Disnakerja** | Latest Update (tanpa keyword) | 3 halaman × klik per-PT | **Semua job** (0 di-filter) → `jobs_disnakerja.csv` |
| **JobStreet** | SG + MY (4 configs) | 15/job per config | AI/MLE only, anti-India → `jobs.csv` |
| **Glints** | AI Engineer & MLE | LATEST sort | Client-side filter AI/MLE → `jobs.csv` |

- ✅ **Tanpa hardcode** — semua path di `src/config.py` (otomatis detect Windows/Docker)
- ✅ **Dedup + sort** — by `posted_date` & `scraped_at` DESC
- ✅ **Scheduler** — Windows Task, Linux cron, Hermes cron (07:00 daily)
- ✅ **Auto-Apply** — `dry-run` aman, `auto` pakai `data/applied.json` anti-double
- ✅ **Debug** — `debug/*.html` jika ke-block Cloudflare

---

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt
playwright install chromium

# 2. Config (optional)
cp .env.example .env
# isi kredensial jika mau auto-apply

# 3. Scrape
python main.py --headless

# Hasil
# data/jobs.csv              → 48 AI jobs (JobStreet strict)
# data/jobs_disnakerja.csv   → 56 semua posisi Latest Update (opsi B)
```

### Auto-Apply

```bash
# dry-run dulu (tidak benar-benar lamar)
python main.py --apply --mode dry-run --limit 3

# baru auto
python main.py --apply --mode auto --limit 5
# log: logs/apply_YYYY-MM-DD.log
# anti-double: data/applied.json
```

---

## 📁 Struktur

```
autojob/
├── main.py              # orkestrator (scrape → dedup → sort → CSV)
├── src/
│   ├── config.py        # single source path & env
│   ├── models.py        # JobPosting (12 kolom)
│   ├── csv_writer.py    # write_csv + dedup by URL
│   ├── cv_parser.py     # CV.pdf → data/cv_data.json (lokal, tidak di-push)
│   ├── scrapers/
│   │   ├── disnakerja.py  # Latest Update + klik per-PT + extract posisi
│   │   ├── jobstreet.py   # 4 configs SG/MY, anti-India
│   │   └── glints.py      # LATEST, filter client-side
│   ├── auth/            # storage_state per portal
│   └── apply/           # applier (dry-run/auto)
├── data/
│   ├── jobs.csv              # AI strict
│   └── jobs_disnakerja.csv   # semua posisi (opsi B)
├── scripts/
│   ├── run_daily.bat/sh      # scheduler harian
│   ├── setup_scheduler.ps1   # Windows Task
│   └── setup_cron.sh         # Linux cron
└── CV.pdf               # lokal saja (di-ignore)
```

---

## 🕒 Scheduler

### Windows
```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_scheduler.ps1
# → Task "AutoJobDailyScrape" daily 07:00
```

### Linux / Mac
```bash
chmod +x scripts/run_daily.sh scripts/setup_cron.sh
./scripts/setup_cron.sh
# 0 7 * * * cd /path/to/autojob && python3 main.py --headless
```

### Hermes
```bash
hermes cron create --schedule "every day at 07:00" --prompt "cd autojob && python main.py --headless"
```

---

## 🔧 Konfigurasi

Semua di `src/config.py` & `.env`:

```env
HEADLESS=true
# kosongkan = pakai Playwright default
PLAYWRIGHT_CHROME_PATH=C:/Users/.../chrome-win/chrome.exe

GLINTS_USER=
GLINTS_PASS=
JOBSTREET_USER=
JOBSTREET_PASS=
DISNAKERJA_USER=
DISNAKERJA_PASS=

APPLY_MODE=dry-run
APPLY_LIMIT=3
```

---

## 📊 Validasi

- Header 12 kolom: `source,keyword,posted_date,scraped_at,title,company,location,country,salary,url,job_id,description_snippet`
- `job_id` bersih tanpa `?/#`
- `country != India` (0 rows)
- Sorted DESC `posted_date`

---

## ⚠️ Catatan

- **CV tidak di-push** — `CV.pdf` & `data/cv_data.json` di `.gitignore` (privasi)
- Disnakerja sengaja **tanpa filter AI** (opsi B) → biar dapat semua Latest Update
- Glints keyword param diabaikan site → filter manual di code
- Auto-apply skeleton — isi selector tombol lamar per-portal di `src/apply/`

---

Made with ☕ for daily job hunting — `python main.py --headless` and go ☕
