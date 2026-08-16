# graph-memory-starter

A knowledge graph your AI assistant reads before it answers.
Three SQLite tables, one recursive query, one prompt hook. No server, no API key.
Purpose: demonstrate the design's effectiveness so you can apply it to your own system.

## Prerequisites

Python 3 (SQLite included). An AI coding assistant with prompt hooks, e.g. Claude Code.
Nothing to install.

## Layout

    corpus/            8 modelled docs (front matter)
    corpus-before/     12 unstructured docs (the A/B control)
    extraction/        LLM output per doc: nodes, edges, aliases
    src/               schema.sql, build_graph.py, recall.py, recall_hook.py
    hooks.json         copy into .claude/settings.json
    extract-prompt.md  the extraction prompt, for your own docs

## Modelling

Ontology: a closed vocabulary, fixed before writing any doc.
Entity types: PERSON, ROLE, POLICY, PROCESS, DOCUMENT.
Relationships: approved_by, held_by, delegates_to, part_of, references.
Logical model: entities with hashed identity (uuid5 of type + name), typed
relations carrying their source doc, aliases for name variants. Each doc
declares its type, entities and links in front matter.
Apply the same design to your own docs; your AI assistant can do the extraction.

## Run

    python src/build_graph.py
    python src/recall.py "A customer wants an £800 refund in March. Who signs it off?"

Wire hooks.json and the same lookup runs before every prompt, injected as context.

## Test cases

| Question | Expected | Why |
|---|---|---|
| A customer wants an £800 refund in March. Who signs it off? | Marcus Webb | 3 hops: policy, role, holder, delegate |
| Who approves supplier payments over £2,000? | Alex Doyle | 2 hops: policy, role, holder |
| What is the onboarding process? | Ops Manager, day-one checklist | 1 hop, several edges |
| What does Priya do? | Support Lead | alias seeding |
| Who is in charge when the boss is away? | no memory matches | outside the vocabulary; fails loudly, never guesses |

## Evals

Glitch Cat Club evals, Aug 2026. One question, three model tiers, two conditions.
The answer needs a 3-hop chain: policy -> role -> holder -> delegate.

Search condition: ask in corpus-before/, no hook. Tooling: the model drives
Grep and Read itself.
Graph condition: wire hooks.json and ask. Tooling: a SQLite recursive query
runs inside the hook before the model is invoked; the model receives the
result as text. Reproduce both yourself.

| Model   | Condition | Tooling          | Result  | Hops reached | Tool calls | Docs read | Context read |
|---------|-----------|------------------|---------|-------------:|-----------:|----------:|-------------:|
| Fable 5 | search    | Grep+Read, model | correct |       3 of 3 |          6 |         4 |  ~780 tokens |
| Fable 5 | graph     | SQL walk, code   | correct |       3 of 3 |          0 |         0 |  ~400 tokens |
| Sonnet  | search    | Grep+Read, model | correct |       3 of 3 |         13 |         8 | ~1180 tokens |
| Sonnet  | graph     | SQL walk, code   | correct |       3 of 3 |          0 |         0 |  ~400 tokens |
| Haiku   | search    | Grep+Read, model | wrong   |       1 of 3 |          5 |         3 |  ~660 tokens |
| Haiku   | graph     | SQL walk, code   | correct |       3 of 3 |          0 |         0 |  ~400 tokens |

Retrieval: 2 ms per query. The ~400-token injection is fixed at any corpus size;
search reads grow with it. Live terminal runs: 20 s of visible searching vs an
answer that starts immediately after the 2 ms recall line.

In the graph condition the model does no retrieval. Zero tool calls, zero
searching, zero multi-hop reasoning: the traversal ran as code before the model
was invoked, and the model reads the injected facts and states the answer.
Proof: the smallest model reaches 1 of 3 hops searching, and 3 of 3 through the
graph, because the graph walks the hops, never the model. Two places a model
still exists: one call speaks the final answer, and a strong model built the
graph once at write time. Spend intelligence at build; answer from structure.
