import argparse, datetime, re
from src.scrapers.disnakerja import scrape_disnakerja_sync
from src.scrapers.jobstreet import scrape_jobstreet_sync
from src.scrapers.glints import scrape_glints_sync
from src.csv_writer import write_csv, deduplicate
from src.config import JOBS_CSV, JOBS_DISNAKERJA_CSV, ensure_dirs

RELEVANT_RE = re.compile(r"\bai\b|machine learning|\bmle\b|artificial intelligence|ml engineer", re.I)

def is_relevant(title):
    return bool(RELEVANT_RE.search(title))

def main(headless=True, strict=True, do_apply=False, apply_mode="dry-run", apply_limit=3):
    print("=== Step 1: Daily Job Scrape ===")
    print(f"headless={headless} strict={strict} at {datetime.datetime.now().isoformat()}")
    ensure_dirs()
    # --- Disnakerja OPSI B: tanpa filter, langsung Latest Update, simpan terpisah ---
    print("\n--- Disnakerja (Latest Update, tanpa filter AI) ---")
    try:
        dj = scrape_disnakerja_sync(headless=headless)
        print(f"[disnakerja] raw {len(dj)} (semua posisi, non-AI juga)")
        # simpan khusus disnakerja
        dj_sorted = sorted(dj, key=lambda j: (j.posted_date, j.scraped_at), reverse=True)
        write_csv(dj_sorted, JOBS_DISNAKERJA_CSV)
        print(f"[disnakerja] saved {len(dj_sorted)} to {JOBS_DISNAKERJA_CSV}")
        for j in dj_sorted[:3]:
            print(f"  disnakerja | {j.posted_date} | {j.title[:60]:60} | {j.company[:30]}")
    except Exception as e:
        print(f"disnakerja fail {e}"); import traceback; traceback.print_exc()
        dj=[]
    # --- JobStreet & Glints tetap strict ---
    all_jobs=[]
    # untuk CSV utama, Disnakerja TIDAK ikut jika strict (opsi B: pisah)
    # jika --no-strict maka gabung semua
    if not strict:
        all_jobs.extend(dj)
        print(f"[main] non-strict: Disnakerja {len(dj)} digabung ke jobs.csv")

    try:
        js = scrape_jobstreet_sync(headless=headless)
        print(f"\n[jobstreet] raw {len(js)}")
        if strict:
            js_f = [j for j in js if is_relevant(j.title)]
            print(f"[jobstreet] filtered {len(js_f)}/{len(js)}")
            js = js_f if len(js_f)>0 else js
        js = [j for j in js if "india" not in j.country.lower() and "india" not in j.location.lower()]
        all_jobs.extend(js)
    except Exception as e:
        print(f"jobstreet fail {e}"); import traceback; traceback.print_exc()
    try:
        gl = scrape_glints_sync(headless=headless)
        print(f"\n[glints] raw {len(gl)}")
        if strict:
            gl_f = [j for j in gl if is_relevant(j.title)]
            print(f"[glints] filtered relevant {len(gl_f)}/{len(gl)}")
            gl = gl_f
        all_jobs.extend(gl)
    except Exception as e:
        print(f"glints fail {e}"); import traceback; traceback.print_exc()
    print(f"\nTotal untuk jobs.csv (strict AI only): {len(all_jobs)}")
    jobs = deduplicate(all_jobs)
    print(f"After dedup: {len(jobs)}")
    jobs_sorted = sorted(jobs, key=lambda j: (j.posted_date, j.scraped_at), reverse=True)
    write_csv(jobs_sorted, JOBS_CSV)
    print(f"=== DONE: {len(jobs_sorted)} jobs saved to {JOBS_CSV} ===")
    print(f"=== DONE: {len(dj)} disnakerja jobs saved to {JOBS_DISNAKERJA_CSV} (opsi B pisah) ===")
    for j in jobs_sorted[:5]:
        print(f"  {j.source:10} | {j.posted_date} | {j.title[:60]:60} | {j.country}")

    if do_apply:
        print(f"\n=== Step 2: Auto Apply (mode={apply_mode} limit={apply_limit}) ===")
        try:
            from src.apply.applier import run_apply
            run_apply(csv_path=JOBS_CSV, mode=apply_mode, limit=apply_limit, headless=headless)
        except Exception as e:
            print(f"apply fail {e}"); import traceback; traceback.print_exc()
    return JOBS_CSV

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", default=True)
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    ap.add_argument("--no-strict", dest="strict", action="store_false")
    ap.add_argument("--apply", action="store_true", help="jalankan auto-apply setelah scrape")
    ap.add_argument("--mode", choices=["dry-run","auto"], default="dry-run", help="mode apply")
    ap.add_argument("--limit", type=int, default=3, help="max lowongan yang dilamar per run")
    args=ap.parse_args()
    main(headless=args.headless, strict=args.strict, do_apply=args.apply, apply_mode=args.mode, apply_limit=args.limit)
