"""Auth manager - simpan/restore storage_state untuk hindari login tiap run."""
import pathlib
from src.config import SESSIONS_DIR, ensure_dirs

def session_path(source: str) -> pathlib.Path:
    ensure_dirs()
    return SESSIONS_DIR / f"{source}.json"

def has_session(source: str) -> bool:
    return session_path(source).exists()

# Placeholder login - implement per portal jika butuh
# Contoh: async def login_glints(page, user, pw): ...
