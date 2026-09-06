"""Google Flow - labs.google/fx/tools/flow -> Try -> login -> New Project -> Get Started -> Video->Images"""
import argparse, pathlib, sys, time, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from playwright.sync_api import sync_playwright
from src.config import get_launch_kwargs, SESSIONS_DIR, ensure_dirs

FLOW_URL = "https://labs.google/fx/tools/flow"
FLOW_URL = FLOW_URL.replace("@url:", "").replace("`", "").strip()
SESSION_FILE = SESSIONS_DIR / "google_flow.json"

def find_try_button(page):
    # ada 9 button yang sama di carousel, cuma 1 yang di viewport (x ~410)
    candidates = page.locator("button:has-text('Try in Google Flow'), a:has-text('Try in Google Flow')")
    n = candidates.count()
    for i in range(n):
        try:
            loc = candidates.nth(i)
            if loc.count()==0: continue
            if not loc.is_visible(): continue
            box = loc.bounding_box()
            if box and 0 <= box["x"] < 1800 and 0 <= box["y"] < 1500 and box["width"]>50:
                print(f"[pick] Try button {i} box {box}")
                return loc
        except: pass
    sels = [
        "button[aria-label='Create with Google Flow']",
        "button:has-text('Create with Google Flow')",
        "a:has-text('Try in Google Flow')",
        "a:has-text('Try Flow')",
        "button:has-text('Try in Google Flow')",
        "a:has-text('Try')",
        "a[href*='flow.google']",
        "a[href*='labs.google']",
    ]
    for sel in sels:
        try:
            loc = page.locator(sel).first
            if loc.count()>0 and loc.is_visible():
                print(f"[found] Try/Create button: {sel}")
                return loc
        except: pass
    return None

def find_create_button(page):
    for sel in ["button[aria-label='Create with Google Flow']", "button:has-text('Create with Google Flow')"]:
        try:
            loc=page.locator(sel).first
            if loc.count()>0 and loc.is_visible():
                print(f"[found] Create {sel}")
                return loc
        except: pass
    return None

def find_new_project(page):
    sels = [
        "button:has-text('New project')",
        "button:has-text('New Project')",
        "a:has-text('New project')",
        "[aria-label*='New project']",
    ]
    for sel in sels:
        try:
            loc = page.locator(sel).first
            if loc.count()>0:
                print(f"[found] New project: {sel} visible={loc.is_visible()}")
                return loc
        except: pass
    return None

def find_get_started(page):
    sels = [
        "button:has-text('Get started')",
        "button:has-text('Get Started')",
        "a:has-text('Get started')",
    ]
    for sel in sels:
        try:
            loc = page.locator(sel).first
            if loc.count()>0 and loc.is_visible():
                print(f"[found] Get started: {sel}")
                return loc
        except: pass
    return None

def switch_video_to_images(page):
    # bawah ada button Video ganti jadi Images
    # cari tab/button dengan teks Video
    candidates = [
        "button:has-text('Video')",
        "[role='tab']:has-text('Video')",
        "[role='button']:has-text('Video')",
        "button:has-text('Veo')",
    ]
    images_sel = [
        "button:has-text('Images')",
        "[role='tab']:has-text('Images')",
        "button:has-text('Image')",
        "text=Images",
    ]
    for vsel in candidates:
        try:
            vloc = page.locator(vsel).first
            if vloc.count()>0 and vloc.is_visible():
                print(f"[found] Video button: {vsel} -> klik")
                vloc.click()
                page.wait_for_timeout(1500)
                # coba klik Images
                for isel in images_sel:
                    try:
                        iloc = page.locator(isel).first
                        if iloc.count()>0 and iloc.is_visible():
                            print(f"[found] Images option: {isel} -> klik")
                            iloc.click()
                            page.wait_for_timeout(1000)
                            print("✅ Video -> Images berhasil")
                            return True
                    except: pass
                # jika tidak ada dropdown, coba cari element Images langsung
                print("[info] Video diklik, tapi opsi Images tidak ketemu - mungkin sudah toggle atau UI berbeda, cek manual")
                return False
        except Exception as e:
            print(f" try {vsel} err {e}")
    print("[warn] Tombol Video tidak ketemu - screenshot debug, cek manual di browser")
    try:
        page.screenshot(path=str(SESSIONS_DIR.parent / "debug" / "flow_video_not_found.png"))
    except: pass
    return False

def main(headless=False, keep_open=True):
    ensure_dirs()
    (SESSIONS_DIR.parent / "debug").mkdir(parents=True, exist_ok=True)
    print("=== Google Flow Automation ===")
    print(f"URL: {FLOW_URL}")
    print(f"Session: {SESSION_FILE} ({'ADA' if SESSION_FILE.exists() else 'BELUM ADA'})")
    launch_kwargs = get_launch_kwargs(headless=headless)
    print(f"headless={headless}")

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        ctx_kwargs = dict(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        if SESSION_FILE.exists():
            try:
                ctx_kwargs["storage_state"] = str(SESSION_FILE)
                print(f"[load] pakai session lama {SESSION_FILE}")
            except Exception as e:
                print(f"load session fail {e}")

        ctx = browser.new_context(**ctx_kwargs)
        page = ctx.new_page()

        print(f"[goto] {FLOW_URL}")
        try:
            page.goto(FLOW_URL, wait_until="commit", timeout=30000)
        except Exception as e:
            print(f"goto commit fail {e}, coba domcontentloaded")
            try: page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=30000)
            except Exception as e2: print(f"goto fail {e2}")
        page.wait_for_timeout(4000)
        print(f"Title: {page.title()}")
        print(f"URL: {page.url}")

        # 1. Klik Try in Google Flow - scroll dulu (y 2530->425)
        btn = find_try_button(page)
        if btn:
            print("[step 1] Klik Try in Google Flow...")
            try:
                btn.scroll_into_view_if_needed(); page.wait_for_timeout(900)
                box = btn.bounding_box()
                print(f"  box {box}")
                try:
                    btn.click(force=True, timeout=4000)
                    print("  force click OK")
                except Exception as e:
                    print(f"  force fail {e}")
                    if box:
                        page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
                    else:
                        page.evaluate("(el)=>el.click()", btn.element_handle())
                page.wait_for_timeout(3500)
                print(f"  -> URL setelah klik: {page.url}")
                if "labs.google" in page.url and "flow.google.com" not in page.url:
                    print("  -> fallback goto https://flow.google.com")
                    page.goto("https://flow.google.com", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3500)
                    print(f"  -> URL fallback: {page.url}")
                print(f"  -> Title: {page.title()}")
            except Exception as e:
                print(f"  klik Try fail {e}")
                try: page.evaluate("(el)=>el.click()", btn.element_handle())
                except: pass
                if "flow.google.com" not in page.url:
                    page.goto("https://flow.google.com", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)
        else:
            print("[warn] Tombol Try tidak ketemu - mungkin sudah redirect atau perlu scroll")
            # coba scroll
            try:
                page.evaluate("window.scrollTo(0, 400)")
                page.wait_for_timeout(1000)
                btn2 = find_try_button(page)
                if btn2:
                    btn2.click()
                    page.wait_for_timeout(3000)
            except: pass

        # 2. Tunggu login email
        print("\n" + "="*60)
        print(" SILAKAN LOGIN GOOGLE DI BROWSER YANG TERBUKA")
        print(" - Pakai email kamu (akun Google)")
        print(" - Selesaikan sampai masuk ke Google Flow (bisa lihat New Project)")
        print(" - Email/session akan disimpan otomatis ke data/sessions/google_flow.json")
        print("="*60)
        print("Setelah BERHASIL login & halaman Flow sudah kebuka, kembali ke terminal dan tekan ENTER...")
        try:
            input(">>> Tekan ENTER jika sudah login <<< ")
        except: 
            print("lanjut...")
            time.sleep(3)

        # simpan session setelah login
        try:
            ctx.storage_state(path=str(SESSION_FILE))
            print(f"[saved] Session Google disimpan: {SESSION_FILE} ({SESSION_FILE.stat().st_size} bytes)")
        except Exception as e:
            print(f"save session fail {e}")

        page.wait_for_timeout(3000)
        print(f"[after login] URL: {page.url}")
        print(f"[after login] Title: {page.title()}")

        # 3. Klik New Project
        print("\n[step 2] Cari New Project...")
        # tunggu agak lama biar flow load
        page.wait_for_timeout(3000)
        np = find_new_project(page)
        if np:
            print("  Klik New Project...")
            try:
                # scroll into view
                np.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                np.click()
                page.wait_for_timeout(3000)
                print(f"  -> URL: {page.url}")
            except Exception as e:
                print(f"  klik New Project fail {e} - coba force click")
                try: np.click(force=True)
                except: pass
        else:
            print("[warn] New Project tidak ketemu - mungkin sudah di dalam project atau selector beda. Cek browser manual, tekan ENTER untuk lanjut...")
            try: input("ENTER untuk lanjut ke Get Started...")
            except: pass

        # 4. Popup Get Started
        print("\n[step 3] Cari popup Get Started...")
        page.wait_for_timeout(2000)
        gs = find_get_started(page)
        if gs:
            print("  Klik Get Started...")
            try:
                gs.click()
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  klik Get Started fail {e}")
        else:
            print("[info] Get Started tidak muncul (mungkin sudah pernah klik)")

        # 5. Ganti Video -> Images
        print("\n[step 4] Ganti Video -> Images di bawah...")
        page.wait_for_timeout(2000)
        # scroll bawah
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
        except: pass
        ok = switch_video_to_images(page)
        if ok:
            print("✅ Flow selesai: Video sudah jadi Images")
        else:
            print("⚠️  Cek manual di browser — cari tab/button Video di bawah dan ganti ke Images, script sudah pause")

        # simpan session akhir
        try:
            ctx.storage_state(path=str(SESSION_FILE))
            print(f"[saved] Session akhir disimpan: {SESSION_FILE}")
        except: pass

        if keep_open:
            print("\n" + "="*60)
            print(" SELESAI - Browser tetap TERBUKA biar kamu cek")
            print(" Tutup browser manual jika sudah, atau tekan ENTER di terminal untuk close")
            print("="*60)
            try:
                input(">>> Tekan ENTER untuk tutup browser <<< ")
            except:
                print("tunggu 30 detik lalu auto close...")
                page.wait_for_timeout(30000)
        browser.close()
        print("Done.")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", default=False)
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    ap.add_argument("--keep-open", action="store_true", default=True)
    ap.add_argument("--no-keep-open", dest="keep_open", action="store_false")
    args=ap.parse_args()
    main(headless=args.headless, keep_open=args.keep_open)
