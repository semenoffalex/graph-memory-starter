# graph-memory-starter

A knowledge graph your AI assistant reads before it answers.
Three SQLite tables, one recursive query, one prompt hook. No server, no API key.
Purpose: demonstrate the design's effectiveness so you can apply it to your own system.

## Which one

    rag/    works on notes as they are, matches meaning when words differ
    graph   modelled docs, typed links, multi-hop answers walked by code

Start with rag/. Move up when your questions chain facts across
documents and you are willing to model for it.

## Set up

Two pastes, both for Claude Code, opened in the folder you keep your notes in.
The first is the RAG. The second is the digest, which turns every session you
close into a note the RAG can find.

Check Python first. In a terminal, try `python3 --version`, then
`python --version`, then `py --version`. One of them prints a 3.x version. If
none does, install Python from python.org with "Add to PATH" ticked.

### Paste one, the RAG

```
Set up the memory starter for me, one step at a time, and stop if a step fails.
1. Check Python 3 runs here (try python3, python, then py). If none runs, stop and tell me to install it from python.org with "Add to PATH" ticked.
2. Clone https://github.com/Glitch-Cat-Club/graph-memory-starter into a folder called memory-starter (no git installed: download the zip from that page and unzip it as memory-starter), then run: python -m pip install fastembed
3. Ask me which folder my markdown notes are in. Then run: python memory-starter/rag/build_index.py --corpus <that folder>
4. Run: python memory-starter/rag/search.py "a question about my notes" and show me the top hits.
5. Merge the recall hook from memory-starter/rag/hooks.json into .claude/settings.json here. Keep any permissions and model already in it. Use python3 in the hook command if that is the one that runs.
6. Tell me in five lines what you did.
```

Then `/exit` and open Claude Code again, so the hook loads.

### Paste two, the digest

```
Add the digest to my memory starter, one step at a time, and stop if a step fails.
1. Merge the hooks from memory-starter/digest/hooks.json into .claude/settings.json here. Keep any permissions and model already in it.
2. Open memory-starter/digest/config.json. Set "mode" to "headless". If claude -p does not run from this folder (try: claude -p "say ok"), set "mode" to "session" instead and tell me.
3. Tell me in three lines where the daily log will land and how to switch the digest off.
```

Then `/exit` and open Claude Code again.

### Which model does what

    bge-small-en-v1.5   local, 67 MB, your CPU, no key. Turns text into 384
                        numbers for the meaning leg of the search. Downloaded
                        once on the first index build, by fastembed.
    Claude              distils a note into questions, writes the session
                        entry, answers you. Through claude -p on your
                        subscription, so no API key here either.

Markdown files, subfolders included. Hidden folders, `.git`, `node_modules`,
`__pycache__` and this starter's own folder are skipped, so a starter cloned
inside your notes never indexes itself.

### The two digest modes

    session    the filtered text waits in digest/pending/. Your next session
               opens by writing the entry in front of you.
    headless   the hook starts claude -p with no window. The entry lands about
               a minute later, and your next session opens clean.

One switch, `"mode"` in `digest/config.json`. Headless needs `claude` on your
PATH.

### The dials

All of them are one line in `digest/config.json`, apart from the voice, which
is `digest/digest-prompt.md`.

    max_turns    30       how much of the session is read
    max_chars    15000    the character budget, the end kept
    min_turns    5        below this the session is not memory
    model        sonnet   which Claude writes the entry
    log_dir      daily    the folder inside your notes the entry lands in
    distil       true     whether the entry feeds the index
    mode         session  session or headless

What is kept from a session is not a dial, it is code: your words and the
replies. Tool calls, results, file dumps and thinking are dropped before any
model reads it, so nothing is judged out by mistake.

### Switch it off

Delete the hook lines from `.claude/settings.json`. Your notes and daily logs
stay. The index is disposable, rebuild it any time.

## Prerequisites

Python 3, SQLite included. Claude Code, or another assistant with prompt hooks.
For the meaning leg of the search, `python -m pip install fastembed`. Without
it the search runs keyword only and says so. The graph half needs nothing
installed.

## Layout

    rag/               the semantic layer: index, search, recall hook, distil
    digest/            the session write up: hooks, config, prompt
    corpus/            8 modelled docs (front matter)
    corpus-before/     12 unstructured docs (the A/B control)
    extraction/        LLM output per doc: nodes, edges, aliases
    src/               schema.sql, build_graph.py, recall.py, recall_hook.py
    hooks.json         the graph recall hook, copy into .claude/settings.json
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
