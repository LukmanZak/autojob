"""Central config - single source of truth untuk semua path & env."""
import os
import pathlib
from dotenv import load_dotenv

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
if not (PROJECT_ROOT / ".env").exists() and (PROJECT_ROOT.parent / ".env").exists():
    load_dotenv(PROJECT_ROOT.parent / ".env")

DATA_DIR = PROJECT_ROOT / "data"
DEBUG_DIR = PROJECT_ROOT / "debug"
LOGS_DIR = PROJECT_ROOT / "logs"
SESSIONS_DIR = PROJECT_ROOT / "data" / "sessions"

CV_PDF = PROJECT_ROOT / "CV.pdf"
CV_JSON = DATA_DIR / "cv_data.json"
JOBS_CSV = DATA_DIR / "jobs.csv"
JOBS_FULL_CSV = DATA_DIR / "jobs_full.csv"
JOBS_DISNAKERJA_CSV = DATA_DIR / "jobs_disnakerja.csv"
APPLIED_JSON = DATA_DIR / "applied.json"

def _detect_chrome():
    env_path = os.getenv("PLAYWRIGHT_CHROME_PATH", "").strip()
    if env_path:
        return env_path
    candidates = [
        pathlib.Path("C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"),
        pathlib.Path.home() / "AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe",
        pathlib.Path("/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"),
        pathlib.Path("/root/.cache/ms-playwright/chromium-1187/chrome-linux/chrome"),
        pathlib.Path("/ms-playwright/chromium-1234/chrome-linux64/chrome"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None

PLAYWRIGHT_CHROME_PATH = _detect_chrome()
HEADLESS = os.getenv("HEADLESS", "true").lower() not in ("0", "false", "no")
APPLY_MODE = os.getenv("APPLY_MODE", "dry-run")
APPLY_LIMIT = int(os.getenv("APPLY_LIMIT", "3"))

def ensure_dirs():
    for d in [DATA_DIR, DEBUG_DIR, LOGS_DIR, SESSIONS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def get_launch_kwargs(headless=True):
    kwargs = dict(headless=headless, args=["--no-sandbox","--disable-blink-features=AutomationControlled","--disable-gpu"])
    if PLAYWRIGHT_CHROME_PATH:
        kwargs["executable_path"] = PLAYWRIGHT_CHROME_PATH
    return kwargs
