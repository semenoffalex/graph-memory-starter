"""Load extraction/*.json into graph.db. Deterministic: same input, same db."""
import json
import sqlite3
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "graph.db"


def normalise(name: str) -> str:
    return name.lower().strip().replace(" ", "_")


def entity_id(type_: str, name: str) -> str:
    key = f"{type_}:{normalise(name)}"
    return str(uuid.uuid5(uuid.NAMESPACE_OID, key))
    # "Ops Manager" in doc 1 and doc 4 -> the same node. No ML, no lookup.


def main() -> None:
    DB.unlink(missing_ok=True)
    db = sqlite3.connect(DB)
    db.executescript((ROOT / "src" / "schema.sql").read_text(encoding="utf-8"))

    files = sorted((ROOT / "extraction").glob("*.json"))
    docs = [json.loads(f.read_text(encoding="utf-8")) for f in files]

    # Pass 1 - every node from every doc, content-addressed.
    for doc in docs:
        for n in doc["nodes"]:
            db.execute(
                "INSERT OR IGNORE INTO entities VALUES (?,?,?,?,?)",
                (entity_id(n["type"], n["name"]), n["name"], n["type"],
                 n.get("description", ""), doc["source_doc"]),
            )

    by_name = {normalise(name): eid
               for eid, name in db.execute("SELECT id, name FROM entities")}

    # Pass 2 - edges and aliases, endpoints resolved by normalised name.
    skipped = []
    for doc in docs:
        for e in doc["edges"]:
            s = by_name.get(normalise(e["source"]))
            t = by_name.get(normalise(e["target"]))
            if s and t:
                db.execute("INSERT INTO relations VALUES (?,?,?,?)",
                           (s, t, e["predicate"], doc["source_doc"]))
            else:
                skipped.append((doc["source_doc"], e))
        for a in doc.get("aliases", []):
            eid = by_name.get(normalise(a["entity"]))
            if eid:
                db.execute("INSERT INTO aliases VALUES (?,?)", (eid, a["alias"]))

    db.commit()
    counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # noqa: S608
              for t in ("entities", "relations", "aliases")}
    print(f"built {DB.name}: {counts['entities']} entities, "
          f"{counts['relations']} relations, {counts['aliases']} aliases "
          f"from {len(files)} docs")
    for doc_name, e in skipped:
        print(f"  skipped edge in {doc_name}: "
              f"{e['source']} --[{e['predicate']}]--> {e['target']} (unknown endpoint)")


if __name__ == "__main__":
    main()
