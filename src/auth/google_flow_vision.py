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
    # LOGIKA BARU: extract loop sampai Video muncul, baru cari Images
    # Sesuai arahan: run terus sampai bisa klik Images, log extract tiap iterasi
    print("[switch] polling Videos candidates sampai muncul...")
    target_video = None
    for attempt in range(6):  # 6 x 1.5s = 9s polling
        candidates = []
        for loc in page.locator("span.settings-summary, span[settingstriggercontent]").all():
            try:
                txt = loc.inner_text().strip()
                if txt:
                    candidates.append((loc, txt, loc.is_visible()))
                    print(f"  candidate Video ({attempt}): '{txt[:60]}' vis={loc.is_visible()}")
            except: pass
        for loc in page.locator("button:has-text('Video')").all():
            try:
                txt = loc.inner_text().strip()
                if txt: candidates.append((loc, txt, loc.is_visible()))
            except: pass
        # cari Videos
        for loc, txt, vis in candidates:
            if "video" in txt.lower() and "720p" in txt.lower():
                target_video = loc
                print(f"[pick] Video ({attempt}) -> '{txt[:60]}'")
                break
        if target_video: break
        for loc, txt, vis in candidates:
            if "video" in txt.lower():
                target_video = loc
                print(f"[pick fallback] Video ({attempt}) -> '{txt[:60]}'")
                break
        if target_video: break
        print(f"  Videos belum muncul, tunggu 1.5s ({attempt+1}/6)")
        page.wait_for_timeout(1500)
        # coba scroll sedikit biar trigger render
        try: page.evaluate("window.scrollBy(0, 100)")
        except: pass
        try:
            page.wait_for_selector("span.settings-summary:has-text('Video')", timeout=1500)
            print("  wait_for_selector Video found")
        except: pass

    if not target_video:
        print("[warn] Videos tidak ketemu setelah polling")
        # log semua text di page untuk debug
        try:
            all_text = page.locator("body").inner_text()
            print(f"  body snippet: {all_text[:500].replace(chr(10),' ')}")
        except: pass
        return False

    try: target_video.scroll_into_view_if_needed(); page.wait_for_timeout(400)
    except: pass
    try:
        target_video.click(force=True, timeout=3000)
        print("  Video clicked (force)")
    except:
        try: page.evaluate("(el)=>el.click()", target_video.element_handle())
        except: pass
    page.wait_for_timeout(1500)

    # extract Images dengan polling juga
    print("[switch] polling Images candidates setelah klik Video...")
    target_img = None
    for attempt in range(5):
        img_candidates = []
        for loc in page.locator("button[role='radio'], span.toggle-text, button:has-text('Image'), [role='radio']").all():
            try:
                txt = loc.inner_text().strip()
                if not txt: continue
                img_candidates.append((loc, txt, loc.is_visible()))
                print(f"  candidate Image ({attempt}): '{txt[:40]}' vis={loc.is_visible()} id={loc.get_attribute('id')}")
            except: pass
        for loc, txt, vis in img_candidates:
            if txt.lower().strip() == "image":
                target_img = loc
                print(f"[pick] Image ({attempt}) -> '{txt}'")
                break
        if not target_img:
            for loc, txt, vis in img_candidates:
                if "image" in txt.lower():
                    target_img = loc
                    print(f"[pick fallback] Image ({attempt}) -> '{txt}'")
                    break
        if target_img: break
        print(f"  Images belum muncul, tunggu 1s ({attempt+1}/5)")
        page.wait_for_timeout(1000)

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
        try:
            btn = target_img
            if "toggle-text" in target_img.evaluate("el=>el.outerHTML").lower():
                btn = page.locator("button:has(span.toggle-text:has-text('Image'))").first
            chk = btn.get_attribute("aria-checked")
            print(f"  aria-checked={chk}")
        except: pass
        print("✅ Video -> Images berhasil (polling extract)")
        return True
    else:
        print("[warn] Images tidak ketemu setelah polling")
        return False

def fill_prompt(page, prompt_text: str):
    """Isi fill 'What do you want to create?' dengan prompt lalu Enter"""
    print(f"[fill] isi prompt: '{prompt_text[:60]}'")
    # cari input fill
    sels = [
        "textarea[placeholder*='What do you want to create']",
        "input[placeholder*='What do you want to create']",
        "textarea[placeholder*='What do you want']",
        "input[placeholder*='What do you want']",
        "div[contenteditable='true']",
        "textarea[placeholder*='create']",
    ]
    fill_loc = None
    for sel in sels:
        try:
            loc = page.locator(sel).first
            if loc.count()>0:
                print(f"[found] fill {sel} vis={loc.is_visible()}")
                fill_loc = loc
                break
        except: pass
    # fallback text
    if not fill_loc:
        try:
            loc = page.locator("text='What do you want to create?'").first
            # parentnya adalah input
            # coba cari sibling textarea
            parent = page.locator("textarea, input, div[contenteditable]").first
            if parent.count()>0:
                fill_loc = parent
                print(f"[fallback] fill via generic textarea/input")
        except: pass
    if not fill_loc:
        print("[warn] fill input tidak ketemu")
        return False
    try:
        fill_loc.scroll_into_view_if_needed(); page.wait_for_timeout(400)
        fill_loc.click(force=True); page.wait_for_timeout(300)
        # isi prompt
        try:
            fill_loc.fill(prompt_text)
        except:
            # contenteditable
            fill_loc.evaluate(f"(el)=>el.textContent=`{prompt_text}`")
            fill_loc.evaluate("(el)=>el.dispatchEvent(new Event('input',{bubbles:true}))")
        print(f"  filled '{prompt_text[:40]}'")
        page.wait_for_timeout(500)
        # tekan Enter atau klik tombol arrow kirim
        try:
            fill_loc.press("Enter")
            print("  pressed Enter")
        except: pass
        # coba klik tombol kirim (arrow)
        for sel in ["button:has(mat-icon:has-text('arrow_forward'))", "button:has-text('→')", "button[aria-label*='Send']", "button:has(mat-icon)"]:
            try:
                btn = page.locator(sel).first
                if btn.count()>0 and btn.is_visible():
                    btn.click(force=True, timeout=2000)
                    print(f"  clicked send {sel}")
                    break
            except: pass
        page.wait_for_timeout(1500)
        print("✅ Fill prompt done")
        return True
    except Exception as e:
        print(f"fill fail {e}")
        import traceback; traceback.print_exc()
        return False

def download_results(page, result_dir: pathlib.Path, folder: pathlib.Path):
    """Tunggu 2 image muncul, klik titik tiga per image -> Download -> 1K -> save ke result image/"""
    import pathlib as _pl
    result_dir = _pl.Path(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    print(f"[download] tunggu 2 image generate di {page.url}")
    # polling sampai image muncul (max 120s)
    for attempt in range(24):  # 24 x 5s = 120s
        # cari image hasil - Flow biasanya img dengan src blob atau cards
        img_candidates = page.locator("img").all()
        # filter yang besar (result)
        big_imgs = []
        for im in img_candidates:
            try:
                box = im.bounding_box()
                if box and box["width"] > 200 and box["height"] > 200:
                    big_imgs.append(im)
            except: pass
        print(f"  attempt {attempt+1}/24: big_imgs={len(big_imgs)}")
        if len(big_imgs) >= 2:
            print(f"  ✅ 2 image terdeteksi")
            break
        # juga cek text/loading
        try:
            if page.locator("text='Generating'").count()>0:
                print("  Generating...")
        except: pass
        page.wait_for_timeout(5000)
    else:
        print("[warn] 2 image tidak muncul setelah 120s, screenshot cek")
        try: page.screenshot(path=str(folder / "10_before_download.png"), full_page=True)
        except: pass
        return False

    # cari tombol titik tiga per image
    # Flow: tiap image card ada button dengan mat-icon more_vert / more_horiz atau aria-label More
    print("[download] cari titik tiga per image...")
    # extract semua more buttons
    more_sels = [
        "button:has(mat-icon:has-text('more_vert'))",
        "button:has(mat-icon:has-text('more_horiz'))",
        "button[aria-label*='More']",
        "button:has-text('⋮')",
    ]
    more_btns = []
    for sel in more_sels:
        for loc in page.locator(sel).all():
            try:
                if loc.is_visible():
                    more_btns.append(loc)
            except: pass
    print(f"  more buttons found: {len(more_btns)}")
    # jika tidak ketemu via more_vert, coba cari via image card container
    if len(more_btns) < 2:
        # coba cari semua button di dekat img
        for loc in page.locator("button").all():
            try:
                txt = loc.inner_text()
                if "more" in loc.evaluate("el=>el.outerHTML").lower():
                    more_btns.append(loc)
            except: pass
        print(f"  after fallback more buttons: {len(more_btns)}")

    # download 2 image
    downloaded = 0
    for idx, more_btn in enumerate(more_btns[:2]):
        try:
            print(f"[download] image {idx+1} klik titik tiga...")
            more_btn.scroll_into_view_if_needed(); page.wait_for_timeout(400)
            more_btn.click(force=True, timeout=3000)
            page.wait_for_timeout(800)
            # di menu, klik Download
            dl_btn = None
            for sel in ["text='Download'", "button:has-text('Download')", "a:has-text('Download')", "[role='menuitem']:has-text('Download')"]:
                loc = page.locator(sel).first
                if loc.count()>0 and loc.is_visible():
                    dl_btn = loc
                    print(f"  found Download {sel}")
                    break
            if not dl_btn:
                print("  Download tidak ketemu, coba page.locator text Download")
                continue
            dl_btn.click(force=True, timeout=3000)
            page.wait_for_timeout(800)
            # pilih 1K (bukan 2K)
            one_k = None
            for sel in ["text='1K'", "button:has-text('1K')", "[role='menuitem']:has-text('1K')", "text='1k'"]:
                loc = page.locator(sel).first
                if loc.count()>0:
                    one_k = loc
                    print(f"  found 1K {sel} vis={loc.is_visible()}")
                    break
            if one_k:
                # handle download via expect_download
                try:
                    with page.expect_download(timeout=15000) as dl_info:
                        one_k.click(force=True, timeout=3000)
                    download = dl_info.value
                    save_path = result_dir / f"result_{idx+1}_1K.png"
                    # jika ada pilihan nama, pakai suggest
                    download.save_as(str(save_path))
                    print(f"  ✅ downloaded {save_path} ({save_path.stat().st_size} bytes)")
                    downloaded += 1
                except Exception as e:
                    print(f"  download expect fail {e}, coba click biasa")
                    try:
                        one_k.click(force=True)
                        page.wait_for_timeout(3000)
                        # fallback: cek downloads folder browser?
                    except: pass
            else:
                print("  1K tidak ketemu, coba klik Download langsung (mungkin default 1K)")
                # jika tidak ada pilihan 1K, download langsung
            page.wait_for_timeout(1000)
            # tutup menu jika masih terbuka (klik elsewhere)
            try: page.keyboard.press("Escape")
            except: pass
            page.wait_for_timeout(500)
        except Exception as e:
            print(f"  download image {idx+1} fail {e}")
            import traceback; traceback.print_exc()

    print(f"[download] selesai {downloaded}/2 ke {result_dir}")
    try:
        page.screenshot(path=str(folder / "11_after_download.png"), full_page=True)
    except: pass
    return downloaded > 0

def main(headless=False, prompt_text: str = "Buatkan logo untuk edukasi."):
    ensure_dirs()
    folder = ensure_flow_session()
    print(f"=== Google Flow Vision ({folder.name}) ===")
    print(f"Images folder: {folder}")
    print(f"Prompt: {prompt_text}")
    launch_kwargs = get_launch_kwargs(headless=headless)
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch_kwargs)
        ctx_kwargs=dict(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36", locale="en-US")
        has_session = SESSION_FILE.exists()
        if has_session:
            try: ctx_kwargs["storage_state"]=str(SESSION_FILE); print(f"[load] session {SESSION_FILE} -> auto-skip login ENTER")
            except: pass
        # viewport native kamu 1280x720 biar tidak kepotong taskbar
        ctx=browser.new_context(viewport={"width": 1280, "height": 720}, accept_downloads=True, **ctx_kwargs)
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
        # 6 Fill prompt + Enter
        print(f"\n[step 6] Fill prompt '{prompt_text}' -> Images mode")
        filled = fill_prompt(page, prompt_text)
        advisor_click(page, folder, "08_after_fill", f"Sudah isi fill dengan '{prompt_text[:40]}' dan Enter. Apakah generate mulai?")
        if filled:
            print("✅ Fill prompt + Enter done")
            page.wait_for_timeout(2500)
            advisor_click(page, folder, "09_generating", "Setelah Enter, cek apakah loading/generating muncul")
        # 7 Download 2 image via titik tiga -> 1K ke result image/
        print(f"\n[step 7] Download 2 image (titik tiga -> Download -> 1K) ke result image/")
        result_dir = pathlib.Path("F:/alpha/result image")
        try:
            ok_dl = download_results(page, result_dir, folder)
            if ok_dl:
                print(f"✅ Download selesai -> {result_dir}")
                advisor_click(page, folder, "10_download_done", f"Download 2 image 1K ke {result_dir} selesai")
            else:
                print("⚠️ Download belum berhasil, cek manual titik tiga -> 1K")
                advisor_click(page, folder, "10_download_fail", "Download gagal, cek manual")
        except Exception as e:
            print(f"download step fail {e}")
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
    ap.add_argument("--prompt", default="Buatkan logo untuk edukasi.", help="prompt untuk fill What do you want to create?")
    args=ap.parse_args()
    main(headless=args.headless, prompt_text=args.prompt)
