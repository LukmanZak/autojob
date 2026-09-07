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
    # Flow hides the Image/Video radios inside Settings. Open that panel
    # before extracting them; a project may already reopen in Image mode.
    settings_trigger = page.locator("button[aria-label='Settings trigger']").first
    try:
        page.wait_for_selector("button[aria-label='Settings trigger']", state="visible", timeout=10000)
    except Exception:
        pass
    if settings_trigger.count() > 0:
        try:
            settings_trigger.click(force=True)
            page.wait_for_timeout(500)
            for loc in page.locator("button[role='radio']").all():
                if not loc.is_visible():
                    continue
                text = " ".join(loc.inner_text().split())
                if text.endswith("Image") and loc.get_attribute("aria-checked") == "true":
                    print("[switch] Image sudah aktif; settings terbuka untuk ratio/count")
                    return True
        except Exception as exc:
            print(f"[switch] gagal membuka Settings sebelum mode extract: {exc}")
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

def configure_image_settings(page, ratio: str = "16:9", count: int = 2):
    """Extract and select the requested Image ratio and generation count."""
    import re
    ratio_alias = {"crop_16_9": "16:9", "crop_landscape": "4:3", "crop_square": "1:1", "crop_portrait": "3:4", "crop_9_16": "9:16"}
    ratio = ratio_alias.get(str(ratio).strip().lower(), str(ratio).strip())
    ratio = ratio.replace("x", ":") if re.fullmatch(r"\d+x\d+", ratio) else ratio
    if ratio not in {"16:9", "4:3", "1:1", "3:4", "9:16"}:
        raise ValueError("ratio harus salah satu dari: 16:9, 4:3, 1:1, 3:4, 9:16")
    count = int(count)
    if count not in {1, 2, 3, 4}:
        raise ValueError("count harus salah satu dari: 1, 2, 3, 4")

    trigger = page.locator("button[aria-label='Settings trigger']").first
    if trigger.count() == 0:
        raise RuntimeError("Settings trigger tidak ketemu setelah Image dipilih")
    # Detect the popup from visible radio buttons instead of locator count;
    # Angular keeps hidden radio nodes mounted after Escape.
    visible_settings = []
    for item in page.locator("button[role='radio']").all():
        try:
            if item.is_visible():
                visible_settings.append(item)
        except Exception:
            pass
    if not any(ratio in " ".join(item.inner_text().split()) for item in visible_settings):
        trigger.click(force=True)
        page.wait_for_timeout(500)

    print(f"[settings] extract Image settings; requested ratio={ratio}, count=x{count}")
    visible = []
    for item in page.locator("button[role='radio']").all():
        try:
            if not item.is_visible():
                continue
            text = " ".join(item.inner_text().split())
            visible.append((item, text))
            print(f"  candidate setting: {text!r} checked={item.get_attribute('aria-checked')}")
        except Exception:
            pass

    ratio_btn = None
    count_btn = None
    for item, text in visible:
        if text.endswith(ratio) or text == ratio:
            ratio_btn = item
        if text == f"x{count}":
            count_btn = item
    if ratio_btn is None:
        raise RuntimeError(f"ratio {ratio} tidak ditemukan di popup Image settings")
    if count_btn is None:
        raise RuntimeError(f"x{count} tidak ditemukan di popup Image settings")

    if ratio_btn.get_attribute("aria-checked") != "true":
        ratio_btn.click(force=True)
        page.wait_for_timeout(300)
        print(f"  selected ratio {ratio}")
    if count_btn.get_attribute("aria-checked") != "true":
        count_btn.click(force=True)
        page.wait_for_timeout(300)
        print(f"  selected count x{count}")

    summary = page.locator("span.settings-summary").first.inner_text().strip()
    summary_ratio = {"16:9": "crop_16_9", "4:3": "crop_landscape", "1:1": "crop_square", "3:4": "crop_portrait", "9:16": "crop_9_16"}
    selected_ratio = summary_ratio[ratio]
    if ratio_btn.get_attribute("aria-checked") != "true" or count_btn.get_attribute("aria-checked") != "true":
        raise RuntimeError(f"settings aria-checked tidak sesuai: ratio={ratio_btn.get_attribute('aria-checked')}, count={count_btn.get_attribute('aria-checked')}")
    if selected_ratio not in summary and ratio not in summary:
        raise RuntimeError(f"settings summary tidak sesuai: {summary!r}")
    # Close the popup explicitly. Escape is flaky with the Material overlay;
    # clicking the same trigger is deterministic when ratio radios are visible.
    try:
        open_ratio = any(
            item.is_visible() and any(token in " ".join(item.inner_text().split()) for token in ("16:9", "4:3", "1:1", "3:4", "9:16"))
            for item in page.locator("button[role='radio']").all()
        )
        if open_ratio:
            trigger.click(force=True)
            page.wait_for_timeout(400)
    except Exception:
        pass
    return True

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

def download_results(page, result_dir: pathlib.Path, folder: pathlib.Path, expected_count: int = 2):
    """Download the first two generated image tiles at 1K."""
    import pathlib as _pl
    import re
    result_dir = _pl.Path(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    print(f"[download] tunggu 2 image generate di {page.url}")
    expected_count = int(expected_count)
    card_sel = "flow-grid-tile-container:has(flow-image-tile)"
    cards = page.locator(card_sel)
    for attempt in range(24):
        count = cards.count()
        print(f"  attempt {attempt + 1}/24: image_cards={count}, expected={expected_count}")
        if count >= expected_count:
            break
        page.wait_for_timeout(5000)
    else:
        print(f"[warn] {expected_count} image card tidak muncul setelah 120s")
        try: page.screenshot(path=str(folder / "10_before_download.png"), full_page=True)
        except Exception: pass
        return False
    downloaded = 0
    for idx in range(expected_count):
        save_path = result_dir / f"result_{idx + 1}_1K.png"
        # Always download the current run; overwrite stale output from a
        # previous prompt instead of counting it as a new result.
        if save_path.exists():
            try:
                save_path.unlink()
            except Exception as exc:
                print(f"[warn] tidak bisa menghapus output lama {save_path}: {exc}")
        success = False
        for retry in range(1, 6):
            try:
                card = page.locator(card_sel).nth(idx)
                image = card.locator("img.image").first
                more = card.locator("button[aria-label='More options']").first
                print(f"[download] image {idx + 1}, retry {retry}/5")
                image.scroll_into_view_if_needed()
                image.hover(force=True)
                page.wait_for_timeout(350)
                if more.count() == 0 or not more.is_visible():
                    raise RuntimeError("More image tidak visible di dalam card")
                print(f"  found image More box={more.bounding_box()}")
                more.click(force=True, timeout=4000)
                page.wait_for_timeout(500)
                dl = None
                for item in page.locator("button[role='menuitem']").all():
                    if not item.is_visible(): continue
                    text = " ".join(item.inner_text().split())
                    icon = item.locator("mat-icon").first
                    icon_text = icon.inner_text().strip() if icon.count() else ""
                    if text == "download Download" or (text == "Download" and icon_text == "download"):
                        dl = item; break
                if dl is None:
                    raise RuntimeError("Download menuitem tidak ketemu setelah image More")
                print(f"  found Download: {dl.inner_text()!r}")
                dl.click(force=True, timeout=4000)
                page.wait_for_timeout(500)
                one_k = None
                for item in page.locator("button[role='menuitem']").all():
                    if not item.is_visible(): continue
                    text = " ".join(item.inner_text().split())
                    if text.startswith("1K"):
                        one_k = item; break
                if one_k is None:
                    raise RuntimeError("1K menuitem tidak ketemu setelah Download")
                print(f"  found 1K: {one_k.inner_text()!r}")
                with page.expect_download(timeout=15000) as dl_info:
                    one_k.click(force=True, timeout=4000)
                download = dl_info.value
                download.save_as(str(save_path))
                if not save_path.exists() or save_path.stat().st_size == 0:
                    raise RuntimeError("download event terjadi tetapi file kosong/tidak ada")
                print(f"  downloaded {save_path} ({save_path.stat().st_size} bytes)")
                downloaded += 1
                success = True
                break
            except Exception as exc:
                print(f"  retry {retry} gagal: {exc}")
                try: page.keyboard.press("Escape")
                except Exception: pass
                page.wait_for_timeout(800)
                try: page.screenshot(path=str(folder / f"10_download_{idx + 1}_{retry}.png"))
                except Exception: pass
        if not success:
            print(f"[download] image {idx + 1} gagal setelah 5 retry")
    print(f"[download] selesai {downloaded}/{expected_count} ke {result_dir}")
    try: page.screenshot(path=str(folder / "11_after_download.png"), full_page=True)
    except Exception: pass
    return downloaded == expected_count

def main(headless=False, prompt_text: str = "Buatkan logo untuk edukasi.", ratio: str = "16:9", count: int = 2):
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
        # Flow may already be in Images mode and expose no Video toggle.
        # Configure ratio/count in either case so requested options are never skipped.
        try:
            configure_image_settings(page, ratio=ratio, count=count)
            print(f"✅ Image settings OK: {ratio}, x{count}")
        except Exception as e:
            print(f"⚠️ Image settings gagal: {e}")
            advisor_click(page, folder, "07b_image_settings_fail", "Image settings gagal; extract ratio/count candidates")
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
        print(f"\n[step 7] Download {count} image (titik tiga -> Download -> 1K) ke result image/")
        result_dir = pathlib.Path("F:/alpha/result image")
        try:
            ok_dl = download_results(page, result_dir, folder, expected_count=count)
            if ok_dl:
                print(f"✅ Download selesai -> {result_dir}")
                advisor_click(page, folder, "10_download_done", f"Download {count} image 1K ke {result_dir} selesai")
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
    ap.add_argument("--ratio", default="16:9", choices=["16:9", "4:3", "1:1", "3:4", "9:16"], help="Image aspect ratio")
    ap.add_argument("--count", type=int, default=2, choices=[1, 2, 3, 4], help="jumlah hasil gambar")
    args=ap.parse_args()
    main(headless=args.headless, prompt_text=args.prompt, ratio=args.ratio, count=args.count)
