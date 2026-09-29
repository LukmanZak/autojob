"""Google Flow dengan folder gambar + AI advisor (vision) - sesi terekam."""
import argparse, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from playwright.sync_api import sync_playwright
from src.config import PROJECT_ROOT, get_launch_kwargs, SESSIONS_DIR, ensure_dirs
from src.vision.flow_advisor import ensure_flow_session, save_step, advisor_click

FLOW_URL = "https://flow.google.com/?pli=1"
# sanitize jika kepaste @url:`...`
FLOW_URL = FLOW_URL.replace("@url:", "").replace("`", "").strip()
SESSION_FILE = SESSIONS_DIR / "google_flow.json"
def move_mouse(page, locator=None):
    """Move the visible browser pointer before an important action."""
    try:
        box = locator.bounding_box() if locator is not None else None
        viewport = page.viewport_size or {"width": 1280, "height": 720}
        if box:
            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2
        else:
            x = viewport["width"] / 2
            y = viewport["height"] / 2
        page.mouse.move(max(1, x - 90), max(1, y - 45), steps=8)
        page.mouse.move(x, y, steps=10)
    except Exception:
        # Pointer motion is cosmetic; it must never block the workflow.
        pass


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
    for sel in ["button[aria-label='Create with Google Flow']", "button:has-text('Create with Google Flow')", "a:has-text('Try in Google Flow')","a:has-text('Try Flow')","button:has-text('Try in Google Flow')","a:has-text('Try')"]:
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
def has_prompt_composer(page):
    """Return whether the Flow project editor is ready for a prompt."""
    for sel in [
        "flow-rich-text-editor .ProseMirror",
        "div[contenteditable='true'].ProseMirror",
        "text='What do you want to create?'",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                return True
        except Exception:
            pass
    return False


def find_existing_project(page):
    """Pick the first project card when New project cannot open."""
    for sel in ["a[aria-label='Open project']", "a[href*='/project/']"]:
        try:
            links = page.locator(sel)
            for index in range(links.count()):
                loc = links.nth(index)
                if loc.is_visible() and loc.bounding_box():
                    print(f"[found] Existing project {sel} index={index}")
                    return loc
        except Exception:
            pass
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

def configure_image_settings(page, ratio: str = "16:9", count: int = 2, model: str = "Nano Banana 2"):
    """Extract and select Image ratio, model family, and generation count."""
    import re
    ratio_alias = {"crop_16_9": "16:9", "crop_landscape": "4:3", "crop_square": "1:1", "crop_portrait": "3:4", "crop_9_16": "9:16"}
    ratio = ratio_alias.get(str(ratio).strip().lower(), str(ratio).strip())
    ratio = ratio.replace("x", ":") if re.fullmatch(r"\d+x\d+", ratio) else ratio
    if ratio not in {"16:9", "4:3", "1:1", "3:4", "9:16"}:
        raise ValueError("ratio harus salah satu dari: 16:9, 4:3, 1:1, 3:4, 9:16")
    count = int(count)
    if count not in {1, 2, 3, 4}:
        raise ValueError("count harus salah satu dari: 1, 2, 3, 4")
    model_alias = {
        "nano banana pro": "Nano Banana Pro",
        "nano banana 2": "Nano Banana 2",
        "nano banana 2 lite": "Nano Banana 2 Lite",
    }
    model = model_alias.get(str(model).strip().lower(), str(model).strip())
    if model not in {"Nano Banana Pro", "Nano Banana 2", "Nano Banana 2 Lite"}:
        raise ValueError("model harus Nano Banana Pro, Nano Banana 2, atau Nano Banana 2 Lite")

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

    model_btn = page.locator("button[aria-label='Select model family']").first
    if model_btn.count() == 0:
        raise RuntimeError("Select model family tidak ditemukan di Image settings")
    current_model = " ".join(model_btn.inner_text().split())
    # Do not use substring matching: "Nano Banana 2" is contained in
    # "Nano Banana 2 Lite" and would silently leave the wrong model active.
    if current_model != model:
        model_btn.click(force=True)
        page.wait_for_timeout(300)
        model_item = None
        for item in page.locator("[role='menuitem']").all():
            item_text = " ".join(item.inner_text().split())
            if item.is_visible() and (item_text == model or item_text.endswith(model)):
                model_item = item
                break
        if model_item is None:
            raise RuntimeError(f"model {model} tidak ditemukan di dropdown")
        model_item.click(force=True)
        page.wait_for_timeout(500)
        # Material dropdown can remain visually open after selection; close it
        # before interacting with count or the prompt submit button.
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception:
            pass
        print(f"  selected model {model}")

    # Selecting a model may close and recreate the settings overlay. Reopen it
    # and reacquire ratio/count locators instead of using stale radio handles.
    fresh_radios = []
    for overlay_attempt in range(4):
        fresh_radios = []
        for item in page.locator("button[role='radio']").all():
            try:
                if item.is_visible():
                    fresh_radios.append((item, " ".join(item.inner_text().split())))
            except Exception:
                pass
        if any(text == f"x{count}" for _, text in fresh_radios):
            break
        try:
            trigger.click(force=True)
        except Exception:
            pass
        page.wait_for_timeout(1200)
    ratio_btn = next((item for item, text in fresh_radios if text.endswith(ratio) or text == ratio), None)
    count_btn = next((item for item, text in fresh_radios if text == f"x{count}"), None)
    if ratio_btn is None or count_btn is None:
        raise RuntimeError(f"radio settings tidak lengkap setelah reopen: {[text for _, text in fresh_radios]}")

    if ratio_btn.get_attribute("aria-checked") != "true":
        ratio_btn.click(force=True)
        page.wait_for_timeout(300)
        print(f"  selected ratio {ratio}")
    if count_btn.get_attribute("aria-checked") != "true":
        count_btn.click(force=True)
        page.wait_for_timeout(300)
        print(f"  selected count x{count}")

    if count_btn.get_attribute("aria-checked") != "true":
        raise RuntimeError(f"gagal memilih x{count}; aria-checked masih {count_btn.get_attribute('aria-checked')}")

    summary = page.locator("span.settings-summary").first.inner_text().strip()
    selected_settings = " ".join(page.locator("button[aria-label='Settings trigger']").first.inner_text().split())
    known_models = ["Nano Banana Pro", "Nano Banana 2 Lite", "Nano Banana 2"]
    detected_model = next(
        (name for name in sorted(known_models, key=len, reverse=True)
         if name in selected_settings),
        None,
    )
    if detected_model != model:
        raise RuntimeError(f"model summary tidak sesuai: {selected_settings!r}")
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

def upload_reference_image(page, image_path: str):
    """Open Add ingredients -> Upload media and attach a reference image."""
    image = pathlib.Path(image_path).expanduser().resolve()
    if not image.exists() or image.stat().st_size == 0:
        raise FileNotFoundError(f"reference image tidak ada/kosong: {image}")
    plus = page.locator("button[aria-label='Add ingredients to the prompt box']").first
    for attempt in range(30):
        if plus.count() > 0 and plus.is_visible() and plus.bounding_box():
            break
        print(f"[upload] menunggu tombol Add ingredients ({attempt + 1}/30)")
        page.wait_for_timeout(1000)
    if plus.count() == 0 or not plus.is_visible() or not plus.bounding_box():
        raise RuntimeError("tombol Add ingredients to the prompt box tidak ditemukan")
    plus.click(force=True)
    page.wait_for_timeout(500)
    upload = page.get_by_text("Upload media", exact=True).last
    if upload.count() == 0 or not upload.is_visible():
        raise RuntimeError("tombol Upload media tidak muncul setelah tombol +")
    print(f"[upload] Upload media ditemukan box={upload.bounding_box()}")
    with page.expect_file_chooser(timeout=5000) as chooser_info:
        upload.click(force=True)
    chooser_info.value.set_files(str(image))
    # The uploaded asset can remain in a loading state for several seconds;
    # visibility alone is not enough because Add to prompt is initially disabled.
    add_to_prompt = page.get_by_text("Add to prompt", exact=True).last
    for attempt in range(20):
        if add_to_prompt.count() > 0 and add_to_prompt.is_visible() and add_to_prompt.is_enabled():
            break
        print(f"[upload] waiting for Add to prompt enabled ({attempt + 1}/20)")
        page.wait_for_timeout(1000)
    if add_to_prompt.count() == 0 or not add_to_prompt.is_visible() or not add_to_prompt.is_enabled():
        raise RuntimeError("asset ter-upload tetapi tombol Add to prompt tetap disabled")
    # Upload first creates an asset in the media picker. It is not yet an
    # ingredient until the picker action "Add to prompt" is clicked.
    print(f"[upload] klik Add to prompt box={add_to_prompt.bounding_box()}")
    add_to_prompt.click(force=True)
    page.wait_for_timeout(1800)
    body = " ".join(page.locator("body").inner_text().split())
    print(f"[upload] file dipasang: {image.name}; body_tail={body[-500:]}")
    # Flow renders an ingredient chip/thumbnail after the upload completes.
    if image.name not in body and page.locator("img").count() == 0:
        print("[upload] nama file tidak tampil sebagai teks; lanjut dengan screenshot/DOM evidence")
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
        move_mouse(page, fill_loc)
        fill_loc.click(force=True); page.wait_for_timeout(300)
        # Flow's contenteditable requires real keyboard events; DOM fill can
        # look correct while Flow's internal prompt state remains empty.
        is_contenteditable = fill_loc.get_attribute("contenteditable") == "true"
        if is_contenteditable:
            fill_loc.press("Control+A")
            fill_loc.press("Backspace")
            fill_loc.press_sequentially(prompt_text, delay=0)
        else:
            fill_loc.fill(prompt_text)
        page.wait_for_timeout(300)
        # Flow may render a contenteditable whose DOM text changes without
        # updating the composer model. Read back the live value before submit.
        live_text = ""
        try:
            live_text = fill_loc.input_value()
        except Exception:
            try:
                live_text = fill_loc.inner_text()
            except Exception:
                live_text = fill_loc.text_content() or ""
        if prompt_text.strip() not in live_text.strip():
            print(f"[fill] composer readback mismatch; retry with keyboard insert_text")
            move_mouse(page, fill_loc)
            fill_loc.click(force=True)
            fill_loc.press("Control+A")
            fill_loc.press("Backspace")
            fill_loc.press_sequentially(prompt_text, delay=0)
            page.wait_for_timeout(300)
            try:
                live_text = fill_loc.input_value()
            except Exception:
                live_text = fill_loc.inner_text()
        if prompt_text.strip() not in live_text.strip():
            raise RuntimeError(f"composer readback kosong/tidak sesuai: {live_text[:120]!r}")
        print(f"  composer readback OK ({len(live_text)} chars)")
        print(f"  filled '{prompt_text[:40]}'")
        page.wait_for_timeout(500)
        # tekan Enter atau klik tombol arrow kirim
        try:
            fill_loc.press("Enter")
            print("  pressed Enter")
        except: pass
        # coba klik tombol kirim (arrow)
        for sel in ["button[aria-label='Start generation']", "button:has(mat-icon:has-text('arrow_forward'))", "button:has-text('→')", "button[aria-label*='Send']"]:
            try:
                btn = page.locator(sel).first
                if btn.count()>0 and btn.is_visible():
                    print(f"  generate button enabled={btn.is_enabled()} box={btn.bounding_box()}")
                    move_mouse(page, btn)
                    btn.click(force=True, timeout=2000)
                    print(f"  clicked send {sel}")
                    # Capture the immediate post-submit state before any
                    # follow-up card/menu interaction. This exposes whether
                    # Flow accepted the prompt or only updated the composer.
                    page.wait_for_timeout(1500)
                    cards = page.locator("flow-grid-tile-container:has(flow-image-tile)")
                    print(f"  post-generate cards={cards.count()} url={page.url}")
                    try:
                        page.screenshot(path=str(pathlib.Path("F:/alpha/images/flow") / "post_generate_probe.png"), full_page=True)
                    except Exception as exc:
                        print(f"  post-generate screenshot failed: {exc}")
                    break
            except: pass
        page.wait_for_timeout(1500)
        print("✅ Fill prompt done")
        return True
    except Exception as e:
        print(f"fill fail {e}")
        import traceback; traceback.print_exc()
        return False

def add_generated_image_to_prompt(page, card_index: int = 0):
    """Attach a generated result through its card menu before the next prompt."""
    card_sel = "flow-grid-tile-container:has(flow-image-tile)"
    cards = page.locator(card_sel)
    ready_card = None
    for attempt in range(36):
        if cards.count() > card_index:
            candidate = cards.nth(card_index)
            try:
                image = candidate.locator("img.image").first
                ready = image.count() > 0 and image.is_visible() and image.evaluate("el => el.complete && el.naturalWidth > 0")
                if ready:
                    ready_card = candidate
                    break
            except Exception:
                pass
        print(f"[reuse] menunggu kartu hasil siap ({attempt + 1}/36)")
        page.wait_for_timeout(2000)
    if ready_card is None:
        raise RuntimeError(f"kartu hasil index {card_index} belum memiliki gambar siap untuk Add to prompt")

    card = ready_card
    card.scroll_into_view_if_needed()
    card.hover(force=True)
    page.wait_for_timeout(500)
    more = card.locator("button[aria-label='More options']").first
    if more.count() == 0 or not more.is_visible():
        raise RuntimeError("titik tiga More options tidak terlihat pada kartu hasil")
    print(f"[reuse] buka titik tiga kartu index={card_index} box={more.bounding_box()}")
    more.click(force=True)
    page.wait_for_timeout(400)

    # The menu is replaced dynamically, so reacquire only visible exact labels.
    add_items = []
    for selector in ["[role='menuitem']", "button", "div"]:
        for item in page.locator(selector).all():
            try:
                text = " ".join(item.inner_text().split())
                if text == "Add to prompt" and item.is_visible() and item.is_enabled():
                    add_items.append(item)
            except Exception:
                pass
    if not add_items:
        try:
            visible_menu_text = []
            for item in page.locator("[role='menuitem'], [role='menu'], [role='dialog']").all():
                if item.is_visible():
                    visible_menu_text.append(" ".join(item.inner_text().split()))
            print(f"[reuse] menu visible text: {visible_menu_text}")
        except Exception:
            pass
        raise RuntimeError("menu titik tiga tidak memiliki Add to prompt yang aktif")
    add_to_prompt = add_items[-1]
    print(f"[reuse] klik Add to prompt box={add_to_prompt.bounding_box()}")
    add_to_prompt.click(force=True)
    page.wait_for_timeout(1200)

    # Confirm the composer contains an ingredient before typing the next prompt.
    body = " ".join(page.locator("body").inner_text().split())
    composer = page.locator("textarea, input, div[contenteditable='true']")
    ingredient_images = 0
    for img in page.locator("img").all():
        try:
            if img.is_visible():
                ingredient_images += 1
        except Exception:
            pass
    if ingredient_images == 0:
        raise RuntimeError("Add to prompt diklik tetapi thumbnail ingredient tidak terdeteksi")
    print(f"✅ [reuse] kartu hasil index={card_index} dipasang sebagai reference; visible_images={ingredient_images}; body_tail={body[-300:]}")
    return True

def download_results(page, result_dir: pathlib.Path, folder: pathlib.Path, expected_count: int = 2, start_index: int = 0):
    """Download one batch of generated image tiles at 1K."""
    import pathlib as _pl
    import re
    result_dir = _pl.Path(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    print(f"[download] tunggu batch {expected_count} image generate di {page.url} mulai index {start_index}")
    expected_count = int(expected_count)
    card_sel = "flow-grid-tile-container:has(flow-image-tile)"
    cards = page.locator(card_sel)
    for attempt in range(24):
        count = cards.count()
        print(f"  attempt {attempt + 1}/24: image_cards={count}, expected={expected_count}")
        if count >= start_index + expected_count:
            break
        page.wait_for_timeout(5000)
    else:
        print(f"[warn] batch cards {start_index}:{start_index + expected_count} tidak muncul setelah 120s")
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
                card = page.locator(card_sel).nth(start_index + idx)
                image = card.locator("img.image").first
                more = card.locator("button[aria-label='More options']").first
                print(f"[download] batch image {idx + 1}/{expected_count}, retry {retry}/5")
                if image.count() == 0 or not image.is_visible() or not image.evaluate("el => el.complete && el.naturalWidth > 0"):
                    print("  tunggu gambar hasil selesai dimuat (maks. 60s)")
                    ready = False
                    for wait_attempt in range(30):
                        page.wait_for_timeout(2000)
                        if image.count() > 0 and image.is_visible() and image.evaluate("el => el.complete && el.naturalWidth > 0"):
                            ready = True
                            break
                    if not ready:
                        raise RuntimeError("gambar hasil belum selesai dimuat setelah 60s")
                image.scroll_into_view_if_needed()
                image.hover(force=True)
                page.wait_for_timeout(350)
                if more.count() == 0 or not more.is_visible():
                    raise RuntimeError("More image tidak visible di dalam card")
                print(f"  found image More box={more.bounding_box()}")
                move_mouse(page, more)
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
                move_mouse(page, dl)
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
                    move_mouse(page, one_k)
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

def main(headless=False, prompt_text="Buatkan logo untuk edukasi.", ratio: str = "16:9", count: int = 2, input_image: str = None, model: str = "Nano Banana 2", wait_for_close: bool = True):
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
                    move_mouse(page, btn)
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
                    move_mouse(page, create_btn)
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
        # 3 Open a project editor. New project can be visually present but
        # inert on the current Flow home, so fall back to an existing card.
        opened_editor = has_prompt_composer(page)
        if not opened_editor:
            np = find_new_project(page)
            if np:
                try:
                    np.scroll_into_view_if_needed(); page.wait_for_timeout(500)
                    page.evaluate("window.scrollBy(0, -100)")
                    page.wait_for_timeout(300)
                    move_mouse(page, np)
                    np.click(force=True); page.wait_for_timeout(3000)
                    print("  -> New Project clicked")
                except Exception as e:
                    print(f"  New Project click fail {e}")
                opened_editor = has_prompt_composer(page)
        if not opened_editor:
            project = find_existing_project(page)
            if project:
                try:
                    project.scroll_into_view_if_needed(); page.wait_for_timeout(400)
                    move_mouse(page, project)
                    project.click(force=True, no_wait_after=True)
                    page.wait_for_timeout(2500)
                except Exception as e:
                    print(f"  Existing project click fail {e}")
                if not has_prompt_composer(page):
                    try:
                        href = project.get_attribute("href")
                        if href:
                            target_url = href if href.startswith("http") else f"https://flow.google.com{href}"
                            print(f"  -> membuka alamat project langsung: {target_url}")
                            page.goto(target_url, wait_until="commit", timeout=30000)
                            page.wait_for_timeout(5000)
                    except Exception as e:
                        print(f"  Existing project direct open fail {e}")
                opened_editor = has_prompt_composer(page)
        if not opened_editor:
            raise RuntimeError(
                "Editor Google Flow belum terbuka. Pilih salah satu project di browser "
                "sekali, lalu jalankan agent lagi."
            )
        advisor_click(page, folder, "04_project_editor_ready", "Editor project siap. Cari area prompt.")
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
                    move_mouse(page, gs)
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
            # Respect an explicit model choice even when a reference image is used.
            selected_model = model
            configure_image_settings(page, ratio=ratio, count=count, model=selected_model)
            print(f"✅ Image settings OK: {selected_model}, {ratio}, x{count}")
        except Exception as e:
            raise RuntimeError(f"Image settings wajib berhasil: {e}") from e
        advisor_click(page, folder, "07_after_video_switch", "Setelah switch Video->Images, apakah sudah jadi Images? Jika belum, dimana tombol Images?")
        if ok: print("✅ Video -> Images OK")
        else: print("⚠️  Cek manual Video->Images di browser")
        if input_image:
            print(f"\n[step 5b] Upload reference image: {input_image}")
            try:
                upload_reference_image(page, input_image)
                advisor_click(page, folder, "07c_after_upload", "Reference image sudah di-upload. Pastikan thumbnail/ingredient muncul di prompt box.")
                print("✅ Reference image upload done")
            except Exception as e:
                print(f"⚠️ Upload reference image gagal: {e}")
                advisor_click(page, folder, "07c_upload_fail", "Upload media gagal; cek DOM, menu, dan file chooser.")
                raise
        # 6-7 Batch prompts: one settings setup, then one prompt/download group
        prompt_list = prompt_text if isinstance(prompt_text, (list, tuple)) else [prompt_text]
        batch_root = PROJECT_ROOT / "result image" / f"batch_{folder.name}"
        batch_root.mkdir(parents=True, exist_ok=True)
        for batch_idx, current_prompt in enumerate(prompt_list, start=1):
            # Flow prepends the newest generation cards before older cards.
            # Each batch therefore downloads the newest `count` cards at index 0.
            batch_start = 0
            if input_image and batch_idx > 1:
                print(f"\n[batch {batch_idx}] Pasang hasil batch sebelumnya sebagai reference via titik tiga")
                add_generated_image_to_prompt(page, card_index=0)
            print(f"\n[batch {batch_idx}/{len(prompt_list)}] Fill prompt '{current_prompt}' -> Images mode")
            filled = fill_prompt(page, current_prompt)
            advisor_click(page, folder, f"08_after_fill_{batch_idx}", f"Batch {batch_idx} prompt sudah diisi. Apakah generate mulai?")
            if not filled:
                print(f"⚠️ Batch {batch_idx} prompt gagal diisi, lanjut batch berikutnya")
                continue
            print(f"✅ Batch {batch_idx} prompt submitted; existing_cards={batch_start}")
            page.wait_for_timeout(2500)
            advisor_click(page, folder, f"09_generating_{batch_idx}", f"Batch {batch_idx} sedang generate")
            result_dir = batch_root / f"prompt_{batch_idx}"
            print(f"[batch {batch_idx}] Download {count} image ke {result_dir}")
            try:
                ok_dl = download_results(page, result_dir, folder, expected_count=count, start_index=batch_start)
                if ok_dl:
                    print(f"✅ Batch {batch_idx} download selesai -> {result_dir}")
                    advisor_click(page, folder, f"10_download_done_{batch_idx}", f"Batch {batch_idx} download {count} image selesai")
                else:
                    print(f"⚠️ Batch {batch_idx} download belum lengkap")
                    advisor_click(page, folder, f"10_download_fail_{batch_idx}", f"Batch {batch_idx} download gagal")
            except Exception as e:
                print(f"batch {batch_idx} download step fail {e}")
        ctx.storage_state(path=str(SESSION_FILE))
        print(f"\n=== SELESAI ===")
        print(f"Folder: {folder}")
        print(f"File: {list(folder.glob('*'))}")
        print(f"Session: {SESSION_FILE}")
        print("Kirim folder ini ke AI: AI baca steps.json + lihat png untuk tau sesi & next click")
        if wait_for_close:
            try: input("ENTER untuk tutup browser >> ")
            except: page.wait_for_timeout(15000)
        else:
            page.wait_for_timeout(500)
        browser.close()

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true", default=False)
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    ap.add_argument("--no-wait", action="store_true", help="tutup browser otomatis setelah selesai")
    ap.add_argument("--prompt", action="append", dest="prompts", default=None, help="prompt; ulangi opsi ini untuk menjalankan batch beberapa prompt")
    ap.add_argument("--ratio", default="16:9", choices=["16:9", "4:3", "1:1", "3:4", "9:16"], help="Image aspect ratio")
    ap.add_argument("--count", type=int, default=2, choices=[1, 2, 3, 4], help="jumlah hasil gambar")
    ap.add_argument("--input-image", default=None, help="path foto referensi untuk di-upload sebagai ingredient")
    ap.add_argument("--model", default="Nano Banana 2", choices=["Nano Banana Pro", "Nano Banana 2", "Nano Banana 2 Lite"], help="model Image; otomatis Pro jika memakai input-image")
    args=ap.parse_args()
    main(headless=args.headless, prompt_text=args.prompts or ["Buatkan logo untuk edukasi."], ratio=args.ratio, count=args.count, input_image=args.input_image, model=args.model, wait_for_close=not args.no_wait)
