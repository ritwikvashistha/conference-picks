# conference-picks

An agent skill that tells you which papers and authors at a conference are worth your time, given your own work. NeurIPS 2026 is built in; other conferences work from a paper list you bring (see [Other conferences](#other-conferences-experimental), experimental). For NeurIPS, give it your NeurIPS paper (id or link), your name, or an abstract, or, in the optional profile mode, your name, ORCID or a paper list so it can cover all your work. It returns a ranked list with a one-line reason for each pick, grouped by site (Sydney, Atlanta, Paris), session and local time, plus authors worth talking to. It can also write a calendar file and a spreadsheet of the picks.

It runs on your own agent, with no accounts and no API keys. The search script uses only the Python standard library and a bundled snapshot of the NeurIPS 2026 program, taken on 2026-11-04 and 2026-11-05, so sessions may have changed since: check neurips.cc for the official schedule.

## Install

Pick one route. All need Python 3.9 or newer and nothing else. Tested on macOS only, with Python 3.9, 3.10, 3.12 and 3.13; Windows and Linux are untested.

**Claude Code plugin** (recommended):

```bash
claude plugin marketplace add ritwikvashistha/conference-picks
claude plugin install conference-picks@conference-picks
```

The same two commands work inside a session as `/plugin marketplace add ...` and `/plugin install ...`. Then just ask, for example:

> I'm going to NeurIPS 2026. My paper there is id 148353. Which papers should I see?

You can also run it as `/conference-picks:conference-picks`.

**Standalone skill in Claude Code:**

```bash
git clone https://github.com/ritwikvashistha/conference-picks
cp -r conference-picks/plugins/conference-picks/skills/conference-picks ~/.claude/skills/
```

**claude.ai** (the chat in the Claude app, on the web, desktop or phone): download [conference-picks.zip](https://github.com/ritwikvashistha/conference-picks/releases/latest/download/conference-picks.zip) from the latest release and upload it as a skill in your claude.ai settings (skills need code execution turned on). Each person uploads their own copy. Then ask as above; no command is needed. To build the zip yourself, run `python3 tools/make_zip.py`, which writes `dist/conference-picks.zip`. This route is untested, and profile mode needs access to api.openalex.org, which a sandboxed environment may block.

**Codex** (CLI, IDE extension and app): Codex reads the same marketplace files, so the plugin route works the same way. Start a new session afterwards.

```bash
codex plugin marketplace add ritwikvashistha/conference-picks
codex plugin add conference-picks@conference-picks
```

Or install the standalone skill. Codex looks in `~/.agents/skills/` (all projects) and in `.agents/skills/` from the project folder up to the repository root (that repository only):

```bash
git clone https://github.com/ritwikvashistha/conference-picks
mkdir -p ~/.agents/skills
cp -r conference-picks/plugins/conference-picks/skills/conference-picks ~/.agents/skills/
```

Ask the same question as above, or type `$conference-picks`, or pick it with `/skills`.

**Other agents:** untested. Point the agent at `plugins/conference-picks/skills/conference-picks/SKILL.md` and tell it to follow it.

## Other conferences (experimental)

NeurIPS 2026 is bundled. For another conference, bring its paper list as a CSV or JSON file with title, authors and abstract (times are optional). Many conferences publish one on the same website software as NeurIPS: on the Downloads page of the conference site (for example `icml.cc/Downloads/2026`), choose csv and press Download Data. Then ask your question, naming the conference and the file:

> I'm going to ICML 2026. Its paper list is `~/Downloads/ICML 2026 Events.csv`. My abstract is: ...

The agent looks at the file, writes a column mapping, and `scripts/import_dataset.py` checks it. The import writes nothing if the file is not good enough (fewer than 50 records, missing titles, abstracts on under half of the papers, conflicting ids, times without a time zone). Otherwise it saves the dataset in `~/.conference-picks/<name>/` (set `CONFERENCE_PICKS_HOME` to move it) and shows a report with three sample records for you to confirm. If you say something is wrong, the agent fixes the mapping and imports again, or deletes the dataset. Later questions reuse it, and `python3 scripts/search.py list` shows what is installed. If the agent cannot write there (a read-only Codex folder, say), it is told to print the mapping and the import command for you to run in your own terminal.

With no times in the file there is no grouping by session and no calendar file; picks are ranked and the answer says so. A dataset comes from one file: if abstracts and times are in different files, join them first. Status: tested by script on the ICML 2026 CSV and on NeurIPS's raw files. With agents, on the ICML file only and one run each: Claude Code (Sonnet) imported it and gave picks, reused the saved dataset in a second run, and asked for the file when given none; Codex imported it and gave picks where it could write, and printed the import command where it could not (an earlier read-only run, told in advance to accept the report, ran the importer in memory and opened a web page despite the instructions). Not tested: you confirming the report yourself (these runs had it pre-approved or could not write), a conference file with session times, other file formats, claude.ai with this version, Windows and Linux.

### A PDF or text book of abstracts (experimental)

Some conferences publish only a book of abstracts. Give the agent the PDF, or its text, and name the conference; [TEXT_PROGRAMS.md](plugins/conference-picks/skills/conference-picks/TEXT_PROGRAMS.md) tells it what to do. Supported: a single-column book in which every entry is a title, one marker line (`Presenter: Name`, or `Authors: Name (Affil), ...`) and an abstract, under day, time-block and session headings, with footers and page numbers around. Not supported: two-column layouts, scanned books (there is no OCR), tables, figures, and an author list that wraps over several lines. A PDF needs `pdftotext` from poppler: the importer calls `pdftotext -layout` itself when it is on your PATH, and otherwise prints the command (`pdftotext -layout book.pdf book.txt`) for you to run. It installs nothing.

Parsing runs on your machine and costs no tokens. The extra cost is the agent's own turns, once per book (later questions reuse the saved dataset): a structure summary from `inspect` (under 3 KB), the patterns it writes, a retry if a check refuses, and the import report. Measured with Claude Sonnet on the 193-page test book, one run each: $0.49 for one full run (import and picks, 31 turns, an earlier version of the instructions); with the final instructions, $0.25 for the import and report, where the agent stops to ask you, plus $0.26 for the picks in a later run that reuses the saved dataset. The ICML CSV took $0.29 for import and picks, so the book route costs about $0.2 more (about 70%), once per book. A different book, agent or wording will differ. The expensive mistake is putting the book itself into the chat: the 193-page test book is 943,438 characters, about 236K tokens at 4 characters per token (an estimate), so give the agent the file's path and do not attach it.

You get title, abstract, presenter or listed authors, day, time block, session and room, and the book page when the offset between printed and PDF page numbers is known. Only the people the book lists are known, and affiliations only if it prints them, so `who --affil` is weak. Times are those of the session or block, not of each talk. Entries are cut out by patterns, so some can come out wrong: on the real book used for testing, at least 6 of 637 titles were wrong. The import refuses a weekday that does not match its date (that book prints two), until you confirm the real date. The patterns are the agent's: in one run its room pattern missed one session heading and left 4 entries wrong, so check the `text:` line of the report (days, blocks and sessions found) as well as the samples. Status: tested by script on synthetic books and locally on one real 637-entry book; with agents, Claude Sonnet ran it on that book as above (five runs, one book). Not tested: Codex, claude.ai, a second real book, and the Authors layout on a real book.

## Budgets

The agent asks how much reading you want, or defaults to Standard. Measured extra tokens on top of an agent's baseline, in tests with Claude subagents (yours may differ):

| Mode | What the agent reads | Extra tokens |
| --- | --- | --- |
| Quick | the ranked list only | a few thousand (estimate) |
| Standard (default) | one line per candidate, then the start of about 30 abstracts | about 35K |
| Deep | the abstracts of all 150 candidates | about 115K |
| Profile mode, with Standard | your works from OpenAlex, three pools, about 30 abstracts | about 45K (one test) |

## Profile mode (optional, more tokens)

By default the picks are based on one or more NeurIPS 2026 papers. If you would rather base them on your whole body of work, share your Google Scholar link, name, ORCID, a BibTeX export or a list of titles:

> Here is my Google Scholar profile: https://scholar.google.com/citations?user=... Which NeurIPS 2026 papers should I see?

Google Scholar has no API and blocks automated access, so the agent will not try to read it. It asks for your name (and institution) or ORCID instead, or a BibTeX export from your Scholar profile, or pasted titles. It finds your works on [OpenAlex](https://openalex.org), asks you to confirm it has the right person, groups your work into research areas, and proposes your top three. You choose which areas to prioritize, or accept its default (about half, 30% and 20% of the picks). It then searches each area separately. This reads more than a single paper, so it costs more tokens.

## How it works

1. The agent reads your abstract and writes a short keyword brief (other names for your ideas, neighbouring fields).
2. `search.py` ranks all 9,145 posters with an abstract by word overlap with your abstract and the brief, and returns a pool of 150.
3. The agent reads the promising candidates, picks 15 to 25, and explains each one in terms of your work.
4. Output is grouped by site and session time, with times local to each site.

Other commands: `who --name "..."` and `who --affil "UT Austin"` look people and institutions up (spelling variants merged), `ics` writes a calendar file, `csv` writes a spreadsheet of the picks.

## How well does it work?

Checked on six papers from different research areas, with a separate LLM judging every paper in each 150-paper pool on a 0 to 3 scale without knowing which method picked what. Standard picked 56 of the 94 papers rated closely related (rated 2 or more), against 34 for the plain word search, and found all 18 papers rated 3. These are one LLM judge's ratings on six papers, not human ratings, and only Claude agents were used for this. Codex was checked only for running end to end, not for quality. Treat it as a good reading list, not a ground truth.

## Limits

- The word search ranks by overlap, so a shared buzzword can crowd the top of the list. The agent is told to judge, not trust the order.
- Poster board numbers were not published when the data was collected, and sessions can change.
- Author lookup in the NeurIPS data is by name or affiliation. In profile mode, OpenAlex sometimes merges different people with similar names or has missing or wrong abstracts, so the agent checks with you.

## Privacy

The search script and the importer run locally and send nothing anywhere. The one exception is the optional `profile` command in profile mode, which sends the name, ORCID or paper titles you give it to api.openalex.org to look up your works. Whatever you give your agent goes to your agent's provider, as with any use of it.

## Data

A snapshot of public NeurIPS 2026 program data is bundled; no other conference's data is. See [DATA_NOTICE.md](plugins/conference-picks/skills/conference-picks/DATA_NOTICE.md) for what it contains, where it came from, and how to ask for a correction or removal.

## Licence and contact

MIT, see [LICENSE](LICENSE). Contact: ritwikvashistha@gmail.com
