"""UserPromptSubmit hook: your notes, read before Claude answers.

Claude Code hands this hook the prompt on stdin as JSON. It runs the same two
legs as search.py and hands the top hits back as additionalContext.

It never blocks a prompt. No index, no prompt, no hits, or any failure at all,
and it prints nothing and exits 0.
"""

import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

DB = HERE / "rag.db"
TOP = 5
BUDGET = 1500  # characters of context in total
PER_HIT = 280  # characters of chunk text per hit


def hits(query):
    """The top rows for a query, as (label, one-line text) pairs."""
    from search import fuse, keyword_leg, meaning_leg

    db = sqlite3.connect(DB)
    try:
        legs = {"keyword": keyword_leg(db, query)}
        meaning = meaning_leg(db, query)
        if meaning is not None:
            legs["meaning"] = meaning
        ranked, _ = fuse(legs)
        out = []
        for rowid in ranked[:TOP]:
            file, section, text = db.execute(
                "SELECT file, section, text FROM chunks WHERE id=?", (rowid,)
            ).fetchone()
            out.append((f"[{file} § {section}]", " ".join(text.split())))
        return out
    finally:
        db.close()


def block(found):
    """The hits trimmed to the budget. Whole hits only, never a half one."""
    kept, used = [], 0
    for label, text in found:
        piece = text[:PER_HIT] + ("..." if len(text) > PER_HIT else "")
        entry = f"{label}\n{piece}"
        if kept and used + len(entry) > BUDGET:
            break
        kept.append(entry)
        used += len(entry) + 2
    return kept


def main():
    try:
        prompt = json.load(sys.stdin).get("prompt", "")
    except Exception:
        return
    if not isinstance(prompt, str) or not prompt.strip() or not DB.is_file():
        return
    try:
        kept = block(hits(prompt))
    except Exception:
        return
    if not kept:
        return
    count = len(kept)
    print(
        json.dumps(
            {
                "systemMessage": f"memory: {count} hit{'' if count == 1 else 's'}",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "From your notes:\n\n" + "\n\n".join(kept),
                },
            }
        )
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
