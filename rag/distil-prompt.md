# Distil a note into the questions it answers

Run this prompt over a note. Save the output in distilled/ as markdown.
build_index.py picks it up automatically and verifies the quote before
indexing. No quote, no entry.

---

Read the note below. Produce exactly this format:

    source: <the note's file name>
    - <a question someone would search for months later>
    - <another, phrased the way they would actually ask>
    summary: <one line>
    rule: <the rule or resolution, if the note contains one>
    quote: "<one quote from the note, copied exactly, that proves the answer>"

Ask for the facts: the number, the name, the rule. Do not ask about
the occasion. If no exact quote proves the answer, produce nothing.

---

<paste the note here>
