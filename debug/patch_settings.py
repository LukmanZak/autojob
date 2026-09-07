from pathlib import Path
p=Path('F:/alpha/src/auth/google_flow_vision.py')
t=p.read_text(encoding='utf-8')
marker='def fill_prompt(page, prompt_text: str):\n'
insert=r'''def configure_image_settings(page, ratio: str = "16:9", count: int = 2):
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
    candidate = page.locator("button[role='radio']").filter(has_text=ratio).first
    if candidate.count() == 0 or not candidate.is_visible():
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
    print(f"[settings] summary after selection: {summary!r}")
    if ratio not in summary or f"x{count}" not in summary:
        raise RuntimeError(f"settings summary tidak sesuai: {summary!r}")
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(250)
    except Exception:
        pass
    return True

'''
if marker not in t: raise SystemExit('marker not found')
t=t.replace(marker,insert+marker,1)
t=t.replace('def download_results(page, result_dir: pathlib.Path, folder: pathlib.Path):', 'def download_results(page, result_dir: pathlib.Path, folder: pathlib.Path, expected_count: int = 2):',1)
t=t.replace('    card_sel = "flow-grid-tile-container:has(flow-image-tile)"\n', '    expected_count = int(expected_count)\n    card_sel = "flow-grid-tile-container:has(flow-image-tile)"\n',1)
t=t.replace('        print(f"  attempt {attempt + 1}/24: image_cards={count}")\n        if count >= 2:', '        print(f"  attempt {attempt + 1}/24: image_cards={count}, expected={expected_count}")\n        if count >= expected_count:',1)
t=t.replace('        print("[warn] 2 image card tidak muncul setelah 120s")', '        print(f"[warn] {expected_count} image card tidak muncul setelah 120s")',1)
t=t.replace('    for idx in range(2):\n', '    for idx in range(expected_count):\n',1)
t=t.replace('    print(f"[download] selesai {downloaded}/2 ke {result_dir}")', '    print(f"[download] selesai {downloaded}/{expected_count} ke {result_dir}")',1)
t=t.replace('    return downloaded == 2\n', '    return downloaded == expected_count\n',1)
t=t.replace('def main(headless=False, prompt_text: str = "Buatkan logo untuk edukasi."):', 'def main(headless=False, prompt_text: str = "Buatkan logo untuk edukasi.", ratio: str = "16:9", count: int = 2):',1)
t=t.replace('        ok=switch_video_to_images(page)\n', '        ok=switch_video_to_images(page)\n        if ok:\n            try:\n                configure_image_settings(page, ratio=ratio, count=count)\n                print(f"✅ Image settings OK: {ratio}, x{count}")\n            except Exception as e:\n                print(f"⚠️ Image settings gagal: {e}")\n                advisor_click(page, folder, "07b_image_settings_fail", "Image settings gagal; extract ratio/count candidates")\n',1)
t=t.replace('        print(f"\\n[step 7] Download 2 image (titik tiga -> Download -> 1K) ke result image/")', '        print(f"\\n[step 7] Download {count} image (titik tiga -> Download -> 1K) ke result image/")',1)
t=t.replace('            ok_dl = download_results(page, result_dir, folder)', '            ok_dl = download_results(page, result_dir, folder, expected_count=count)',1)
t=t.replace('                advisor_click(page, folder, "10_download_done", f"Download 2 image 1K ke {result_dir} selesai")', '                advisor_click(page, folder, "10_download_done", f"Download {count} image 1K ke {result_dir} selesai")',1)
t=t.replace('    ap.add_argument("--prompt", default="Buatkan logo untuk edukasi.", help="prompt untuk fill What do you want to create?")\n    args=ap.parse_args()\n    main(headless=args.headless, prompt_text=args.prompt)', '    ap.add_argument("--prompt", default="Buatkan logo untuk edukasi.", help="prompt untuk fill What do you want to create?")\n    ap.add_argument("--ratio", default="16:9", choices=["16:9", "4:3", "1:1", "3:4", "9:16"], help="Image aspect ratio")\n    ap.add_argument("--count", type=int, default=2, choices=[1, 2, 3, 4], help="jumlah hasil gambar")\n    args=ap.parse_args()\n    main(headless=args.headless, prompt_text=args.prompt, ratio=args.ratio, count=args.count)')
p.write_text(t,encoding='utf-8')
print('settings/count support added')
