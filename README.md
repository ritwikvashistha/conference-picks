# neurips-picks

An agent skill that tells you which NeurIPS 2026 papers and authors are worth your time, given your own work. Give it your NeurIPS paper (id or link), your name, or an abstract. It returns a ranked list with a one-line reason for each pick, grouped by site (Sydney, Atlanta, Paris), session and local time, plus authors worth talking to. It can also write a calendar file and a spreadsheet of the picks.

It runs on your own agent, with no accounts and no API keys. The search script uses only the Python standard library and a bundled snapshot of the NeurIPS 2026 program.

## Install

Claude Code:

```bash
git clone https://github.com/ritwikvashistha/neurips-picks ~/.claude/skills/neurips-picks
```

Then start a session and ask, for example:

> I'm going to NeurIPS 2026. My paper there is id 148353. Which papers should I see?

Other routes are not tested yet: uploading the folder as a zip skill on claude.ai, or pointing another coding agent at `SKILL.md` and telling it to follow it.

Requirements: Python 3.9 or newer, nothing else to install.

## Budgets

The agent asks how much reading you want, or defaults to Standard. Measured extra tokens on top of an agent's baseline, in tests with Claude subagents (yours may differ):

| Mode | What the agent reads | Extra tokens |
| --- | --- | --- |
| Quick | the ranked list only | a few thousand (estimate) |
| Standard (default) | one line per candidate, then the start of about 30 abstracts | about 35K |
| Deep | the abstracts of all 150 candidates | about 115K |

## How it works

1. The agent reads your abstract and writes a short keyword brief (other names for your ideas, neighbouring fields).
2. `scripts/search.py` ranks all 9,105 posters with an abstract by word overlap with your abstract and the brief, and returns a pool of 150.
3. The agent reads the promising candidates, picks 15 to 25, and explains each one in terms of your work.
4. Output is grouped by site and session time, with times local to each site.

Other commands: `who --name "..."` and `who --affil "UT Austin"` look people and institutions up (spelling variants merged), `ics` writes a calendar file, `csv` writes a spreadsheet of the picks.

## How well does it work?

Checked on six papers from different research areas, with a separate LLM judging every paper in each 150-paper pool on a 0 to 3 scale without knowing which method picked what. Standard picked 56 of the 94 papers rated closely related (rated 2 or more), against 34 for the plain word search, and found all 18 papers rated 3. These are one LLM judge's ratings on six papers, not human ratings, and only Claude agents have been tested. Treat it as a good reading list, not a ground truth.

## Limits

- The word search ranks by overlap, so a shared buzzword can crowd the top of the list. The agent is told to judge, not trust the order.
- Poster board numbers were not published when the data was collected, and sessions can change.
- Author lookup is by name or affiliation within the NeurIPS data; ORCID is not supported.

## Privacy

The script runs locally and sends nothing anywhere. Whatever you give your agent goes to your agent's provider, as with any use of it.

## Data

A snapshot of public NeurIPS 2026 program data is bundled. See [DATA_NOTICE.md](DATA_NOTICE.md) for what it contains, where it came from, and how to ask for a correction or removal.

## Licence and contact

MIT, see [LICENSE](LICENSE). Contact: ritwikvashistha@gmail.com
