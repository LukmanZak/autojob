"""Buka tldraw.com, tunggu login manual, lalu simpan storage state."""
import pathlib
import sys

# Jalankan file ini langsung dari root project:
# python src/auth/tldraw/login.py
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

from src.config import SESSIONS_DIR, ensure_dirs, get_launch_kwargs

TLDRAW_URL = "https://www.tldraw.com/"
TLDRAW_SESSION_DIR = SESSIONS_DIR / "tldraw"
TLDRAW_SESSION_FILE = TLDRAW_SESSION_DIR / "tldraw.json"


def main():
    """Buka browser headed dan simpan session setelah user selesai login."""
    ensure_dirs()
    TLDRAW_SESSION_DIR.mkdir(parents=True, exist_ok=True)

    print("=== tldraw Manual Login ===")
    print(f"URL: {TLDRAW_URL}")
    print(f"Session akan disimpan ke: {TLDRAW_SESSION_FILE}")
    if TLDRAW_SESSION_FILE.exists():
        print("[info] Session tldraw lama akan ditimpa setelah login selesai.")

    # Sengaja selalu headed: user perlu menyelesaikan login di browser yang terlihat.
    launch_kwargs = get_launch_kwargs(headless=False)
    print("[open] Membuka browser headed...")

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        try:
            try:
                page.goto(TLDRAW_URL, wait_until="domcontentloaded", timeout=45_000)
            except Exception as exc:
                # Aplikasi SPA bisa tetap usable walaupun domcontentloaded timeout.
                print(f"[warn] Navigasi belum selesai, browser tetap dibuka: {exc}")
            page.wait_for_timeout(3_000)
            print(f"[page] Title: {page.title()}")
            print(f"[page] URL: {page.url}")

            print("\n" + "=" * 60)
            print(" SILAKAN LOGIN tldraw DI BROWSER YANG TERBUKA")
            print(" - Selesaikan seluruh proses login sampai akun sudah masuk")
            print(" - Jangan tutup browser sebelum session disimpan")
            print(" - Script belum melakukan automation tldraw lain")
            print("=" * 60)
            input("\n>>> Jika login sudah selesai, tekan ENTER untuk menyimpan session <<< ")

            context.storage_state(path=str(TLDRAW_SESSION_FILE))
            if not TLDRAW_SESSION_FILE.exists():
                raise RuntimeError("Storage state tidak terbentuk")
            size = TLDRAW_SESSION_FILE.stat().st_size
            if size == 0:
                raise RuntimeError("Storage state terbentuk tetapi kosong")
            print(f"[saved] Session tldraw tersimpan: {TLDRAW_SESSION_FILE} ({size} bytes)")
            print("[done] Tidak ada automation lanjutan.")
        finally:
            browser.close()
            print("[closed] Browser ditutup setelah session tersimpan.")


if __name__ == "__main__":
    main()
