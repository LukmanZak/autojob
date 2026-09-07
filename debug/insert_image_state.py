from pathlib import Path
p=Path('F:/alpha/src/auth/google_flow_vision.py')
t=p.read_text(encoding='utf-8')
needle='def switch_video_to_images(page):\n'
insert='''def switch_video_to_images(page):
    # Some Flow projects reopen with Image already selected. Detect that
    # state first instead of failing while searching for a Video summary.
    for loc in page.locator("button[role='radio'][aria-checked='true']").all():
        try:
            if loc.is_visible() and loc.locator("span.toggle-text").filter(has_text="Image").count() > 0:
                print("[switch] Image sudah aktif; skip klik Video -> lanjut settings")
                return True
        except Exception:
            pass
'''
if t.count(needle)!=1: raise SystemExit(f'needle count={t.count(needle)}')
t=t.replace(needle,insert,1)
p.write_text(t,encoding='utf-8')
print('already-image detection added')
