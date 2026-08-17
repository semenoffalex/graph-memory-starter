# rag

A semantic layer over messy notes. One index, two search legs, no
vector database, no API key. The model is 67 MB and runs on your CPU.

Point your AI assistant at this folder and ask it to set it up.

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

## Setup

    pip install fastembed
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

Rebuild any time. The files stay the truth; the index is disposable.
