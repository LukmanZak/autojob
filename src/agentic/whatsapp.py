"""Small, visible WhatsApp Web delivery layer for the quote agent.

The module deliberately uses a saved browser session instead of handling a
WhatsApp password. The first login is always completed by the account owner in
the visible browser window.
"""
from __future__ import annotations

import pathlib
import time
from typing import Iterable

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from src.config import SESSIONS_DIR, ensure_dirs, get_launch_kwargs

WHATSAPP_URL = "https://web.whatsapp.com/"
WHATSAPP_SESSION_FILE = SESSIONS_DIR / "whatsapp_web.json"


class WhatsAppAgentError(RuntimeError):
    """An expected, user-actionable WhatsApp Web problem."""


def _visible_first(page: Page, selectors: Iterable[str]):
    for selector in selectors:
        try:
            candidates = page.locator(selector)
            for index in range(candidates.count()):
                item = candidates.nth(index)
                if item.is_visible():
                    return item
        except Exception:
            continue
    return None


def _move_mouse(page: Page, locator=None) -> None:
    """Move the visible browser pointer before an important action."""
    try:
        box = locator.bounding_box() if locator is not None else None
        if box:
            target_x = box["x"] + box["width"] / 2
            target_y = box["y"] + box["height"] / 2
        else:
            viewport = page.viewport_size or {"width": 1280, "height": 720}
            target_x = viewport["width"] / 2
            target_y = viewport["height"] / 2
        page.mouse.move(max(1, target_x - 90), max(1, target_y - 45), steps=8)
        page.mouse.move(target_x, target_y, steps=10)
    except Exception:
        # Pointer motion is cosmetic; it must never block delivery.
        pass


def _click(page: Page, locator) -> None:
    _move_mouse(page, locator)
    locator.click(force=True, timeout=8_000)
    page.wait_for_timeout(350)


def _is_logged_in(page: Page) -> bool:
    ready_selectors = [
        "div[contenteditable='true'][data-tab='3']",
        "button[aria-label*='Search']",
        "div[title='Search']",
        "span[data-icon='search']",
    ]
    return _visible_first(page, ready_selectors) is not None


def _wait_for_login(page: Page, timeout_ms: int, allow_manual: bool) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if _is_logged_in(page):
            return
        page.wait_for_timeout(1_000)

    if allow_manual:
        print("[WhatsApp] Browser sudah terbuka. Selesaikan QR jika diminta.")
        try:
            input("[WhatsApp] Tekan ENTER setelah daftar chat terlihat: ")
        except EOFError as exc:
            raise WhatsAppAgentError(
                "WhatsApp belum siap. Jalankan `python quote_agent.py --setup-whatsapp` "
                "sekali dari terminal yang bisa menerima input."
            ) from exc
        if _is_logged_in(page):
            return

    raise WhatsAppAgentError(
        "WhatsApp Web belum terhubung. Jalankan `python quote_agent.py --setup-whatsapp` "
        "untuk login sekali di browser yang terbuka."
    )


def _open_page(playwright, allow_manual: bool, timeout_ms: int):
    launch_kwargs = get_launch_kwargs(headless=False)
    browser = playwright.chromium.launch(**launch_kwargs)
    context_kwargs = {
        "viewport": {"width": 1280, "height": 850},
        "locale": "en-US",
    }
    if WHATSAPP_SESSION_FILE.exists():
        context_kwargs["storage_state"] = str(WHATSAPP_SESSION_FILE)
    context = browser.new_context(**context_kwargs)
    page = context.new_page()
    try:
        page.goto(WHATSAPP_URL, wait_until="domcontentloaded", timeout=60_000)
    except Exception:
        # WhatsApp can keep loading after the shell appears; readiness below is
        # the useful check.
        pass
    page.wait_for_timeout(2_000)
    _wait_for_login(page, timeout_ms, allow_manual)
    return browser, context, page


def _open_search(page: Page):
    search_box = _visible_first(
        page,
        [
            "div[contenteditable='true'][data-tab='3']",
            "input[placeholder*='Search']",
            "div[contenteditable='true'][role='textbox']",
        ],
    )
    if search_box is not None:
        return search_box

    search_button = _visible_first(
        page,
        [
            "button[aria-label*='Search']",
            "div[title='Search']",
            "span[data-icon='search']",
        ],
    )
    if search_button is not None:
        _click(page, search_button)
        page.wait_for_timeout(500)

    search_box = _visible_first(
        page,
        [
            "div[contenteditable='true'][data-tab='3']",
            "input[placeholder*='Search']",
            "div[contenteditable='true'][role='textbox']",
        ],
    )
    if search_box is None:
        raise WhatsAppAgentError("Kolom pencarian WhatsApp tidak terlihat.")
    return search_box


def _select_exact_chat(page: Page, target: str) -> None:
    search = _open_search(page)
    try:
        search.fill("")
    except Exception:
        search.click(force=True)
        search.press("Control+A")
        search.press("Backspace")
    search.fill(target)
    page.wait_for_timeout(1_200)

    exact_title = []
    for selector in ["span[title]", "[role='gridcell']", "[role='listitem']", "[role='option']"]:
        try:
            for index in range(page.locator(selector).count()):
                item = page.locator(selector).nth(index)
                if not item.is_visible():
                    continue
                title = (item.get_attribute("title") or "").strip()
                text = " ".join(item.inner_text().split())
                if title == target:
                    exact_title.append(item)
                elif text == target:
                    exact_title.append(item)
        except Exception:
            continue

    if not exact_title:
        raise WhatsAppAgentError(
            f"Chat '{target}' tidak ditemukan. Pastikan nama chat diri sendiri sama persis "
            "dengan nilai WHATSAPP_TARGET. Tidak ada pesan yang dikirim."
        )

    _click(page, exact_title[0])
    page.wait_for_timeout(700)


def _set_file_for_attachment(page: Page, image_path: pathlib.Path, attach_button) -> None:
    _click(page, attach_button)
    page.wait_for_timeout(450)
    file_inputs = page.locator("input[type='file']")
    if file_inputs.count() > 0:
        file_inputs.last.set_input_files(str(image_path))
        return

    # Some WhatsApp builds open the native chooser only after the first menu
    # click. Handle that variant without touching the OS file dialog.
    try:
        with page.expect_file_chooser(timeout=3_000) as chooser_info:
            _click(page, attach_button)
        chooser_info.value.set_files(str(image_path))
    except PlaywrightTimeoutError as exc:
        raise WhatsAppAgentError("Menu lampiran gambar WhatsApp tidak muncul.") from exc


def _send_button(page: Page):
    button = _visible_first(
        page,
        [
            "button[aria-label='Send']",
            "button[aria-label*='Send']",
            "div[role='button'][aria-label*='Send']",
            "span[data-icon='send']",
        ],
    )
    if button is None:
        raise WhatsAppAgentError("Tombol kirim gambar belum terlihat.")
    return button


def _send_one(page: Page, image_path: pathlib.Path) -> None:
    attach = _visible_first(
        page,
        [
            "button[aria-label*='Attach']",
            "div[title='Attach']",
            "button[title='Attach']",
            "span[data-icon='attach']",
        ],
    )
    if attach is None:
        raise WhatsAppAgentError("Tombol lampiran WhatsApp tidak terlihat.")

    _set_file_for_attachment(page, image_path, attach)
    page.wait_for_timeout(1_000)
    _click(page, _send_button(page))
    page.wait_for_timeout(1_200)


def setup_whatsapp_session(timeout_ms: int = 180_000) -> pathlib.Path:
    """Open WhatsApp visibly, let the owner finish login, and save the session."""
    ensure_dirs()
    with sync_playwright() as playwright:
        browser = None
        try:
            browser, context, page = _open_page(playwright, allow_manual=True, timeout_ms=timeout_ms)
            context.storage_state(path=str(WHATSAPP_SESSION_FILE))
            if not WHATSAPP_SESSION_FILE.exists() or WHATSAPP_SESSION_FILE.stat().st_size == 0:
                raise WhatsAppAgentError("Sesi WhatsApp tidak berhasil disimpan.")
            print(f"[WhatsApp] Sesi tersimpan: {WHATSAPP_SESSION_FILE}")
            return WHATSAPP_SESSION_FILE
        finally:
            if browser is not None:
                browser.close()


def send_images(images: Iterable[pathlib.Path], target: str = "You", timeout_ms: int = 60_000) -> int:
    """Send verified image files to one exact chat label."""
    if not WHATSAPP_SESSION_FILE.exists():
        raise WhatsAppAgentError(
            "Sesi WhatsApp belum siap. Jalankan `python quote_agent.py --setup-whatsapp` "
            "sekali, lalu ulangi agent."
        )
    paths = [pathlib.Path(path).expanduser().resolve() for path in images]
    if not paths:
        raise WhatsAppAgentError("Tidak ada gambar yang bisa dikirim.")
    if not target.strip():
        raise WhatsAppAgentError("Nama chat WhatsApp kosong.")
    for path in paths:
        if not path.exists() or path.stat().st_size == 0:
            raise WhatsAppAgentError(f"File gambar tidak ada atau kosong: {path}")

    ensure_dirs()
    with sync_playwright() as playwright:
        browser = None
        try:
            browser, context, page = _open_page(playwright, allow_manual=False, timeout_ms=timeout_ms)
            _select_exact_chat(page, target.strip())
            for index, path in enumerate(paths, start=1):
                print(f"[WhatsApp] Mengirim gambar {index}/{len(paths)}...")
                _send_one(page, path)
            context.storage_state(path=str(WHATSAPP_SESSION_FILE))
            return len(paths)
        finally:
            if browser is not None:
                browser.close()
