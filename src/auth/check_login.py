"""Check login status - buka browser biar kelihatan sudah login atau belum."""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from playwright.sync_api import sync_playwright
from src.config import get_launch_kwargs, SESSIONS_DIR

def is_logged_in(page):
    for sel in [
        "[data-automation='profileMenu']",
        "a:has-text('MyJobStreet')",
        "img[alt*='avatar']",
        "[data-testid='header-profile']",
    ]:
        try:
            if page.locator(sel).count() > 0:
                return True, sel
        except: pass
    try:
        if page.locator("a:has-text('Keluar'), a:has-text('Logout')").count() > 0:
            return True, "logout link"
    except: pass
    return False, ""

def main(source="jobstreet", show=False, headless=None):
    # headless None -> auto: show=True berarti headed
    if headless is None:
        headless = not show
    session = SESSIONS_DIR / f"{source}.json"
    print(f"=== Check login: {source} ===")
    print(f"Session file: {session} -> {'ADA' if session.exists() else 'BELUM ADA'}")
    if session.exists():
        print(f"Size: {session.stat().st_size} bytes")
    launch_kwargs = get_launch_kwargs(headless=headless)
    print(f"Launch: headless={headless} {launch_kwargs.get('executable_path','')}")
    url = "https://id.jobstreet.com/id/login" if source=="jobstreet" else "https://id.jobstreet.com/"
    if source=="jobstreet":
        url = "https://id.jobstreet.com/"
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        # pakai session jika ada
        ctx_kwargs = dict(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="id-ID"
        )
        if session.exists():
            ctx_kwargs["storage_state"] = str(session)
            print(f"[load] pakai session {session}")
        else:
            print("[info] tanpa session (belum login)")
        ctx = browser.new_context(**ctx_kwargs)
        page = ctx.new_page()
        print(f"[goto] {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000)
        print(f"Title: {page.title()}")
        print(f"URL: {page.url}")
        logged, sel = is_logged_in(page)
        if logged:
            print(f"✅ SUDAH LOGIN (deteksi: {sel})")
        else:
            print("❌ BELUM LOGIN — akan redirect ke /id/login atau tombol Masuk masih muncul")
            # cek tombol Masuk masih ada?
            try:
                if page.locator("a:has-text('Masuk'), a:has-text('Sign In')").count()>0:
                    print("  -> Tombol 'Masuk' masih terlihat")
            except: pass
        if show:
            print("\nBrowser terbuka 15 detik — cek avatar pojok kanan atas. Tutup manual atau tunggu auto-close...")
            page.wait_for_timeout(15000)
        browser.close()
    print("Done. Jika BELUM: python src/auth/jobstreet_login.py --no-headless")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source", default="jobstreet")
    ap.add_argument("--show", action="store_true", help="buka browser kelihatan")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    ap.set_defaults(headless=None)
    args=ap.parse_args()
    # jika --show tanpa headless flag, pakai headed
    show = args.show
    headless = args.headless
    if show and headless is None:
        headless=False
    main(source=args.source, show=show, headless=headless)
