"""Google Flow dengan folder gambar + AI advisor (vision) - sesi terekam."""
import argparse, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from playwright.sync_api import sync_playwright
from src.config import get_launch_kwargs, SESSIONS_DIR, ensure_dirs
from src.vision.flow_advisor import ensure_flow_session, save_step, advisor_click

FLOW_URL = "https://labs.google/fx/tools/flow"
SESSION_FILE = SESSIONS_DIR / "google_flow.json"

def find_try_button(page):
    # ada 9 button yang sama di carousel, cuma 1 yang di viewport (x ~410)
    # pilih yang bounding_box di dalam viewport
    candidates = page.locator("button:has-text('Try in Google Flow'), a:has-text('Try in Google Flow')")
    n = candidates.count()
    for i in range(n):
        try:
            loc = candidates.nth(i)
            if loc.count()==0: continue
            if not loc.is_visible(): continue
            box = loc.bounding_box()
            if box and 0 <= box["x"] < 1800 and 0 <= box["y"] < 1200 and box["width"]>50:
                print(f"[pick] Try button {i} box {box}")
                return loc
        except: pass
    # fallback: first visible
    for sel in ["a:has-text('Try in Google Flow')","a:has-text('Try Flow')","button:has-text('Try in Google Flow')","a:has-text('Try')","a[href*='flow.google']"]:
        try:
            loc=page.locator(sel).first
            if loc.count()>0 and loc.is_visible(): return loc
        except: pass
    return None
def find_new_project(page):
    for sel in ["button:has-text('New project')","button:has-text('New Project')","a:has-text('New project')"]:
        try:
            loc=page.locator(sel).first
            if loc.count()>0: return loc
        except: pass
    return None
def find_get_started(page):
    for sel in ["button:has-text('Get started')","button:has-text('Get Started')"]:
        try:
            loc=page.locator(sel).first
            if loc.count()>0 and loc.is_visible(): return loc
        except: pass
    return None
def switch_video_to_images(page):
    for vsel in ["button:has-text('Video')","[role='tab']:has-text('Video')"]:
        try:
            vloc=page.locator(vsel).first
            if vloc.count()>0 and vloc.is_visible():
                vloc.click(); page.wait_for_timeout(1200)
                for isel in ["button:has-text('Images')","[role='tab']:has-text('Images')","text=Images"]:
                    try:
                        iloc=page.locator(isel).first
                        if iloc.count()>0 and iloc.is_visible():
                            iloc.click(); page.wait_for_timeout(800); return True
                    except: pass
                return False
        except: pass
    return False

def main(headless=False):
    ensure_dirs()
    folder = ensure_flow_session()
    print(f"=== Google Flow Vision ({folder.name}) ===")
    print(f"Images folder: {folder}")
    launch_kwargs = get_launch_kwargs(headless=headless)
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch_kwargs)
        ctx_kwargs=dict(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36", locale="en-US")
        if SESSION_FILE.exists():
            try: ctx_kwargs["storage_state"]=str(SESSION_FILE); print(f"[load] session {SESSION_FILE}")
            except: pass
        ctx=browser.new_context(**ctx_kwargs)
        page=ctx.new_page()
        # 0 home
        print(f"[goto] {FLOW_URL}"); page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=60000); page.wait_for_timeout(3500)
        advisor_click(page, folder, "01_home", "Cari tombol 'Try in Google Flow' - dimana? Return koordinat klik.")
        # 1 Try - scroll dulu biar viewport kena (y 2530 -> 425)
        btn=find_try_button(page)
        if btn:
            try:
                print(f"[step 1] Klik Try in Google Flow...")
                btn.scroll_into_view_if_needed(); page.wait_for_timeout(900)
                box = btn.bounding_box()
                print(f"  box after scroll {box}")
                try:
                    btn.click(force=True, timeout=4000)
                    print("  -> force click OK")
                except Exception as e:
                    print(f"  force fail {e}, fallback mouse")
                    if box:
                        page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
                    else:
                        page.evaluate("(el)=>el.click()", btn.element_handle())
                page.wait_for_timeout(3500)
                print(f"  -> URL after click: {page.url}")
                # jika tidak navigasi (masih labs), fallback direct goto flow.google.com
                if "labs.google" in page.url and "flow.google.com" not in page.url:
                    print("  -> Try tidak navigasi, fallback goto https://flow.google.com")
                    page.goto("https://flow.google.com", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3500)
                    print(f"  -> URL fallback: {page.url}")
            except Exception as e:
                print(f"[warn] klik Try gagal {e}, coba JS click + fallback goto")
                try: page.evaluate("(el)=>el.click()", btn.element_handle())
                except: pass
                page.wait_for_timeout(2500)
                if "flow.google.com" not in page.url:
                    page.goto("https://flow.google.com", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)
            advisor_click(page, folder, "02_after_try", "Setelah klik Try (atau fallback goto flow.google.com), cek apakah sudah di flow.google.com/about. Apa next step login?")
        else:
            print("[warn] Try tidak ketemu"); advisor_click(page, folder, "02_try_not_found", "Try button tidak ketemu, dimana?")
        # 2 login
        print("\n>>> LOGIN GOOGLE MANUAL DI BROWSER - setelah login tekan ENTER <<<")
        print(f"Folder gambar: {folder} - screenshot akan terus diambil")
        try: input("ENTER jika sudah login >> ")
        except: time.sleep(3)
        ctx.storage_state(path=str(SESSION_FILE))
        advisor_click(page, folder, "03_after_login", "User sudah login Google. Cari 'New Project' - dimana?")
        page.wait_for_timeout(2500)
        # 3 New Project
        np=find_new_project(page)
        if np:
            try: np.scroll_into_view_if_needed(); page.wait_for_timeout(400); np.click(); page.wait_for_timeout(3000)
            except: pass
            advisor_click(page, folder, "04_new_project_clicked", "Sudah klik New Project. Cari popup 'Get Started'")
        else:
            advisor_click(page, folder, "04_new_project_not_found", "Tombol New Project tidak ketemu - dimana?")
            try: input("Klik New Project manual lalu ENTER >> ")
            except: pass
        # 4 Get Started
        gs=find_get_started(page)
        if gs:
            gs.click(); page.wait_for_timeout(2000)
            advisor_click(page, folder, "05_get_started_clicked", "Sudah klik Get Started. Cari area bawah tombol Video -> Images")
        else:
            advisor_click(page, folder, "05_get_started_not_found", "Popup Get Started tidak muncul")
        # 5 Video -> Images
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(800)
        advisor_click(page, folder, "06_before_video_switch", "Di bawah ada tombol Video yang harus diganti jadi Images - tunjuk koordinat Video")
        ok=switch_video_to_images(page)
        advisor_click(page, folder, "07_after_video_switch", "Setelah switch Video->Images, apakah sudah jadi Images? Jika belum, dimana tombol Images?")
        if ok: print("✅ Video -> Images OK")
        else: print("⚠️  Cek manual Video->Images di browser")
        ctx.storage_state(path=str(SESSION_FILE))
        print(f"\n=== SELESAI ===")
        print(f"Folder: {folder}")
        print(f"File: {list(folder.glob('*'))}")
        print(f"Session: {SESSION_FILE}")
        print("Kirim folder ini ke AI: AI baca steps.json + lihat png untuk tau sesi & next click")
        try: input("ENTER untuk tutup browser >> ")
        except: page.wait_for_timeout(15000)
        browser.close()

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", default=False)
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    args=ap.parse_args()
    main(headless=args.headless)
