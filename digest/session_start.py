"""SessionStart hook: hand a staged session to this one to write up.

Session mode only. When a session closed and left its text staged, this hands
that text, the voice and one instruction to the session opening now, so you
watch the entry being written instead of trusting it happened.

In headless mode there is nothing to do here and nothing is printed.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import common  # noqa: E402

DISTIL = HERE.parent / "rag" / "distil.py"


def main():
    cfg = common.config()
    if cfg["mode"] != "session":
        return
    staged = sorted(common.PENDING.glob("*.md")) if common.PENDING.is_dir() else []
    if not staged:
        return
    notes = common.corpus()
    if notes is None:
        return

    first = staged[0]
    text = first.read_text(encoding="utf-8")
    if not text.strip():
        first.unlink(missing_ok=True)
        return

    log = common.today_log(notes, cfg)
    steps = [
        f"1. Write the entry into {log} under a new heading: "
        f"## Session {datetime.now():%H:%M}. The file is appended to, never edited.",
        f"2. Delete the staged file {first}.",
    ]
    if cfg["distil"]:
        steps.append(f'3. Run: python "{DISTIL}" "{notes}"')
        steps.append("4. Tell me in one line that the last session is written up.")
    else:
        steps.append("3. Tell me in one line that the last session is written up.")

    body = (
        "A session closed and left its text to be written up. Do this first, "
        "before anything else.\n\n"
        + "\n".join(steps)
        + "\n\n=== how to write it ===\n\n"
        + common.PROMPT.read_text(encoding="utf-8")
        + "\n\n=== the session ===\n\n"
        + text
    )
    count = len(staged)
    print(
        json.dumps(
            {
                "systemMessage": (
                    f"memory: {count} session{'' if count == 1 else 's'} to write up"
                ),
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": body,
                },
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a session opening is never blocked by this
        common.note_failure("session_start", f"{type(exc).__name__} {exc}")
    sys.exit(0)
