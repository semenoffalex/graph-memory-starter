CREATE TABLE entities  (id TEXT PRIMARY KEY,   -- uuid5(type + normalised name)
                        name TEXT, type TEXT,
                        description TEXT, source_doc TEXT);
CREATE TABLE relations (source_id TEXT, target_id TEXT,
                        predicate TEXT, source_doc TEXT);
CREATE TABLE aliases   (entity_id TEXT, alias TEXT);
