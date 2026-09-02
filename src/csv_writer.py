import csv, pathlib
from .models import JobPosting

HEADER = ["source","keyword","posted_date","scraped_at","title","company","location","country","salary","url","job_id","description_snippet"]

def write_csv(jobs, path):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # sort DESC by posted_date
    jobs_sorted = sorted(jobs, key=lambda j: j.posted_date, reverse=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for j in jobs_sorted:
            row = {k: getattr(j,k,"") for k in HEADER}
            w.writerow(row)
    print(f"Wrote {len(jobs_sorted)} rows to {p}")
    return p

def deduplicate(jobs):
    seen=set()
    out=[]
    for j in jobs:
        key=j.url.split("?")[0].lower().strip()
        if key not in seen:
            seen.add(key)
            out.append(j)
    return out
