"""Auto-apply skeleton - dry-run aman, auto mode butuh kredensial."""
import csv, json, pathlib, datetime
from src.config import APPLIED_JSON, LOGS_DIR, ensure_dirs
from src.auth.base import session_path

def load_jobs(csv_path, limit=3):
    jobs=[]
    with open(csv_path, newline="", encoding="utf-8") as f:
        r=csv.DictReader(f)
        for row in r:
            jobs.append(row)
            if len(jobs) >= limit:
                break
    return jobs

def load_applied():
    if APPLIED_JSON.exists():
        try:
            return set(json.loads(APPLIED_JSON.read_text(encoding="utf-8")))
        except: return set()
    return set()

def save_applied(urls: set):
    ensure_dirs()
    APPLIED_JSON.write_text(json.dumps(sorted(urls), indent=2, ensure_ascii=False), encoding="utf-8")

def run_apply(csv_path, mode="dry-run", limit=3, headless=True):
    ensure_dirs()
    csv_path = pathlib.Path(csv_path)
    if not csv_path.exists():
        print(f"[apply] CSV tidak ada: {csv_path}")
        return
    jobs = load_jobs(csv_path, limit=limit)
    applied = load_applied()
    log_path = LOGS_DIR / f"apply_{datetime.date.today().isoformat()}.log"
    print(f"[apply] mode={mode} limit={limit} jobs={len(jobs)} already_applied={len(applied)}")
    print(f"[apply] log -> {log_path}")

    new_applied = set(applied)
    for j in jobs:
        url=j.get("url","")
        title=j.get("title","")
        company=j.get("company","")
        source=j.get("source","")
        key=url.split("?")[0].lower().strip()
        if key in applied:
            print(f"  SKIP sudah dilamar: {title[:60]}")
            continue
        if mode=="dry-run":
            print(f"  [DRY-RUN] would apply: [{source}] {title} @ {company} -> {url}")
            # jangan tandai applied di dry-run, biar bisa diulang
        else:
            # TODO: implement playwright auto-apply per source
            # contoh: buka url, cek tombol Lamar/Apply, isi form dari CV, submit
            # untuk sekarang hanya log dan tandai
            print(f"  [AUTO] applying: [{source}] {title} -> {url}")
            print(f"    (skeleton: butuh login {source} & selector tombol apply)")
            # simulasikan sukses - di implementasi nanti ganti dengan hasil real
            new_applied.add(key)
        # tulis log
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"{datetime.datetime.now().isoformat()} | {mode} | {source} | {title} | {url}\n")

    if mode!="dry-run" and new_applied != applied:
        save_applied(new_applied)
        print(f"[apply] saved {len(new_applied)} applied URLs to {APPLIED_JSON}")
    print("[apply] done")
