import hashlib
from pathlib import Path
from datetime import datetime, timezone
import uuid
import platform
import sys

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def new_run_id() -> str:
    return str(uuid.uuid4())

def env_fingerprint() -> dict:
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
    }