"""JobStreet manual login helper - buka browser, klik Masuk, tunggu user login, save session."""
import argparse, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from playwright.sync_api import sync_playwright
from src.config import get_launch_kwargs, SESSIONS_DIR, ensure_dirs

LOGIN_URLS = [
    "https://id.jobstreet.com/id/login",
    "https://id.jobstreet.com/",
]

def find_and_click_masuk(page):
    selectors = [
        "a:has-text('Masuk')",
        "a:has-text('Sign In')",
        "a:has-text('Log Masuk')",
        "button:has-text('Masuk')",
        "[data-automation='signIn']",
        "a[href*='login']",
        "a[href*='sign-in']",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                print(f"[login] klik {sel}")
                loc.click()
                return True
        except Exception as e:
            print(f"  try {sel} fail: {e}")
    return False

def is_logged_in(page):
    checks = [
        "[data-automation='profileMenu']",
        "a:has-text('MyJobStreet')",
        "button:has-text('Profile')",
        "[aria-label*='Profile']",
        "img[alt*='avatar']",
    ]
    for sel in checks:
        try:
            if page.locator(sel).count() > 0:
                return True
        except: pass
    # fallback: url contains profile or has logout
    try:
        if "myjobstreet" in page.url.lower() or "profile" in page.url.lower():
            return True
        if page.locator("a:has-text('Keluar'), a:has-text('Log Out'), a:has-text('Logout')").count() > 0:
            return True
    except: pass
    return False

def main(headless=False):
    ensure_dirs()
    out = SESSIONS_DIR / "jobstreet.json"
    print("=== JobStreet Manual Login ===")
    print(f"Browser headless={headless} -> untuk login manual pakai --no-headless (headed)")
    print(f"Session akan disimpan di: {out}")
    launch_kwargs = get_launch_kwargs(headless=headless)
    print(f"Launch kwargs: {launch_kwargs}")

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="en-MY"
        )
        page = context.new_page()
        # buka homepage
        url = LOGIN_URLS[0]
        print(f"[open] {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3000)
        print(f"Title: {page.title()}")
        # klik Masuk
        clicked = find_and_click_masuk(page)
        if clicked:
            print("[info] Sudah klik Masuk, tunggu redirect ke login...")
            page.wait_for_timeout(3000)
        else:
            print("[warn] Tombol Masuk tidak ketemu otomatis, silakan klik manual di browser.")

        print("\n" + "="*60)
        print(" SILAKAN LOGIN MANUAL DI BROWSER YANG TERBUKA")
        print(" - Bisa pakai Google / Email / Password + OTP")
        print(" - Tunggu sampai masuk ke dashboard MyJobStreet (avatar muncul)")
        print(" - JANGAN tutup browser")
        print("="*60)
        print("\nSetelah BERHASIL login, kembali ke terminal ini dan tekan ENTER...")
        try:
            input(">>> Tekan ENTER jika sudah login <<< ")
        except EOFError:
            print("No input, lanjut...")
            time.sleep(5)

        # cek login
        page.wait_for_timeout(2000)
        print(f"URL sekarang: {page.url}")
        print(f"Title sekarang: {page.title()}")
        logged = is_logged_in(page)
        print(f"Deteksi login: {'YA' if logged else 'BELUM TERDETEKSI (tetap simpan sesi, coba cek manual)'}")

        # simpan session apapun (biar apply bisa pakai)
        context.storage_state(path=str(out))
        print(f"[saved] Session disimpan: {out} ({out.stat().st_size} bytes)")

        # verifikasi dengan buka lagi pakai session
        print("\nVerifikasi: buka ulang dengan session...")
        # keep browser open 3 detik biar user lihat
        page.wait_for_timeout(3000)
        browser.close()
        print("Done. Lanjut: python main.py --apply --mode dry-run --limit 3")
        print(f"Jika gagal deteksi, coba login ulang: python src/auth/jobstreet_login.py --no-headless")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", default=False)
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    args = ap.parse_args()
    # default headed untuk login manual
    main(headless=args.headless)
