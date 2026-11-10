---
name: conference-picks
description: Pick the NeurIPS 2026 papers and authors most relevant to the user's own work, grouped by site, session and local time. Also works for another conference from a dataset the user supplies. Use when the user is attending NeurIPS 2026 or another conference and gives a paper, name, Google Scholar link or abstract, or asks what to see.
---

# NeurIPS 2026 picks

Everything runs locally with Python 3.9+ (standard library only), except the optional `profile` command in profile mode, which contacts OpenAlex. Do not fetch neurips.cc or other web pages to check or fill in details: the bundled data already holds the sessions and times.

For another conference, or a dataset the user supplies, read `OTHER_CONFERENCES.md` in this folder first: it overrides the NeurIPS-specific parts below.

Commands use `${CLAUDE_SKILL_DIR}`, the folder that holds this SKILL.md. Claude Code expands it; other agents (such as Codex) do not, so use that folder's real path instead. Put working files (`brief.txt`, `profile.json`, pool files) in a scratch folder such as `/tmp/conference-picks/` (create it first) and pass full paths, not in the user's project. If you cannot write files (read-only sandbox), pass the brief inline with `--text` and print any deliverable in your reply. Write deliverables (`.ics`, `.csv`) to the current folder.

If you cannot run these scripts or open this folder's files (some chat apps load only a skill's text), ask the user to attach the zip they installed from (`conference-picks-chatgpt.zip` or `conference-picks.zip`, both at https://github.com/ritwikvashistha/conference-picks/releases/latest), unzip it and use the folder in it that holds SKILL.md. Never search the web instead, and never invent papers.

## 1. Get the user's work
Two ways in. The default is cheaper; profile mode is optional and costs more tokens (see "Profile mode" below).

- **Default: one or more NeurIPS 2026 papers** (link or id, repeatable): `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py show <id>[,<id>...]` prints its abstract and, if scheduled, where it is. Read it first: you need it to judge relevance.
- Their name: `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py who --name "First Last"` lists their NeurIPS 2026 papers. Confirm with the user that these are theirs, then use the ids as above.
- Pasted abstract(s): use the text as given.
- **Optional: profile mode**, when the user gives a Google Scholar link, ORCID, a BibTeX export or a list of titles, or wants coverage beyond one paper. Go to "Profile mode".

## 2. Pick a budget
Ask once. If you cannot ask, use Standard. Say the cost to the user in your first message (in the final one if you cannot talk first).

| Mode | What you read | Extra tokens on top of your session's baseline (measured; yours may differ) |
|---|---|---|
| Quick | the ranked list only | a few K (estimate) |
| Standard (default) | one line per candidate, then the first 700 characters of ~30 abstracts | ~35K |
| Deep | the abstracts of all 150 candidates | ~115K |

These come from test runs where a do-nothing agent run alone counted ~52K tokens of fixed overhead, so the totals were about 88K for Standard and 167K for Deep. Profile mode with Standard adds the cost of reading the user's works and triaging three pools: about 45K extra in one test (about 10K more than Standard on NeurIPS papers; the run counted ~97K in total). Tell the user it costs more than giving NeurIPS papers.

## 3. Search
First write a search brief from the user's abstract(s), before you look at any candidates: about 25 short phrases (1-4 words; a few more is fine), one per line, saved to `brief.txt` in the scratch folder. Cover the core problems and methods, the names other communities use for the same ideas, and neighbouring subfields where similar problems are studied, even when they share no words with the abstract. Keyword search cannot cross a vocabulary gap by itself; the brief helps. It is scored as one extra query, weighted like one of the user's abstracts, so it adds reach without replacing them.

`python3 ${CLAUDE_SKILL_DIR}/scripts/search.py find --paper <id> [--paper <id> ...] --text-file brief.txt` prints 150 candidates as TSV: rank, id, score, where, title, matched terms. For pasted abstracts, save them to `abstract.txt` and use `--text-file abstract.txt --text-file brief.txt` (each file is one query). The user's own papers are excluded. The order comes from keyword overlap, and a shared buzzword (for example "MMD") can fill the top ranks with weak matches while strong ones sit at rank 15-100: judge, do not trust the order. The matched terms mix whole phrases and single words, so treat them as hints. A `[oral]` tag in `where` marks an oral paper.

Keep every `show` output under about 15 KB, because bigger outputs get truncated or saved to a file you then have to hunt for: run `show` in batches of at most 12 ids (10 for Deep).

- **Quick:** take the top 20. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py show <their ids> --no-abstract` to get authors. The reason for each is its matched terms; claim nothing more.
- **Standard:** from the 150 lines choose the ~30 most promising (title and matched terms; when unsure, keep it). Run `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py show <ids> --chars 700` in batches. Keep the best.
- **Deep:** run `show` on all 150 ids in batches, without `--chars`. Keep the best.

## 4. Judge
Relevant means the user would learn something from the paper or gain from talking to its authors, given their own abstract. Rank them; no tiers. A paper that shares an author with the user's own paper(s) is their group's work: do not rank it, name it in one closing line instead. Give one concrete reason per paper that points at the user's work (a shared problem, method or data), not just a shared keyword. Aim for 15-20 picks; go up to 25 when the topic is broad and many candidates are strong; fewer is fine when the rest are weak. Do not pad.

## 5. Output
Markdown. First line: where and when the user's own papers are presented; say "no session scheduled yet" for one without a slot.

Group the picks by site (Sydney, Atlanta, Paris), then by session time, in date order. The `where` column already has the weekday, date and local time at that site, so copy it as given. Put picks with `-` under "Location not yet known" last, in rank order. Inside a group, order by your ranking and keep the overall rank on every line (for example `#3`), so the ranking is not lost by grouping.

Per paper: title linked to `https://neurips.cc/virtual/2026/poster/<id>`, authors, one reason. End with up to 8 authors worth talking to (people on several picks; if nobody repeats, the authors of the picks closest to the user's work) and why. Leave out the user's own co-authors, and mark any pick that is in the same session slot as one of the user's own papers ("same slot as your poster"). Add a last line saying the times come from a snapshot (date in `DATA_NOTICE.md`) and may have changed.

If the user wants a calendar file: `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py ics <picked ids> > conference-picks.ics` (times are converted to UTC; picks without a session yet are skipped and reported). To find other people from the user's institution: `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py who --affil "UT Austin"` (any common name or acronym works: "MIT", "Tsinghua", "Google DeepMind"; spelling variants are merged). The first line gives the number of papers and author slots and the split by site. Unknown names fall back to a regex on the raw affiliation.

If the user wants a spreadsheet to share with labmates: write one line per pick to a file, `<id><TAB><one-line reason>`, best first, then run `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py csv <picked ids> --reasons reasons.tsv > conference-picks.csv`. Columns: rank, id, title, authors, institutions, site, session, local start and end, hall, oral, link, reason.

## Profile mode (optional, more tokens)
Use it when the user wants the picks based on their whole body of work, not one paper. It replaces steps 1 and 3; steps 2, 4 and 5 still apply, with the changes below.

**P1. Get the works.**
- **Google Scholar link:** say you cannot read Scholar reliably: it has no API, its terms bar automated access against its own rules, and it blocks automated requests. Never try to get past a block or a CAPTCHA. Ask for one of these instead: their name (and institution) or ORCID; a BibTeX export from their Scholar profile (profiles have an Export option for selected papers); a pasted list of titles; or their NeurIPS 2026 paper ids. Only if the user explicitly asks you to try the profile page with your own fetch tool, read the first page only and stop at any block.
- **Name:** `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py profile --name "First Last" --affil "<institution>"` lists matching OpenAlex authors. Names are ambiguous and OpenAlex sometimes merges different people, so show the user the institutions and topics and confirm which one is them. If none fits, ask for an ORCID or use another input.
- **Then** `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py profile --id A... --save profile.json` (or `--orcid 0000-...`). It lists their works from the last 5 years, newest first (`--since YEAR` and `-n` change that), with short abstracts. Drop works that are clearly not theirs. OpenAlex abstracts can be missing or wrong: ignore one that does not fit its title.
- **BibTeX or titles:** `profile --bibtex scholar.bib --lookup --save profile.json` or `profile --titles-file titles.txt --lookup --save profile.json`. `--lookup` fetches abstracts from OpenAlex by title; some papers will not be found, and titles alone make weak queries.
- If the user has NeurIPS 2026 papers (`who --name` finds them), also run `show <ids> --no-abstract` for them: you need their session slots and co-authors for step 5. Use them as `--paper` in P3 for the area they belong to.
- If you cannot ask the user to confirm the OpenAlex author, choose the candidate whose institution matches the one the user gave and whose recent works fit their field, and say so.
- The `profile` command sends only the name, ORCID or titles you give it to api.openalex.org (an ORCID also to pub.orcid.org). If it fails, do what its message says.

**P2. Propose areas.** Group the works into research areas. Propose the three most important, ranked, each with one line and its work numbers. Weigh recent output and what the user cares about. Ask which areas to prioritize. The default is your three in your order, with about half, 30% and 20% of the picks. If you cannot ask or get no answer, use the default. The user can pick one to three areas, reorder them, or name their own.

**P3. Search per area.** Keep `profile.json`, the briefs and the pool files in one working folder and pass full paths. For each prioritized area, write a brief for that area as in step 3, then run `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py find --profile profile.json --use <work numbers of that area> --text-file brief_<n>.txt --exclude-name "<the user's name>" -k 60 > pool_<n>.tsv`. Add `--paper <id>` for their NeurIPS 2026 papers in that area, if any. Read each pool file in full (about 9 KB each). Triage across the pools, then read about 10 abstracts per area with `show --chars 700` in batches of at most 12. A paper in two pools counts once. If an area has no strong candidates, give it fewer picks and say so; do not pad.

**P4. Pick and output.** Pick 15-25 in total, split across the areas as agreed, and label every pick with its area. Output as in step 5, plus a closing line giving the number of picks per area. For Quick, take the top picks of each pool; for Deep, read more per area.

Data sources, terms and how to request a correction: see `DATA_NOTICE.md` in this folder.
