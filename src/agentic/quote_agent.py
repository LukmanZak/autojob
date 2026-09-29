"""Agentic quote workflow: Google Flow -> four images -> WhatsApp Web."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import os
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence

from src.config import LOGS_DIR, PROJECT_ROOT, ensure_dirs
from .whatsapp import WhatsAppAgentError, send_images, setup_whatsapp_session

FLOW_SCRIPT = PROJECT_ROOT / "src" / "auth" / "google_flow_vision.py"
FLOW_LOGIN_SCRIPT = PROJECT_ROOT / "src" / "auth" / "google_flow_session" / "login.py"
FLOW_SESSION_FILE = PROJECT_ROOT / "data" / "sessions" / "google_flow.json"
FLOW_IMAGE_ROOT = PROJECT_ROOT / "images" / "flow"
QUOTE_RESULT_ROOT = PROJECT_ROOT / "result image"

# Prompts stay in English so the generated artwork has one consistent language.
DEFAULT_QUOTE_PROMPTS: tuple[str, ...] = (
    "Create a premium vertical 9:16 motivational quote poster for social media. Use a warm sunrise over quiet mountains, elegant modern typography, generous negative space, strong contrast, and a calm hopeful mood. Display exactly this quote, with perfect spelling and no extra words: \"Small steps still move you forward.\" Keep the quote highly legible and centered.",
    "Create a stylish vertical 9:16 inspirational quote poster for social media. Use soft cream paper, a bold cobalt blue accent, subtle geometric shapes, refined editorial typography, and an optimistic modern mood. Display exactly this quote, with perfect spelling and no extra words: \"Your future is built by what you do today.\" Keep the quote highly legible and centered.",
    "Create a minimal vertical 9:16 quote poster with a deep charcoal background, a single glowing line of light, premium white typography, balanced spacing, and a focused cinematic mood. Display exactly this quote, with perfect spelling and no extra words: \"Focus on progress, not perfection.\" Keep the quote highly legible and centered.",
    "Create a vibrant vertical 9:16 quote poster for social media using a tasteful coral, lavender, and gold color palette, fluid abstract shapes, crisp contemporary typography, and an uplifting mood. Display exactly this quote, with perfect spelling and no extra words: \"Make room for the life you want.\" Keep the quote highly legible and centered.",
)


class QuoteAgentError(RuntimeError):
    """An expected problem with a clear next action."""


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True)
class QuoteAgentSettings:
    """Runtime choices for one agent run."""

    prompts: tuple[str, ...] = DEFAULT_QUOTE_PROMPTS
    target: str = os.getenv("WHATSAPP_TARGET", "You").strip() or "You"
    send: bool = _env_bool("QUOTE_AGENT_AUTO_SEND", False)
    headless: bool = _env_bool("QUOTE_AGENT_HEADLESS", False)
    flow_timeout_seconds: int = int(os.getenv("QUOTE_AGENT_FLOW_TIMEOUT", "1800"))
    whatsapp_timeout_seconds: int = int(os.getenv("QUOTE_AGENT_WHATSAPP_TIMEOUT", "120"))


class AgentConsole:
    """Friendly terminal updates; detailed browser output goes to a log file."""

    def __init__(self) -> None:
        self.started = dt.datetime.now()

    @staticmethod
    def _stamp() -> str:
        return dt.datetime.now().strftime("%H:%M:%S")

    def info(self, message: str) -> None:
        print(f"[{self._stamp()}] {message}", flush=True)

    def ok(self, message: str) -> None:
        self.info(f"Selesai: {message}")

    def warn(self, message: str) -> None:
        self.info(f"Perhatian: {message}")

    def fail(self, message: str) -> None:
        self.info(f"Berhenti: {message}")


def _detail_log_path() -> pathlib.Path:
    ensure_dirs()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOGS_DIR / f"quote_agent_{stamp}_detail.log"


def _print_plan(console: AgentConsole, prompts: Sequence[str]) -> None:
    console.info("Rencana hari ini: buka Google Flow, buat 4 gambar quote, lalu kirim ke WhatsApp.")
    for index, prompt in enumerate(prompts, start=1):
        console.info(f"Quote {index}: {prompt}")


def _latest_batch_root(started_at: float) -> pathlib.Path | None:
    candidates = [path for path in QUOTE_RESULT_ROOT.glob("batch_*") if path.is_dir()]
    if not candidates:
        return None
    fresh = [path for path in candidates if path.stat().st_mtime >= started_at - 2]
    return max(fresh or candidates, key=lambda path: path.stat().st_mtime)


def _collect_generated_images(batch_root: pathlib.Path, expected: int) -> list[pathlib.Path]:
    images: list[pathlib.Path] = []
    for index in range(1, expected + 1):
        prompt_dir = batch_root / f"prompt_{index}"
        candidates = sorted(prompt_dir.glob("result_*.png")) + sorted(prompt_dir.glob("result_*.jpg")) + sorted(prompt_dir.glob("result_*.jpeg"))
        if not candidates:
            raise QuoteAgentError(
                f"Gambar quote ke-{index} belum ditemukan. Detail browser ada di folder logs/."
            )
        images.append(candidates[0])
    return images


def _run_flow(settings: QuoteAgentSettings, console: AgentConsole, detail_log: pathlib.Path) -> list[pathlib.Path]:
    if not FLOW_SESSION_FILE.exists():
        raise QuoteAgentError(
            "Sesi Google Flow belum siap. Jalankan `python quote_agent.py --setup-flow` "
            "sekali, lalu ulangi agent."
        )
    if not FLOW_SCRIPT.exists():
        raise QuoteAgentError(f"Alur Google Flow tidak ditemukan: {FLOW_SCRIPT}")
    if len(settings.prompts) != 4:
        raise QuoteAgentError("Alur ini menjaga hasil tetap 4 gambar; berikan tepat 4 prompt.")

    QUOTE_RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    FLOW_IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
    started_at = dt.datetime.now().timestamp()
    command = [
        sys.executable,
        str(FLOW_SCRIPT),
        "--headless" if settings.headless else "--no-headless",
        "--no-wait",
        "--ratio",
        "9:16",
        "--count",
        "1",
        "--model",
        "Nano Banana 2",
    ]
    for prompt in settings.prompts:
        command.extend(["--prompt", prompt])

    console.info("Membuka browser dan menyiapkan Google Flow...")
    console.info("Pointer browser akan bergerak sendiri saat tombol penting dipilih.")
    with detail_log.open("w", encoding="utf-8") as stream:
        try:
            result = subprocess.run(
                command,
                cwd=str(PROJECT_ROOT),
                stdin=None,
                stdout=stream,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=settings.flow_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise QuoteAgentError(
                "Google Flow belum selesai dalam batas waktu. Cek browser dan log detail."
            ) from exc

    if result.returncode != 0:
        raise QuoteAgentError(
            f"Google Flow berhenti sebelum selesai (kode {result.returncode}). "
            f"Lihat log detail: {detail_log}"
        )

    batch_root = _latest_batch_root(started_at)
    if batch_root is None:
        raise QuoteAgentError(
            "Google Flow selesai tetapi folder hasil belum ada. "
            f"Lihat log detail: {detail_log}"
        )
    images = _collect_generated_images(batch_root, len(settings.prompts))
    return images


def run_quote_agent(settings: QuoteAgentSettings | None = None) -> list[pathlib.Path]:
    """Run one complete quote generation and optional delivery cycle."""
    settings = settings or QuoteAgentSettings()
    console = AgentConsole()
    detail_log = _detail_log_path()
    _print_plan(console, settings.prompts)

    if settings.headless:
        console.warn("Mode tanpa tampilan aktif; gunakan --visible agar browser terlihat.")

    if not settings.send:
        console.info("Mode aman: gambar akan dibuat, tetapi belum dikirim. Tambahkan --send untuk mengirim.")

    if not FLOW_IMAGE_ROOT.exists():
        FLOW_IMAGE_ROOT.mkdir(parents=True, exist_ok=True)

    console.info("Langkah 1/2: membuat empat gambar quote...")
    images = _run_flow(settings, console, detail_log)
    console.ok(f"Empat gambar siap di {images[0].parent.parent}")

    if settings.send:
        console.info("Langkah 2/2: membuka WhatsApp Web...")
        try:
            sent = send_images(
                images,
                target=settings.target,
                timeout_ms=settings.whatsapp_timeout_seconds * 1_000,
            )
        except WhatsAppAgentError:
            raise
        console.ok(f"{sent} gambar terkirim ke chat '{settings.target}'.")
    else:
        console.info("Langkah 2/2 dilewati. Tidak ada pesan yang dikirim.")

    console.ok(f"Run selesai. Catatan browser tersimpan di {detail_log}")
    return images


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agent konten: Google Flow -> 4 quote images -> WhatsApp Web"
    )
    parser.add_argument("--send", action="store_true", default=None, help="kirim 4 gambar ke chat target")
    parser.add_argument("--no-send", action="store_false", dest="send", help="buat gambar tanpa mengirim")
    parser.add_argument("--visible", action="store_false", dest="headless", help="tampilkan browser (default)")
    parser.add_argument("--headless", action="store_true", dest="headless", help="jalankan browser tanpa tampilan")
    parser.add_argument("--target", default=None, help="nama chat WhatsApp yang harus sama persis")
    parser.add_argument("--prompt", action="append", dest="prompts", help="ganti prompt; ulangi 4 kali")
    parser.add_argument("--dry-run", action="store_true", help="tampilkan rencana tanpa membuka browser")
    parser.add_argument("--setup-flow", action="store_true", help="login Google Flow sekali dan simpan sesi")
    parser.add_argument("--setup-whatsapp", action="store_true", help="login WhatsApp Web sekali dan simpan sesi")
    parser.set_defaults(headless=None, send=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = QuoteAgentSettings(
        prompts=tuple(args.prompts) if args.prompts else DEFAULT_QUOTE_PROMPTS,
        target=(args.target or os.getenv("WHATSAPP_TARGET", "You")).strip() or "You",
        send=QuoteAgentSettings.send if args.send is None else args.send,
        headless=QuoteAgentSettings.headless if args.headless is None else args.headless,
    )
    console = AgentConsole()

    try:
        if args.setup_flow:
            if not FLOW_LOGIN_SCRIPT.exists():
                raise QuoteAgentError(f"Helper login Google Flow tidak ditemukan: {FLOW_LOGIN_SCRIPT}")
            console.info("Membuka browser untuk login Google Flow sekali...")
            completed = subprocess.run([sys.executable, str(FLOW_LOGIN_SCRIPT)], cwd=str(PROJECT_ROOT), check=False)
            return completed.returncode

        if args.setup_whatsapp:
            console.info("Membuka browser untuk login WhatsApp Web sekali...")
            setup_whatsapp_session()
            console.ok("Sesi WhatsApp siap dipakai oleh jadwal otomatis.")
            return 0

        if len(settings.prompts) != 4:
            raise QuoteAgentError("Agent quote membutuhkan tepat 4 prompt agar hasilnya tetap 4 gambar.")

        if args.dry_run:
            _print_plan(console, settings.prompts)
            console.ok("Dry-run selesai; browser tidak dibuka dan tidak ada pesan dikirim.")
            return 0

        run_quote_agent(settings)
        return 0
    except (QuoteAgentError, WhatsAppAgentError) as exc:
        console.fail(str(exc))
        return 1
    except KeyboardInterrupt:
        console.warn("Run dihentikan dari keyboard.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
