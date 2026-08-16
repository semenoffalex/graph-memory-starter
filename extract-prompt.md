Read the document below. Extract a knowledge graph using ONLY this vocabulary.

Entity types: PERSON, ROLE, POLICY, PROCESS, DOCUMENT
Relationships: approved_by, held_by, delegates_to, part_of, references

Return JSON:
{"source_doc": "...",
 "nodes": [{"name","type","description"}],
 "edges": [{"source","predicate","target"}],
 "aliases": [{"entity","alias"}]}

Rules:
- Use the most complete form of each name. Add short forms as aliases.
- Put conditions (amounts, dates, time windows) in the entity description.
- Extract only facts stated in the document.
- Every edge endpoint must appear in nodes.
