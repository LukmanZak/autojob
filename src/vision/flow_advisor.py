"""Vision advisor - kirim screenshot ke AI (muse-spark) biar tau sesi & harus klik apa."""
import pathlib, json, datetime, base64

def ensure_flow_session():
    base = pathlib.Path("F:/alpha/images/flow")
    base.mkdir(parents=True, exist_ok=True)
    sess = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    folder = base / sess
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "steps.json").write_text(json.dumps([], indent=2), encoding="utf-8")
    print(f"[vision] session folder: {folder}")
    return folder

def save_step(folder: pathlib.Path, page, step_name: str, ai_decision=None):
    """Screenshot + log steps.json"""
    folder = pathlib.Path(folder)
    # hitung nomor
    existing = sorted(folder.glob("*.png"))
    idx = len(existing) + 1
    fname = f"{idx:02d}_{step_name}.png"
    path = folder / fname
    try:
        # viewport 1200 height, full_page False cukup, tapi jangan kepotong - screenshot viewport yang sudah di-scroll
        page.screenshot(path=str(path), full_page=False)
        print(f"[vision] screenshot {fname} -> {path} ({path.stat().st_size} bytes)")
    except Exception as e:
        print(f"screenshot fail {e}")
        path = None
    # log
    log_path = folder / "steps.json"
    try:
        steps = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    except: steps=[]
    steps.append({
        "idx": idx,
        "step": step_name,
        "file": str(path) if path else None,
        "url": page.url if hasattr(page, 'url') else "",
        "title": page.title() if hasattr(page, 'title') else "",
        "ai_decision": ai_decision,
        "time": datetime.datetime.now().isoformat()
    })
    log_path.write_text(json.dumps(steps, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

def ask_ai_for_click(screenshot_path: pathlib.Path, prompt: str = "Cari tombol yang harus di-klik untuk lanjutkan flow. Return klik koordinat."):
    """
    Placeholder untuk kirim ke muse-spark vision.
    Di hermes desktop, screenshot akan di-render via MEDIA: path dan divisi bisa pakai vision_analyze manual.
    Untuk automation headless, fungsi ini bisa dipanggil manual: vision_analyze(image_url=path, question=prompt)
    """
    # Untuk sekarang hanya log, tidak auto-call AI (butuh API key frontend).
    # User bisa drag screenshot ke chat dan tanya AI, atau next iter kita auto-call via tool.
    return {"action": "manual_check", "path": str(screenshot_path), "prompt": prompt}

# Helper untuk dipanggil dari google_flow.py
def advisor_click(page, folder, step_name, prompt):
    path = save_step(folder, page, step_name)
    decision = ask_ai_for_click(path, prompt)
    # simpan decision ke steps.json (update last)
    log_path = pathlib.Path(folder) / "steps.json"
    steps = json.loads(log_path.read_text(encoding="utf-8"))
    steps[-1]["ai_decision"] = decision
    log_path.write_text(json.dumps(steps, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[advisor] {step_name} -> {decision} | cek {path}")
    return path, decision
