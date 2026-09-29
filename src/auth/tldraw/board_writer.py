"""Buka board tldraw berdasarkan alias lalu menulis teks lewat interaksi mouse."""
from __future__ import annotations

import argparse
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

from src.config import DEBUG_DIR, SESSIONS_DIR, ensure_dirs, get_launch_kwargs

TLDRAW_URL = "https://www.tldraw.com/"
TLDRAW_SESSION_FILE = SESSIONS_DIR / "tldraw" / "tldraw.json"
BOARD_ALIASES = {
    "mora": "Mora 2",
    "mora 2": "Mora 2",
    "nayla": "Nayla",
    "qilbi": "Qilbi",
}
FILE_ITEM_SELECTOR = "[data-testid^='tla-file-link-'][role='listitem']"


def resolve_board_name(name: str) -> str:
    """Resolve nama singkat yang disebut user ke nama board tldraw."""
    key = " ".join(name.strip().lower().split())
    try:
        return BOARD_ALIASES[key]
    except KeyError as exc:
        available = ", ".join(sorted(BOARD_ALIASES))
        raise ValueError(f"Board tidak dikenal: {name!r}. Alias tersedia: {available}") from exc


def current_board_name(page) -> str:
    title = page.locator("[data-testid='tla-file-name']").first
    if title.count() == 0:
        return ""
    try:
        return " ".join(title.inner_text().split())
    except Exception:
        return ""


def open_board(page, requested_name: str) -> str:
    """Buka board dengan nama exact, bukan partial match."""
    target = resolve_board_name(requested_name)
    if current_board_name(page) == target:
        print(f"[board] sudah berada di {target}")
        return target

    sidebar = page.locator("[data-testid='tla-sidebar']").first
    sidebar.wait_for(state="visible", timeout=15_000)
    items = sidebar.locator(FILE_ITEM_SELECTOR)
    selected = None
    for index in range(items.count()):
        item = items.nth(index)
        label = " ".join(item.inner_text().split())
        if label == target:
            selected = item
            break

    if selected is None:
        available = [
            " ".join(items.nth(index).inner_text().split())
            for index in range(items.count())
        ]
        raise RuntimeError(
            f"Board {target!r} tidak ditemukan di sidebar. "
            f"Yang terbaca: {available}"
        )

    selected.scroll_into_view_if_needed()
    link = selected.locator("a").first
    click_target = link if link.count() > 0 else selected
    box = click_target.bounding_box()
    if not box or box["width"] <= 0 or box["height"] <= 0:
        raise RuntimeError(f"Board {target!r} tidak punya area klik yang valid: {box}")
    click_target.click(force=True)

    for _ in range(30):
        if current_board_name(page) == target:
            print(f"[board] terbuka: {target}")
            return target
        page.wait_for_timeout(500)
    raise RuntimeError(
        f"Klik board {target!r} selesai, tetapi judul aktif belum berubah. "
        f"Judul sekarang: {current_board_name(page)!r} URL: {page.url}"
    )


def canvas_box(page):
    canvas = page.locator("[data-testid='canvas']").first
    canvas.wait_for(state="visible", timeout=10_000)
    box = canvas.bounding_box()
    if not box or box["width"] < 400 or box["height"] < 300:
        raise RuntimeError(f"Canvas tidak siap: {box}")
    return box


def write_text_with_mouse(page, text: str, canvas_x: float, canvas_y: float) -> None:
    """Klik Text tool, klik posisi canvas dengan mouse, lalu isi text editor."""
    tool = page.locator("[data-testid='tools.text']").first
    tool.wait_for(state="visible", timeout=10_000)
    tool.click(force=True)
    page.wait_for_timeout(250)

    box = canvas_box(page)
    x = box["x"] + canvas_x
    y = box["y"] + canvas_y
    if x >= box["x"] + box["width"] or y >= box["y"] + box["height"]:
        raise RuntimeError(f"Posisi teks di luar canvas: {(x, y)} dalam {box}")

    print(f"[write] mouse click canvas x={round(x)} y={round(y)}")
    page.mouse.click(x, y)
    page.wait_for_timeout(300)
    # tldraw membuat editor teks setelah klik canvas; input tetap dilakukan melalui
    # keyboard Playwright, bukan manipulasi DOM langsung.
    page.keyboard.insert_text(text)
    page.wait_for_timeout(250)
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)


def collect_rendered_text(page) -> list[str]:
    values: list[str] = []
    for selector in ("svg text", "[data-testid='canvas'] text", "text"):
        try:
            values.extend(page.locator(selector).all_inner_texts())
        except Exception:
            pass
    result = []
    seen = set()
    for value in values:
        value = " ".join(value.split())
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def verify_questions(page, questions: list[str]) -> list[str]:
    """Cari kembali teks yang dirender tldraw setelah penulisan."""
    rendered = collect_rendered_text(page)
    body_text = " ".join(page.locator("body").inner_text().split())
    haystack = " ".join(rendered + [body_text])
    missing = []
    for question in questions:
        normalized = " ".join(question.split())
        if normalized not in haystack:
            # Teks tldraw dapat terpecah ke beberapa SVG text node; prefix cukup
            # sebagai fallback verifikasi visual/DOM.
            prefix = normalized[:32]
            if prefix not in haystack:
                missing.append(question)
    print(f"[verify] rendered_text={rendered}")
    return missing


def main(board: str, questions: list[str], keep_open: bool = False) -> None:
    if not questions:
        raise ValueError("Minimal satu --question harus diberikan")
    if not TLDRAW_SESSION_FILE.exists():
        raise FileNotFoundError(
            f"Session tidak ditemukan: {TLDRAW_SESSION_FILE}. "
            "Jalankan login.py terlebih dahulu."
        )

    ensure_dirs()
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    target = resolve_board_name(board)
    print(f"=== tldraw board writer: {board!r} -> {target!r} ===")
    print(f"Session: {TLDRAW_SESSION_FILE}")

    # Tetap headed agar aksi mouse dapat dilihat di browser.
    launch_kwargs = get_launch_kwargs(headless=False)
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            storage_state=str(TLDRAW_SESSION_FILE),
            viewport={"width": 1280, "height": 720},
            locale="en-US",
        )
        page = context.new_page()
        try:
            page.goto(TLDRAW_URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(8_000)
            print(f"[page] URL={page.url} title={page.title()!r}")
            open_board(page, board)

            positions = [(160, 150), (160, 310), (160, 470)]
            for index, question in enumerate(questions):
                x, y = positions[index] if index < len(positions) else (160, 150 + index * 130)
                print(f"[question {index + 1}] {question}")
                write_text_with_mouse(page, question, x, y)

            # Beri waktu sinkronisasi tldraw sebelum verifikasi dan penutupan.
            page.wait_for_timeout(3_000)
            missing = verify_questions(page, questions)
            screenshot = DEBUG_DIR / f"tldraw_{target.lower().replace(' ', '_')}_written.png"
            page.screenshot(path=str(screenshot), full_page=False)
            print(f"[screenshot] {screenshot}")
            if missing:
                raise RuntimeError(f"Teks tidak ditemukan setelah ditulis: {missing}")
            print(f"[done] {len(questions)} teks berhasil ditulis di {target}")

            if keep_open:
                input("Tekan ENTER untuk menutup browser... ")
        finally:
            browser.close()
            print("[closed] Browser ditutup.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", required=True, help="Alias board: mora, nayla, atau qilbi")
    parser.add_argument(
        "--question",
        action="append",
        required=True,
        help="Teks yang ditulis; ulangi option ini untuk beberapa teks",
    )
    parser.add_argument("--keep-open", action="store_true")
    args = parser.parse_args()
    main(board=args.board, questions=args.question, keep_open=args.keep_open)
