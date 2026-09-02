# Alpha Daily Job Automation

## Ringkasan
Scrape daily lowongan **MLE & AI Engineer** dari 3 portal:
- **disnakerja.com** (`?s=AI+Engineer` paginated)
- **JobStreet** luar negeri kecuali India (SG + MY, 4 search configs, filter country != India)
- **Glints** (filtered client-side karena keyword param diabaikan site)

Output: `data/jobs.csv` terurut **terbaru DESC** (`posted_date` + `scraped_at`), dedup by URL, tanpa India.

## Cara pakai
```bat
# install
uv pip install -r requirements.txt

# scrape strict (hanya MLE/AI, default)
python main.py --headless

# scrape full (semua lowongan tanpa filter relevance, untuk debug)
python main.py --no-strict --headless

# output
data/jobs.csv          # strict 51 rows (JobStreet relevant) - default benar
data/jobs_full.csv     # full 123 rows (semua portals, termasuk SALES Glints & PAM JAYA Disnakerja)
data/jobs_strict_final.csv # backup strict
```

## Validasi CSV (debugging loop)
- Header 12 kolom: source,keyword,posted_date,scraped_at,title,company,location,country,salary,url,job_id,description_snippet
- `job_id` bersih tanpa `?`/`#` (split)
- `country` tidak ada India (0 rows)
- `title` semua mengandung AI/MLE/Machine Learning (strict)
- URL https valid (curl -I 200)
- Sorted DESC by posted_date

## Scheduler harian
- `scripts/run_daily.bat` untuk Windows Task Scheduler (trigger daily 07:00)
- Atau Hermes cron: `hermes cron create --schedule "every day at 07:00" --prompt "cd F:/alpha && python main.py --headless"`

## CV source
- `F:/alpha/CV.pdf` -> `data/cv_data.json` via `python src/cv_parser.py`

## Step 2 (next)
Auto-login + auto-lamar belum dijalankan (butuh kredensial Glints/JobStreet/Disnakerja). Skeleton ada di `src/auth/` & `src/apply/`.
Jalankan dry-run dulu:
```bat
python main.py --apply --mode dry-run --limit 3
```
