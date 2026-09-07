from pathlib import Path
p=Path('F:/alpha/src/auth/google_flow_vision.py')
t=p.read_text(encoding='utf-8')
start=t.index('def switch_video_to_images(page):')
body=t.index('    # LOGIKA BARU: extract loop sampai Video muncul, baru cari Images',start)
head='''def switch_video_to_images(page):
    # Flow hides the Image/Video radios inside Settings. Open that panel
    # before extracting them; a project may already reopen in Image mode.
    settings_trigger = page.locator("button[aria-label='Settings trigger']").first
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
'''
t=t[:start]+head+t[body:]
p.write_text(t,encoding='utf-8')
print('switch settings-open logic replaced')
