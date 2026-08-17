"""Build the index: chunk markdown on headings, index keywords and meaning.

Reads ../corpus-before by default, plus any distilled entries in distilled/.
Writes rag.db next to this script. Run again any time; the index is disposable.
"""

import argparse
import re
import sqlite3
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "rag.db"
CHUNK_BUDGET = 1600  # characters, roughly 400 tokens

SCHEMA = """
DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS chunks_fts;
DROP TABLE IF EXISTS vectors;
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    file TEXT NOT NULL,
    section TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    text TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'chunk'
);
CREATE VIRTUAL TABLE chunks_fts USING fts5(text, file, section);
CREATE TABLE vectors (id INTEGER PRIMARY KEY, vec BLOB NOT NULL);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def sections(lines):
    """Split markdown lines into (heading, start, end) sections."""
    out = []
    heading, start = None, 0
    for i, line in enumerate(lines):
        if re.match(r"^#{1,3} ", line):
            if i > start or heading is not None:
                out.append((heading, start, i))
            heading, start = line.lstrip("# ").strip(), i
    out.append((heading, start, len(lines)))
    return [(h, s, e) for h, s, e in out if any(l.strip() for l in lines[s:e])]


def chunk_file(path):
    """Yield (section, start_line, end_line, text) chunks packed to the budget."""
    lines = path.read_text(encoding="utf-8").splitlines()
    packed = []
    for heading, s, e in sections(lines):
        text = "\n".join(lines[s:e]).strip()
        title = heading or path.stem
        if len(text) <= CHUNK_BUDGET:
            packed.append((title, s + 1, e, text))
            continue
        # oversized section: split on line groups within the budget
        buf, buf_start = [], s
        for i in range(s, e):
            buf.append(lines[i])
            if sum(len(l) + 1 for l in buf) >= CHUNK_BUDGET:
                packed.append((title, buf_start + 1, i + 1, "\n".join(buf).strip()))
                buf, buf_start = [], i + 1
        if any(l.strip() for l in buf):
            packed.append((title, buf_start + 1, e, "\n".join(buf).strip()))
    return packed


def parse_distilled(path):
    """Read a distilled entry: source, questions, summary, rule, quote."""
    entry = {"questions": []}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("source:"):
            entry["source"] = line.split(":", 1)[1].strip()
        elif line.startswith("- "):
            entry["questions"].append(line[2:].strip())
        elif line.startswith("summary:"):
            entry["summary"] = line.split(":", 1)[1].strip()
        elif line.startswith("rule:"):
            entry["rule"] = line.split(":", 1)[1].strip()
        elif line.startswith("quote:"):
            entry["quote"] = line.split(":", 1)[1].strip().strip('"')
    return entry


def normalise(text):
    return " ".join(text.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(HERE.parent / "corpus-before"))
    args = ap.parse_args()
    corpus = Path(args.corpus)

    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    db.execute("INSERT INTO meta VALUES ('corpus', ?)", (str(corpus.resolve()),))

    docs = []  # (embed_text, row)
    files = sorted(corpus.glob("*.md"))
    for path in files:
        for section, s, e, text in chunk_file(path):
            label = f"[{path.name} § {section}]"
            row = (path.name, section, s, e, text, "chunk")
            docs.append((label + "\n" + text, row))

    dropped = 0
    distilled_dir = HERE / "distilled"
    distilled_files = sorted(distilled_dir.glob("*.md")) if distilled_dir.is_dir() else []
    for path in distilled_files:
        entry = parse_distilled(path)
        source = corpus / entry.get("source", "")
        quote = entry.get("quote", "")
        # grounding check: the quote must appear in the source, word for word
        if not source.is_file() or normalise(quote) not in normalise(source.read_text(encoding="utf-8")):
            dropped += 1
            print(f"dropped {path.name}: quote not found in {entry.get('source', '?')}")
            continue
        body = "\n".join(
            entry["questions"]
            + [entry.get("summary", ""), entry.get("rule", ""), quote]
        ).strip()
        label = f"[{entry['source']} § distilled]"
        row = (entry["source"], "distilled", 0, 0, body, "distilled")
        docs.append((label + "\n" + body, row))

    for embed_text, row in docs:
        cur = db.execute(
            "INSERT INTO chunks (file, section, start_line, end_line, text, kind) VALUES (?,?,?,?,?,?)",
            row,
        )
        db.execute(
            "INSERT INTO chunks_fts (rowid, text, file, section) VALUES (?,?,?,?)",
            (cur.lastrowid, embed_text, row[0], row[1]),
        )

    model_line = "keyword only (pip install fastembed for the meaning leg)"
    try:
        from fastembed import TextEmbedding

        model = TextEmbedding()  # default: BAAI/bge-small-en-v1.5
        vecs = list(model.embed([t for t, _ in docs]))
        for rowid, vec in enumerate(vecs, start=1):
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            blob = struct.pack(f"{len(vec)}f", *(x / norm for x in vec))
            db.execute("INSERT INTO vectors (id, vec) VALUES (?,?)", (rowid, blob))
        model_line = f"model {model.model_name} ({len(vecs[0])}d) + keyword sqlite fts5"
    except ImportError:
        pass

    db.commit()
    db.close()
    n_distilled = len(distilled_files) - dropped
    print(f"indexed {len(files)} files, {len(docs) - n_distilled} chunks, {n_distilled} distilled entries, {dropped} dropped")
    print(model_line)


if __name__ == "__main__":
    main()
