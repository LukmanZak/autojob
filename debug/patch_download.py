from pathlib import Path
p=Path('F:/alpha/src/auth/google_flow_vision.py')
t=p.read_text(encoding='utf-8')
start=t.index('def download_results(')
end=t.index('\ndef main(', start)
new=r'''def download_results(page, result_dir: pathlib.Path, folder: pathlib.Path):
    """Download the first two generated image tiles at 1K."""
    import pathlib as _pl
    import re
    result_dir = _pl.Path(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    print(f"[download] tunggu 2 image generate di {page.url}")
    card_sel = "flow-grid-tile-container:has(flow-image-tile)"
    cards = page.locator(card_sel)
    for attempt in range(24):
        count = cards.count()
        print(f"  attempt {attempt + 1}/24: image_cards={count}")
        if count >= 2:
            break
        page.wait_for_timeout(5000)
    else:
        print("[warn] 2 image card tidak muncul setelah 120s")
        try: page.screenshot(path=str(folder / "10_before_download.png"), full_page=True)
        except Exception: pass
        return False
    downloaded = 0
    for idx in range(2):
        save_path = result_dir / f"result_{idx + 1}_1K.png"
        if save_path.exists() and save_path.stat().st_size > 0:
            print(f"[download] image {idx + 1} sudah ada: {save_path}")
            downloaded += 1
            continue
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
    print(f"[download] selesai {downloaded}/2 ke {result_dir}")
    try: page.screenshot(path=str(folder / "11_after_download.png"), full_page=True)
    except Exception: pass
    return downloaded == 2
'''
p.write_text(t[:start]+new+t[end:],encoding='utf-8')
print('replaced download_results')
