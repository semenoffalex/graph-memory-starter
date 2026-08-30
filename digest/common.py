"""What the three digest scripts all need: the config, your notes, the log."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
PROMPT = HERE / "digest-prompt.md"
PENDING = HERE / "pending"
LOG = HERE / "log"
RAG_DB = HERE.parent / "rag" / "rag.db"

DEFAULTS = {
    "mode": "session",
    "min_turns": 5,
    "max_turns": 30,
    "max_chars": 15000,
    "model": "sonnet",
    "log_dir": "daily",
    "distil": True,
}


def config():
    """config.json over the defaults. A broken file never stops the digest."""
    cfg = dict(DEFAULTS)
    try:
        loaded = json.loads(CONFIG.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            cfg.update(loaded)
    except Exception:
        pass
    return cfg


def corpus():
    """Your notes folder, as build_index recorded it. None when there is no index."""
    if not RAG_DB.is_file():
        return None
    try:
        db = sqlite3.connect(RAG_DB)
        row = db.execute("SELECT value FROM meta WHERE key='corpus'").fetchone()
        db.close()
    except Exception:
        return None
    if not row or not row[0]:
        return None
    path = Path(row[0])
    return path if path.is_dir() else None


def today_log(notes, cfg, when=None):
    """Today's log file inside your notes. The folder is made if it is missing."""
    when = when or datetime.now()
    folder = Path(notes) / cfg["log_dir"]
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{when:%Y-%m-%d}.md"


def note_failure(name, message):
    """Write a failure where a member can find it, and never raise doing it."""
    try:
        LOG.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().isoformat(timespec="seconds")
        with (LOG / "digest.log").open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {name}: {message}\n")
    except Exception:
        pass
