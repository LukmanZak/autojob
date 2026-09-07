from pathlib import Path
p=Path('F:/alpha/src/auth/google_flow_vision.py')
t=p.read_text(encoding='utf-8')
old='''    settings_trigger = page.locator("button[aria-label='Settings trigger']").first
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
new='''    settings_trigger = page.locator("button[aria-label='Settings trigger']").first
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
'''
if old not in t: raise SystemExit('old block not found')
p.write_text(t.replace(old,new,1),encoding='utf-8')
print('settings trigger wait added')
