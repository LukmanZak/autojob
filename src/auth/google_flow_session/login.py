"""Bootstrap session Google Flow melalui login manual di browser headed."""
import pathlib
import sys

# Jalankan dari root project:
# python src/auth/google_flow_session/login.py
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

from src.config import SESSIONS_DIR, ensure_dirs, get_launch_kwargs

FLOW_URL = "https://flow.google.com/?pli=1"
SESSION_FILE = SESSIONS_DIR / "google_flow.json"


def main():
    """Buka Google Flow, tunggu login manual, lalu simpan storage state."""
    ensure_dirs()
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("=== Google Flow Manual Login ===")
    print(f"URL: {FLOW_URL}")
    print(f"Session akan disimpan ke: {SESSION_FILE}")
    if SESSION_FILE.exists():
        print("[info] Session Google Flow lama akan ditimpa setelah login selesai.")

    # Jangan memakai session lama di bootstrap ini; user diminta login ulang
    # secara manual lalu hasilnya disimpan sebagai session baru.
    launch_kwargs = get_launch_kwargs(headless=False)
    print("[open] Membuka browser headed...")

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        try:
            try:
                page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=60_000)
            except Exception as exc:
                # SPA/login redirect tetap bisa dilanjutkan dari browser yang terbuka.
                print(f"[warn] Navigasi belum selesai, browser tetap dibuka: {exc}")
            page.wait_for_timeout(5_000)
            print(f"[page] Title: {page.title()}")
            print(f"[page] URL: {page.url}")

            # Login Google Flow baru benar-benar dipakai setelah CTA ini
            # membawa browser dari landing page ke aplikasi Flow.
            create = page.locator("button[aria-label='Create with Google Flow']").first
            if create.count() == 0:
                create = page.locator("button:has-text('Create with Google Flow')").first
            if create.count() > 0 and create.is_visible():
                create.scroll_into_view_if_needed()
                create.click(force=True, no_wait_after=True)
                page.wait_for_timeout(5_000)
                print(f"[create] URL setelah Create: {page.url}")
            else:
                print("[warn] Tombol Create with Google Flow tidak ditemukan")

            print("\n" + "=" * 60)
            print(" SILAKAN LOGIN GOOGLE FLOW DI BROWSER YANG TERBUKA")
            print(" - Jika muncul account chooser, pilih akun lalu selesaikan login")
            print(" - Selesaikan sampai terlihat New project atau editor Google Flow")
            print(" - Jangan tutup browser sebelum session disimpan")
            print(" - Runner ini tidak membuat project atau generate gambar")
            print("=" * 60)
            input("\n>>> Jika login sudah selesai, tekan ENTER untuk menyimpan session <<< ")

            page.wait_for_timeout(1_500)
            body = " ".join(page.locator("body").inner_text().split())
            flow_ready = (
                "/project/" in page.url
                or "New project" in body
                or page.locator("button:has-text('New project'), a:has-text('New project')").count() > 0
            )
            if not flow_ready:
                raise RuntimeError(
                    "Login belum sampai aplikasi Google Flow; "
                    f"session tidak disimpan. URL sekarang: {page.url}"
                )

            context.storage_state(path=str(SESSION_FILE))
            if not SESSION_FILE.exists():
                raise RuntimeError("Storage state tidak terbentuk")
            size = SESSION_FILE.stat().st_size
            if size == 0:
                raise RuntimeError("Storage state terbentuk tetapi kosong")
            print(f"[saved] Session Google Flow tersimpan: {SESSION_FILE} ({size} bytes)")
            print("[done] Belum ada automation generation yang dijalankan.")
        finally:
            browser.close()
            print("[closed] Browser ditutup setelah session tersimpan.")


if __name__ == "__main__":
    main()
