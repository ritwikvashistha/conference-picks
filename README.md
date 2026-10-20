# neurips-picks

An agent skill that tells you which NeurIPS 2026 papers and authors are worth your time, given your own work. Give it your NeurIPS paper (id or link), your name, or an abstract, or, in the optional profile mode, your name, ORCID or a paper list so it can cover all your work. It returns a ranked list with a one-line reason for each pick, grouped by site (Sydney, Atlanta, Paris), session and local time, plus authors worth talking to. It can also write a calendar file and a spreadsheet of the picks.

It runs on your own agent, with no accounts and no API keys. The search script uses only the Python standard library and a bundled snapshot of the NeurIPS 2026 program.

## Install

Pick one route. All need Python 3.9 or newer and nothing else.

**Claude Code plugin** (recommended):

```bash
claude plugin marketplace add ritwikvashistha/neurips-picks
claude plugin install neurips-picks@neurips-picks
```

The same two commands work inside a session as `/plugin marketplace add ...` and `/plugin install ...`. While the repository is private, you need GitHub access to it. Then just ask, for example:

> I'm going to NeurIPS 2026. My paper there is id 148353. Which papers should I see?

You can also run it as `/neurips-picks:neurips-picks`.

**Standalone skill in Claude Code:**

```bash
git clone https://github.com/ritwikvashistha/neurips-picks
cp -r neurips-picks/plugins/neurips-picks/skills/neurips-picks ~/.claude/skills/
```

**claude.ai:** run `python3 tools/make_zip.py` to build `dist/neurips-picks.zip`, then upload it as a skill in your claude.ai settings. This route is untested, and profile mode needs access to api.openalex.org, which a sandboxed environment may block.

**Other agents:** untested. Point the agent at `plugins/neurips-picks/skills/neurips-picks/SKILL.md` and tell it to follow it.

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
2. `search.py` ranks all 9,105 posters with an abstract by word overlap with your abstract and the brief, and returns a pool of 150.
3. The agent reads the promising candidates, picks 15 to 25, and explains each one in terms of your work.
4. Output is grouped by site and session time, with times local to each site.

Other commands: `who --name "..."` and `who --affil "UT Austin"` look people and institutions up (spelling variants merged), `ics` writes a calendar file, `csv` writes a spreadsheet of the picks.

## How well does it work?

Checked on six papers from different research areas, with a separate LLM judging every paper in each 150-paper pool on a 0 to 3 scale without knowing which method picked what. Standard picked 56 of the 94 papers rated closely related (rated 2 or more), against 34 for the plain word search, and found all 18 papers rated 3. These are one LLM judge's ratings on six papers, not human ratings, and only Claude agents have been tested. Treat it as a good reading list, not a ground truth.

## Limits

- The word search ranks by overlap, so a shared buzzword can crowd the top of the list. The agent is told to judge, not trust the order.
- Poster board numbers were not published when the data was collected, and sessions can change.
- Author lookup in the NeurIPS data is by name or affiliation. In profile mode, OpenAlex sometimes merges different people with similar names or has missing or wrong abstracts, so the agent checks with you.

## Privacy

The search script runs locally and sends nothing anywhere. The one exception is the optional `profile` command in profile mode, which sends the name, ORCID or paper titles you give it to api.openalex.org to look up your works. Whatever you give your agent goes to your agent's provider, as with any use of it.

## Data

A snapshot of public NeurIPS 2026 program data is bundled. See [DATA_NOTICE.md](plugins/neurips-picks/skills/neurips-picks/DATA_NOTICE.md) for what it contains, where it came from, and how to ask for a correction or removal.

## Licence and contact

MIT, see [LICENSE](LICENSE). Contact: ritwikvashistha@gmail.com
