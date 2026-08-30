"""Distil your notes into the questions they answer, through claude -p.

    python distil.py path/to/your/notes
    python distil.py path/to/your/notes --limit 20

One short call per note, subfolders included. Every answer is checked before it
is kept: it needs a question and a quote, and the quote has to be in the note
word for word. Anything else is dropped and named. A note already distilled is
skipped unless it has changed since. The index is rebuilt at the end.

State lives in distilled/.state.json, keyed by the note's path inside your
notes folder with the sha256 of what was read.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build_index import normalise, note_files, parse_entry, utf8_out  # noqa: E402

DISTILLED = HERE / "distilled"
STATE = DISTILLED / ".state.json"
PROMPT = HERE / "distil-prompt.md"
CONFIG = HERE.parent / "digest" / "config.json"
CALL_TIMEOUT = 300  # seconds for one claude -p call


def model_name():
    """The model in digest/config.json, or sonnet when there is no config."""
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8")).get("model") or "sonnet"
    except Exception:
        return "sonnet"


def child_env():
    """The environment for a claude -p child, with our own markers removed.

    Claude Code stamps CLAUDECODE and a set of CLAUDE_* variables into every
    session. Left in place they tell the child it is nested inside the session
    that started it. MEMORY_STARTER_CHILD goes the other way: it tells our own
    SessionEnd hook that this session is the digest, so it is not digested.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
    env["MEMORY_STARTER_CHILD"] = "1"
    return env


def claude_argv(model):
    """The command that runs one headless call, resolved for this machine."""
    exe = shutil.which("claude")
    if exe is None:
        raise RuntimeError("claude is not on your PATH")
    argv = [exe, "-p", "--model", model, "--output-format", "text"]
    if exe.lower().endswith((".cmd", ".bat")):
        argv = ["cmd", "/c", *argv]  # a shim, not an executable
    return argv


def ask(model, prompt_text, payload):
    """One claude -p call. The prompt file and the payload go in on stdin.

    It runs in an empty folder on purpose. The child reads what we hand it and
    nothing else: no project, no settings, no hooks of ours firing inside it.
    """
    with tempfile.TemporaryDirectory(prefix="memory-starter-") as scratch:
        proc = subprocess.run(
            claude_argv(model),
            input=prompt_text + "\n\n---\n\n" + payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=child_env(),
            cwd=scratch,
            timeout=CALL_TIMEOUT,
        )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "claude failed").strip()[:200])
    return proc.stdout


def slug_for(rel):
    """A file name for a note's distilled entry, unique across subfolders."""
    stem = rel[:-3] if rel.endswith(".md") else rel
    return (re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "note") + ".md"


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state):
    DISTILLED.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def render(rel, entry):
    """The distilled entry as build_index reads it."""
    lines = [f"source: {rel}"]
    lines += [f"- {q}" for q in entry["questions"]]
    if entry.get("summary"):
        lines.append(f"summary: {entry['summary']}")
    if entry.get("rule"):
        lines.append(f"rule: {entry['rule']}")
    lines.append(f'quote: "{entry["quote"]}"')
    return "\n".join(lines) + "\n"


def distil_one(path, rel, model, prompt_text):
    """Distil one note. Returns the entry text, or None with the reason said."""
    body = path.read_text(encoding="utf-8", errors="replace")
    entry = parse_entry(ask(model, prompt_text, f"file name: {rel}\n\n{body}"))
    quote = entry.get("quote", "")
    if not entry["questions"] or not quote:
        print(f"dropped {rel}: no question or no quote")
        return None
    if normalise(quote) not in normalise(body):
        print(f"dropped {rel}: quote not found in the note")
        return None
    return render(rel, entry)


def run(corpus, paths=None, limit=None, rebuild=True):
    """Distil the notes under corpus that have changed. Returns the counts."""
    corpus = Path(corpus).resolve()
    if not corpus.is_dir():
        raise RuntimeError(f"not a folder: {corpus}")
    prompt_text = PROMPT.read_text(encoding="utf-8")
    model = model_name()
    files = [Path(p).resolve() for p in paths] if paths else note_files(corpus)

    state = load_state()
    counts = {"distilled": 0, "skipped": 0, "dropped": 0}
    for path in files:
        if limit is not None and counts["distilled"] + counts["dropped"] >= limit:
            counts["skipped"] += 1
            continue
        rel = path.relative_to(corpus).as_posix()
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        known = state.get(rel)
        slug = slug_for(rel)
        if known and known.get("sha256") == digest and (DISTILLED / slug).is_file():
            counts["skipped"] += 1
            continue
        try:
            text = distil_one(path, rel, model, prompt_text)
        except Exception as exc:  # one bad note never stops the run
            print(f"dropped {rel}: {type(exc).__name__} {exc}")
            counts["dropped"] += 1
            continue
        if text is None:
            counts["dropped"] += 1
            continue
        DISTILLED.mkdir(parents=True, exist_ok=True)
        (DISTILLED / slug).write_text(text, encoding="utf-8")
        state[rel] = {"sha256": digest, "slug": slug}
        counts["distilled"] += 1
        print(f"distilled {rel} -> distilled/{slug}")
    save_state(state)

    print(
        f"distilled {counts['distilled']}, skipped {counts['skipped']}, "
        f"dropped {counts['dropped']}"
    )
    if rebuild and counts["distilled"]:
        rebuild_index(corpus)
    return counts


def rebuild_index(corpus):
    """Rebuild the index over a folder. The index is disposable, always."""
    subprocess.run(
        [sys.executable, str(HERE / "build_index.py"), "--corpus", str(corpus)],
        check=False,
    )


def main():
    utf8_out()
    ap = argparse.ArgumentParser(description="Distil notes into questions.")
    ap.add_argument("corpus", help="the folder your markdown notes are in")
    ap.add_argument("--limit", type=int, default=None, help="stop after N notes")
    args = ap.parse_args()
    try:
        run(args.corpus, limit=args.limit)
    except Exception as exc:
        sys.exit(f"distil: {exc}")


if __name__ == "__main__":
    main()
