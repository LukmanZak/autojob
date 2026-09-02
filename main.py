import asyncio, argparse, pathlib, datetime, re
from src.scrapers.disnakerja import scrape_disnakerja_sync
from src.scrapers.jobstreet import scrape_jobstreet_sync
from src.scrapers.glints import scrape_glints_sync
from src.csv_writer import write_csv, deduplicate
from src.models import JobPosting

RELEVANT_RE = re.compile(r"\bai\b|machine learning|\bmle\b|artificial intelligence|ml engineer", re.I)

def is_relevant(title):
    return bool(RELEVANT_RE.search(title))

def main(headless=True, strict=True):
    print("=== Step 1: Daily Job Scrape ===")
    print(f"headless={headless} strict={strict} at {datetime.datetime.now().isoformat()}")
    all_jobs=[]
    # Disnakerja - apply strict filter
    try:
        dj = scrape_disnakerja_sync(headless=headless)
        print(f"[disnakerja] raw {len(dj)}")
        if strict:
            dj_f = [j for j in dj if is_relevant(j.title)]
            print(f"[disnakerja] filtered relevant {len(dj_f)}/{len(dj)} (keeping filtered if >0 else raw fallback for debug)")
            # if filtered is 0, keep 5 sample raw but mark; better keep 0 to show no AI jobs on disnakerja
            dj = dj_f if len(dj_f)>0 else []
        all_jobs.extend(dj)
    except Exception as e:
        print(f"disnakerja fail {e}"); import traceback; traceback.print_exc()
    # JobStreet - already relevant via search, keep all
    try:
        js = scrape_jobstreet_sync(headless=headless)
        print(f"[jobstreet] raw {len(js)}")
        if strict:
            js_f = [j for j in js if is_relevant(j.title)]
            print(f"[jobstreet] filtered {len(js_f)}/{len(js)}")
            js = js_f if len(js_f)>0 else js
        # strict India exclude already in scraper, double-check
        js = [j for j in js if "india" not in j.country.lower() and "india" not in j.location.lower()]
        all_jobs.extend(js)
    except Exception as e:
        print(f"jobstreet fail {e}"); import traceback; traceback.print_exc()
    # Glints - strict filter (keyword param not working, so client filter)
    try:
        gl = scrape_glints_sync(headless=headless)
        print(f"[glints] raw {len(gl)}")
        if strict:
            gl_f = [j for j in gl if is_relevant(j.title)]
            print(f"[glints] filtered relevant {len(gl_f)}/{len(gl)}")
            gl = gl_f
        all_jobs.extend(gl)
    except Exception as e:
        print(f"glints fail {e}"); import traceback; traceback.print_exc()
    print(f"Total raw before dedup: {len(all_jobs)}")
    jobs = deduplicate(all_jobs)
    print(f"After dedup: {len(jobs)}")
    # sort DESC
    jobs_sorted = sorted(jobs, key=lambda j: (j.posted_date, j.scraped_at), reverse=True)
    out = pathlib.Path("F:/alpha/data/jobs.csv")
    write_csv(jobs_sorted, out)
    print(f"=== DONE: {len(jobs_sorted)} jobs saved to {out} ===")
    for j in jobs_sorted[:7]:
        print(f"  {j.source:10} | {j.posted_date} | {j.title[:70]:70} | {j.country:10} | {j.url[:80]}")
    if len(jobs_sorted)==0:
        print("WARNING: CSV empty - mungkin tidak ada lowongan AI/MLE hari ini")
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", default=True)
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    ap.add_argument("--no-strict", dest="strict", action="store_false")
    args=ap.parse_args()
    main(headless=args.headless, strict=args.strict)
