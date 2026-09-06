"""Google Flow dengan folder gambar + AI advisor (vision) - sesi terekam."""
import argparse, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from playwright.sync_api import sync_playwright
from src.config import get_launch_kwargs, SESSIONS_DIR, ensure_dirs
from src.vision.flow_advisor import ensure_flow_session, save_step, advisor_click

FLOW_URL = "https://labs.google/fx/tools/flow"
# sanitize jika kepaste @url:`...`
FLOW_URL = FLOW_URL.replace("@url:", "").replace("`", "").strip()
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
            if box and 0 <= box["x"] < 1800 and 0 <= box["y"] < 1500 and box["width"]>50:
                print(f"[pick] Try button {i} box {box}")
                return loc
        except: pass
    # fallback: first visible
    for sel in ["button[aria-label='Create with Google Flow']", "button:has-text('Create with Google Flow')", "a:has-text('Try in Google Flow')","a:has-text('Try Flow')","button:has-text('Try in Google Flow')","a:has-text('Try')","a[href*='flow.google']"]:
        try:
            loc=page.locator(sel).first
            if loc.count()>0 and loc.is_visible(): 
                print(f"[fallback] Try/Create {sel}")
                return loc
        except: pass
    return None

def find_create_button(page):
    for sel in ["button[aria-label='Create with Google Flow']", "button:has-text('Create with Google Flow')", "a:has-text('Create with Google Flow')"]:
        try:
            loc=page.locator(sel).first
            if loc.count()>0 and loc.is_visible():
                print(f"[found] Create {sel}")
                return loc
        except: pass
    return None
def find_new_project(page):
    # selector presisi kamu: button dengan <span class="mat-focus-indicator"></span> + text New project
    for sel in [
        "button:has(span.mat-focus-indicator):has-text('New project')",
        "button:has(span.mat-focus-indicator):has-text('New Project')",
        "button:has-text('New project')",
        "button:has-text('New Project')",
        "a:has-text('New project')",
        "[aria-label*='New project']",
    ]:
        try:
            loc=page.locator(sel).first
            if loc.count()>0:
                # cek is_visible atau ada
                if loc.is_visible():
                    print(f"[found] New project {sel}")
                    return loc
                return loc
        except: pass
    return None
def find_get_started(page):
    # overlay <div class="click-blocker-overlay"> nutupin klik, tunggu hidden dulu
    for sel in ["button:has-text('Get started')","button:has-text('Get Started')"]:
        try:
            loc=page.locator(sel).first
            if loc.count()>0:
                # tunggu overlay hilang biar tidak intercepts pointer
                try:
                    page.wait_for_selector("div.click-blocker-overlay", state="hidden", timeout=4000)
                except: pass
                if loc.is_visible():
                    print(f"[found] Get started {sel}")
                    return loc
                # tetap return meski belum visible untuk force click
                return loc
        except: pass
    return None
def switch_video_to_images(page):
    # LOGIKA BARU: extract dulu semua, cari Videos, klik, extract lagi cari Images -> klik
    # Sesuai arahan: di videos ada apa aja -> cari mana Videos -> klik -> extract lagi -> cari Images -> klik
    print("[switch] extract Videos candidates...")
    try:
        # extract semua kandidat Video
        candidates = []
        # span settings-summary adalah video trigger utama
        for loc in page.locator("span.settings-summary, span[settingstriggercontent]").all():
            try:
                txt = loc.inner_text().strip()
                vis = loc.is_visible()
                candidates.append((loc, txt, vis))
                print(f"  candidate Video: '{txt[:40]}' vis={vis}")
            except: pass
        # fallback juga cek button Video
        for loc in page.locator("button:has-text('Video')").all():
            try:
                txt = loc.inner_text().strip()
                candidates.append((loc, txt, loc.is_visible()))
                print(f"  candidate Video btn: '{txt[:40]}'")
            except: pass
        # cari yang Videos (teks mengandung Video)
        target_video = None
        for loc, txt, vis in candidates:
            if "video" in txt.lower() and "720p" in txt.lower():
                target_video = loc
                print(f"[pick] Video -> '{txt[:50]}'")
                break
        if not target_video:
            # cari yang mengandung Video aja
            for loc, txt, vis in candidates:
                if "video" in txt.lower():
                    target_video = loc
                    print(f"[pick fallback] Video -> '{txt[:50]}'")
                    break
        if target_video:
            try: target_video.scroll_into_view_if_needed(); page.wait_for_timeout(400)
            except: pass
            try:
                target_video.click(force=True, timeout=3000)
                print("  Video clicked (force)")
            except:
                try: page.evaluate("(el)=>el.click()", target_video.element_handle())
                except: pass
            page.wait_for_timeout(1200)
        else:
            print("[warn] Videos tidak ketemu di extract")
            return False

        # extract lagi semua kandidat Images setelah klik Video (panel kebuka)
        print("[switch] extract Images candidates setelah klik Video...")
        page.wait_for_timeout(600)
        img_candidates = []
        for loc in page.locator("button[role='radio'], span.toggle-text, button:has-text('Image'), [role='radio']").all():
            try:
                txt = loc.inner_text().strip()
                if not txt: continue
                img_candidates.append((loc, txt, loc.is_visible()))
                print(f"  candidate Image: '{txt[:40]}' vis={loc.is_visible()} tag={loc.evaluate('el=>el.tagName')}")
            except: pass
        # cari Images
        target_img = None
        for loc, txt, vis in img_candidates:
            if txt.lower().strip() == "image":
                target_img = loc
                print(f"[pick] Image -> '{txt}'")
                break
        if not target_img:
            for loc, txt, vis in img_candidates:
                if "image" in txt.lower():
                    target_img = loc
                    print(f"[pick fallback] Image -> '{txt}'")
                    break
        if target_img:
            try: target_img.scroll_into_view_if_needed(); page.wait_for_timeout(300)
            except: pass
            try:
                target_img.click(force=True, timeout=3000, no_wait_after=True)
                print("  Image clicked (force)")
            except:
                try: page.evaluate("(el)=>el.click()", target_img.element_handle())
                except:
                    box = target_img.bounding_box()
                    if box: page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
            page.wait_for_timeout(800)
            # cek aria-checked pada parent button jika span
            try:
                btn = target_img
                # jika span toggle-text, ambil parent button
                if "toggle-text" in target_img.evaluate("el=>el.outerHTML").lower():
                    btn = page.locator("button:has(span.toggle-text:has-text('Image'))").first
                chk = btn.get_attribute("aria-checked")
                print(f"  aria-checked={chk}")
            except: pass
            print("✅ Video -> Images berhasil (extract logic)")
            return True
        else:
            print("[warn] Images tidak ketemu setelah extract")
            return False
    except Exception as e:
        print(f"video->images extract err {e}")
        import traceback; traceback.print_exc()
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
        has_session = SESSION_FILE.exists()
        if has_session:
            try: ctx_kwargs["storage_state"]=str(SESSION_FILE); print(f"[load] session {SESSION_FILE} -> auto-skip login ENTER")
            except: pass
        # viewport native kamu 1280x720 biar tidak kepotong taskbar
        ctx=browser.new_context(viewport={"width": 1280, "height": 720}, **ctx_kwargs)
        page=ctx.new_page()
        # set window sesuai layar
        try: page.set_viewport_size({"width": 1280, "height": 720})
        except: pass
        # 0 home - pakai commit biar tidak timeout domcontentloaded di labs.google
        print(f"[goto] {FLOW_URL}")
        try:
            page.goto(FLOW_URL, wait_until="commit", timeout=30000)
        except Exception as e:
            print(f"goto commit fail {e}, coba domcontentloaded")
            try: page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=30000)
            except Exception as e2: print(f"goto fail {e2}")
        page.wait_for_timeout(3500)
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
            print("[warn] Try tidak ketemu, langsung goto flow.google.com")
            page.goto("https://flow.google.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            advisor_click(page, folder, "02_try_not_found_goto", "Try tidak ketemu, sudah goto flow.google.com/about")
        # 1b. Di flow.google.com/about klik Create with Google Flow (selector kamu)
        create_btn=find_create_button(page)
        if create_btn:
            print("[step 1b] Klik Create with Google Flow...")
            try:
                create_btn.scroll_into_view_if_needed(); page.wait_for_timeout(600)
                box2=create_btn.bounding_box()
                print(f"  create box {box2}")
                # no_wait_after biar tidak timeout nunggu navigasi login
                try:
                    create_btn.click(force=True, timeout=4000, no_wait_after=True)
                except:
                    # fallback: mouse atau JS
                    if box2:
                        page.mouse.click(box2["x"]+box2["width"]/2, box2["y"]+box2["height"]/2)
                    else:
                        page.evaluate("(el)=>el.click()", create_btn.element_handle())
                print("  -> Create clicked (no_wait)")
                page.wait_for_timeout(4000)
                print(f"  -> URL after Create: {page.url}")
            except Exception as e:
                print(f"  Create click fail {e}")
                try:
                    page.evaluate("(el)=>el.click()", create_btn.element_handle())
                    page.wait_for_timeout(3000)
                except: pass
            advisor_click(page, folder, "02b_after_create", "Setelah klik Create with Google Flow, seharusnya muncul login Google. Tunggu login?")
        else:
            print("[info] Create button tidak ketemu di about (mungkin sudah login)") 
            advisor_click(page, folder, "02b_create_not_found", "Create button tidak ketemu, cek apakah sudah di login/dashboard")
        # 2 login - auto-skip jika sudah ada session
        if has_session:
            print("\n[auto] Sudah ada session google_flow.json -> skip ENTER, lanjut...")
            page.wait_for_timeout(1500)
        else:
            print("\n>>> LOGIN GOOGLE MANUAL DI BROWSER - setelah login tekan ENTER <<<")
            print(f"Folder gambar: {folder} - screenshot akan terus diambil")
            try: input("ENTER jika sudah login >> ")
            except: time.sleep(3)
        ctx.storage_state(path=str(SESSION_FILE))
        advisor_click(page, folder, "03_after_login", "User sudah login Google. Cari 'New Project' - dimana?")
        page.wait_for_timeout(2500)
        # 3 New Project - pakai full viewport screenshot biar tidak kepotong
        np=find_new_project(page)
        if np:
            try:
                np.scroll_into_view_if_needed(); page.wait_for_timeout(500)
                # pastikan tidak kepotong bawah - scroll sedikit ke atas
                page.evaluate("window.scrollBy(0, -100)")
                page.wait_for_timeout(300)
                np.click(force=True); page.wait_for_timeout(3000)
                print("  -> New Project clicked")
            except Exception as e:
                print(f"  New Project click fail {e}")
                try: page.evaluate("(el)=>el.click()", np.element_handle())
                except: pass
            advisor_click(page, folder, "04_new_project_clicked", "Sudah klik New Project. Cari popup 'Get Started'")
        else:
            advisor_click(page, folder, "04_new_project_not_found", "Tombol New Project tidak ketemu - dimana?")
            if not has_session:
                try: input("Klik New Project manual lalu ENTER >> ")
                except: pass
            else:
                print("[auto] skip manual New Project (sudah login)")
                page.wait_for_timeout(1000)
        # 4 Get Started - handle overlay click-blocker
        gs=find_get_started(page)
        if gs:
            try:
                # overlay bisa nutupin, tunggu hidden atau force JS
                gs.scroll_into_view_if_needed(); page.wait_for_timeout(400)
                try:
                    # tunggu overlay hilang
                    page.wait_for_selector("div.click-blocker-overlay", state="hidden", timeout=3000)
                except: pass
                try:
                    gs.click(force=True, timeout=3000, no_wait_after=True)
                    print("  -> Get Started clicked (force)")
                except:
                    page.evaluate("(el)=>el.click()", gs.element_handle())
                    print("  -> Get Started JS clicked")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Get Started fail {e}, coba JS")
                try: page.evaluate("(el)=>el.click()", gs.element_handle())
                except: pass
                page.wait_for_timeout(1500)
            advisor_click(page, folder, "05_get_started_clicked", "Sudah klik Get Started. Cari area bawah tombol Video -> Images")
        else:
            advisor_click(page, folder, "05_get_started_not_found", "Popup Get Started tidak muncul (mungkin sudah pernah, cek overlay hidden)")
        # 5 Video -> Images - pastikan bottom input bar kelihatan (jangan kepotong)
        # scroll ke input bar "What do you want to create?" biar Video·720p kelihatan
        try:
            bottom = page.locator("text='What do you want to create?'").first
            if bottom.count()>0:
                bottom.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                # jangan scroll terlalu bawah, biar Video button tetap di viewport tengah-bawah
                page.evaluate("window.scrollBy(0, 80)")
                page.wait_for_timeout(400)
            else:
                # fallback: scroll ke settings-summary
                vloc_tmp = page.locator("span.settings-summary:has-text('Video')").first
                if vloc_tmp.count()>0:
                    vloc_tmp.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    page.evaluate("window.scrollBy(0, -120)")
                else:
                    page.evaluate("window.scrollBy(0, 300)")
        except:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight - 600)")
        page.wait_for_timeout(600)
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
