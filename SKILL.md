---
name: neurips-picks
description: Find the NeurIPS 2026 papers and authors most relevant to the user's own work, grouped by site, session and local time. Use when the user is attending NeurIPS 2026 and gives their paper (NeurIPS link, id or abstract), their name, or asks what to see.
---

# NeurIPS 2026 picks

Everything runs locally with Python 3.9+ (standard library only). Paths below are relative to this folder.

## 1. Get the user's work
- A NeurIPS 2026 paper (link or id, repeatable): `python3 scripts/search.py show <id>[,<id>...]` prints its abstract and, if scheduled, where it is. Read it first: you need it to judge relevance.
- Their name: `python3 scripts/search.py who --name "First Last"` lists their NeurIPS 2026 papers. Confirm with the user that these are theirs, then use the ids as above.
- Pasted abstract(s): use the text as given.
- ORCID is not supported yet. Ask for a paper link, name or abstract.

## 2. Pick a budget
Ask once. If you cannot ask, use Standard. Say the cost to the user in your first message (in the final one if you cannot talk first).

| Mode | What you read | Extra tokens on top of your session's baseline (measured; yours may differ) |
|---|---|---|
| Quick | the ranked list only | a few K (estimate) |
| Standard (default) | one line per candidate, then the first 700 characters of ~30 abstracts | ~35K |
| Deep | the abstracts of all 150 candidates | ~115K |

These come from test runs where a do-nothing agent run alone counted ~52K tokens of fixed overhead, so the totals were about 88K for Standard and 167K for Deep.

## 3. Search
First write a search brief from the user's abstract(s), before you look at any candidates: about 25 short phrases (1-4 words; a few more is fine), one per line, saved to `brief.txt` in the current folder. Cover the core problems and methods, the names other communities use for the same ideas, and neighbouring subfields where similar problems are studied, even when they share no words with the abstract. Keyword search cannot cross a vocabulary gap by itself; the brief helps. It is scored as one extra query, weighted like one of the user's abstracts, so it adds reach without replacing them.

`python3 scripts/search.py find --paper <id> [--paper <id> ...] --text-file brief.txt` prints 150 candidates as TSV: rank, id, score, where, title, matched terms. For pasted abstracts, save them to `abstract.txt` and use `--text-file abstract.txt --text "$(cat brief.txt)"`. The user's own papers are excluded. The order comes from keyword overlap, and a shared buzzword (for example "MMD") can fill the top ranks with weak matches while strong ones sit at rank 15-100: judge, do not trust the order. The matched terms mix whole phrases and single words, so treat them as hints. A `[oral]` tag in `where` marks an oral paper.

Keep every `show` output under about 15 KB, because bigger outputs get truncated or saved to a file you then have to hunt for: run `show` in batches of at most 12 ids (10 for Deep).

- **Quick:** take the top 20. Run `python3 scripts/search.py show <their ids> --no-abstract` to get authors. The reason for each is its matched terms; claim nothing more.
- **Standard:** from the 150 lines choose the ~30 most promising (title and matched terms; when unsure, keep it). Run `python3 scripts/search.py show <ids> --chars 700` in batches. Keep the best.
- **Deep:** run `show` on all 150 ids in batches, without `--chars`. Keep the best.

## 4. Judge
Relevant means the user would learn something from the paper or gain from talking to its authors, given their own abstract. Rank them; no tiers. Give one concrete reason per paper that points at the user's work (a shared problem, method or data), not just a shared keyword. Aim for 15-20 picks; go up to 25 when the topic is broad and many candidates are strong; fewer is fine when the rest are weak. Do not pad.

## 5. Output
Markdown. First line: where and when the user's own papers are presented; say "no session scheduled yet" for one without a slot.

Group the picks by site (Sydney, Atlanta, Paris), then by session time, in date order. The `where` column already has the weekday, date and local time at that site, so copy it as given. Put picks with `-` under "Location not yet known" last, in rank order. Inside a group, order by your ranking and keep the overall rank on every line (for example `#3`), so the ranking is not lost by grouping.

Per paper: title linked to `https://neurips.cc/virtual/2026/poster/<id>`, authors, one reason. End with up to 8 authors worth talking to (people on several picks; if nobody repeats, the authors of the picks closest to the user's work) and why. Leave out the user's own co-authors, and mark any pick that is in the same session slot as one of the user's own papers ("same slot as your poster").

If the user wants a calendar file: `python3 scripts/search.py ics <picked ids> > neurips-picks.ics` (times are converted to UTC; picks without a session yet are skipped and reported). To find other people from the user's institution: `python3 scripts/search.py who --affil "UT Austin"` (any common name or acronym works: "MIT", "Tsinghua", "Google DeepMind"; spelling variants are merged). The first line gives the number of papers and author slots and the split by site. Unknown names fall back to a regex on the raw affiliation.

If the user wants a spreadsheet to share with labmates: write one line per pick to a file, `<id><TAB><one-line reason>`, best first, then run `python3 scripts/search.py csv <picked ids> --reasons reasons.tsv > neurips-picks.csv`. Columns: rank, id, title, authors, institutions, site, session, local start and end, hall, oral, link, reason.

Data sources, terms and how to request a correction: see `DATA_NOTICE.md` in this folder.
