"""Query the graph: seed entities from the question, walk k hops, return triples.

Pure SQLite, no model call anywhere in this file. This is the code that runs
inside the prompt hook, so it has to be deterministic and fast.
"""
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "graph.db"

WALK = """
WITH RECURSIVE walk(entity_id, depth) AS (
  SELECT id, 0 FROM entities WHERE id IN ({seeds})
  UNION
  SELECT CASE WHEN r.source_id = w.entity_id
              THEN r.target_id ELSE r.source_id END,
         w.depth + 1
  FROM relations r JOIN walk w
    ON w.entity_id IN (r.source_id, r.target_id)
  WHERE w.depth < ?
)
SELECT e1.name, r.predicate, e2.name, r.source_doc,
       MIN((SELECT MIN(depth) FROM walk WHERE entity_id = r.source_id),
           (SELECT MIN(depth) FROM walk WHERE entity_id = r.target_id)) AS near
FROM relations r
JOIN entities e1 ON e1.id = r.source_id
JOIN entities e2 ON e2.id = r.target_id
WHERE r.source_id IN (SELECT entity_id FROM walk)
  AND r.target_id IN (SELECT entity_id FROM walk)
ORDER BY near
"""


@dataclass
class Facts:
    triples: list  # (source, predicate, target, source_doc)
    notes: list  # (entity_name, description) for entities in the triples
    ms: float

    def as_text(self) -> str:
        header = f"memory: {len(self.triples)} facts recalled in {self.ms:.0f} ms"
        if not self.triples:
            return header + "\n(no memory matches for this prompt)"
        width = max(len(f"{s} --[{p}]--> {t}") for s, p, t, _ in self.triples)
        lines = [f"{f'{s} --[{p}]--> {t}':<{width}}   ({doc})"
                 for s, p, t, doc in self.triples]
        text = header + "\n\n" + "\n".join(lines)
        if self.notes:
            # The conditions live on the entities, not the edges - carry them.
            text += "\n\nwhere:\n" + "\n".join(
                f"  {name}: {desc}" for name, desc in self.notes)
        return text


def _seeds(db: sqlite3.Connection, question: str) -> list:
    """An entity is a seed when its name or an alias appears in the question."""
    q = question.lower()
    found = {}
    rows = list(db.execute("SELECT id, name FROM entities"))
    rows += list(db.execute("SELECT entity_id, alias FROM aliases"))
    for eid, text in rows:
        if re.search(rf"\b{re.escape(text.lower())}\b", q):
            found[eid] = True
    return list(found)


def recall(question: str, hops: int = 3, top_k: int = 8) -> Facts:
    t0 = time.perf_counter()
    db = sqlite3.connect(DB)
    seeds = _seeds(db, question)
    if not seeds:
        return Facts([], [], (time.perf_counter() - t0) * 1000)
    marks = ",".join("?" * len(seeds))
    rows = db.execute(WALK.format(seeds=marks), (*seeds, hops)).fetchall()
    triples = [(s, p, t, doc) for s, p, t, doc, _ in rows[:top_k]]
    names = {n for s, _, t, _ in triples for n in (s, t)}
    marks = ",".join("?" * len(names))
    notes = db.execute(
        f"SELECT name, description FROM entities "  # noqa: S608
        f"WHERE name IN ({marks}) AND description != '' ORDER BY name",
        (*names,)).fetchall()
    return Facts(triples, notes, (time.perf_counter() - t0) * 1000)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    question = " ".join(sys.argv[1:]) or "what do we know?"
    print(recall(question).as_text())
