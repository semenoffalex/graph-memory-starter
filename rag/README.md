# rag

A semantic layer over messy notes. One index, two search legs, no
vector database, no API key. The model is 67 MB and runs on your CPU.

Point your AI assistant at this folder and ask it to set it up. The one paste
that does it is in the repo README.

## What makes this different

Standard RAG chops text into fixed-size windows, embeds them, and
searches by similarity alone. Three changes here, each measured on a
real corpus before it earned its place:

1. Chunks follow the document's own headings, and every chunk carries
   its source label: [file § section]. The label is part of what gets
   embedded and keyword-indexed.
2. Search runs two legs, keyword (BM25) and meaning (embeddings), and
   merges the rankings with reciprocal rank fusion (k=60).
3. Notes can be distilled at write time into the questions you would
   ask later. Distilled entries are indexed beside the chunks, and the
   build checks each entry's quote against its source file. No quote,
   no entry. See distil-prompt.md and distilled/.

Hits return with the lines around them; context lines wear a dot.

Measured on my corpus: 3.1x retrieval quality over the standard build.
The biggest single lever was the embedding model.

## Which model does what

    bge-small-en-v1.5   local, 67 MB, your CPU. Text into 384 numbers, for the
                        meaning leg. Downloaded once on the first build.
    Claude              distils a note into the questions it answers. Through
                        claude -p, on your subscription.

## Setup

    python -m pip install fastembed
    python build_index.py
    python search.py "your question"

First run downloads the model once (67 MB). Without fastembed
installed, search runs keyword-only and says so.

## Test cases

The corpus is ../corpus-before, the same twelve messy docs the graph
was built from. Every row below is a real run.

| Question | Top hits | Why |
|---|---|---|
| what is the mileage rate | expenses.md, both legs | plain keywords, both legs agree |
| how do we talk to customers in writing | handbook § Tone of voice and brand-voice.md, meaning leg | keywords match "in writing" in the wrong doc; meaning finds the right ones |
| who has sign-off while Sarah is away | the distilled entry, then the memo itself | a distilled question meets the question you ask |
| A customer wants an £800 refund in March. Who signs it off? | the £500 rule, first hit | the rule surfaces; chaining March to Marcus is the graph's job, one folder up |

## Your own notes

    python build_index.py --corpus path/to/your/markdown

Markdown files, subfolders included. Hidden folders, `.git`, `node_modules`,
`__pycache__` and this starter's own folder are skipped, so a starter cloned
inside your notes never indexes itself. A note in a subfolder is indexed under
its path inside your notes, so `daily/2026-08-30.md` is found and read back as
that.

Rebuild any time. The files stay the truth; the index is disposable.

## Distil

    python distil.py path/to/your/markdown
    python distil.py path/to/your/markdown --limit 20

One short Claude call per note, so start with a folder of tens. Each answer is
checked before it is kept: it needs a question and a quote, and the quote has
to be in the note word for word. Anything else is dropped and named.

A note already distilled is skipped unless it has changed. State lives in
`distilled/.state.json`, keyed by the note's path with a sha256 of what was
read. The index is rebuilt at the end.

Which Claude it uses is `"model"` in `../digest/config.json`, sonnet by
default.

## The recall hook

    hooks.json  ->  merge into .claude/settings.json

`recall_hook.py` runs on every prompt you submit. It searches the index and
hands the top five hits back as context, under about 1,500 characters, with a
one-line note saying how many. It never blocks a prompt: no index, no hits, or
any failure at all and it prints nothing.

It is a fresh process each time, so it loads the embedding model before every
prompt. Measured on a laptop: about 0.9 seconds with the meaning leg, under
0.1 without it.
