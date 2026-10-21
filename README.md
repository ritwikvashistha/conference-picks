# neurips-picks

An agent skill that tells you which NeurIPS 2026 papers and authors are worth your time, given your own work. Give it your NeurIPS paper (id or link), your name, or an abstract, or, in the optional profile mode, your name, ORCID or a paper list so it can cover all your work. It returns a ranked list with a one-line reason for each pick, grouped by site (Sydney, Atlanta, Paris), session and local time, plus authors worth talking to. It can also write a calendar file and a spreadsheet of the picks.

It runs on your own agent, with no accounts and no API keys. The search script uses only the Python standard library and a bundled snapshot of the NeurIPS 2026 program, taken 2026-10-17 to 2026-10-20, so sessions may have changed since: check neurips.cc for the official schedule.

## Install

Pick one route. All need Python 3.9 or newer and nothing else. Tested on macOS only, with Python 3.9, 3.10 and 3.13; Windows and Linux are untested.

**Claude Code plugin** (recommended):

```bash
claude plugin marketplace add ritwikvashistha/neurips-picks
claude plugin install neurips-picks@neurips-picks
```

The same two commands work inside a session as `/plugin marketplace add ...` and `/plugin install ...`. Then just ask, for example:

> I'm going to NeurIPS 2026. My paper there is id 148353. Which papers should I see?

You can also run it as `/neurips-picks:neurips-picks`.

**Standalone skill in Claude Code:**

```bash
git clone https://github.com/ritwikvashistha/neurips-picks
cp -r neurips-picks/plugins/neurips-picks/skills/neurips-picks ~/.claude/skills/
```

**claude.ai:** run `python3 tools/make_zip.py` to build `dist/neurips-picks.zip`, then upload it as a skill in your claude.ai settings. This route is untested, and profile mode needs access to api.openalex.org, which a sandboxed environment may block.

**Codex** (CLI, IDE extension and app): Codex reads the same marketplace files, so the plugin route works the same way. Start a new session afterwards.

```bash
codex plugin marketplace add ritwikvashistha/neurips-picks
codex plugin add neurips-picks@neurips-picks
```

Or install the standalone skill. Codex looks in `~/.agents/skills/` (all projects) and in `.agents/skills/` from the project folder up to the repository root (that repository only):

```bash
git clone https://github.com/ritwikvashistha/neurips-picks
mkdir -p ~/.agents/skills
cp -r neurips-picks/plugins/neurips-picks/skills/neurips-picks ~/.agents/skills/
```

Ask the same question as above, or type `$neurips-picks`, or pick it with `/skills`. See "Using it in Codex" below for what was tested and what limits apply.

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

Checked on six papers from different research areas, with a separate LLM judging every paper in each 150-paper pool on a 0 to 3 scale without knowing which method picked what. Standard picked 56 of the 94 papers rated closely related (rated 2 or more), against 34 for the plain word search, and found all 18 papers rated 3. These are one LLM judge's ratings on six papers, not human ratings, and only Claude agents were used for this. Codex was checked only for running end to end (see "Using it in Codex"), not for quality. Treat it as a good reading list, not a ground truth.

## Using it in Codex

Checked on 2026-10-20 on macOS with Codex CLI 0.163.0-alpha.10.2 (the CLI bundled with the ChatGPT desktop app). In five sessions with the skill in a project's `.agents/skills/` folder, and in one with the plugin installed from a local checkout, the prompt "I'm going to NeurIPS 2026, my paper is id 148353, which papers should I see?" was enough for Codex to pick up the skill, run the bundled script and return a grouped list; one session also produced a calendar. After installing from this repository on GitHub with the commands above, a shorter session found the skill and ran its script from the plugin cache. The Codex docs describe no equivalent of `${CLAUDE_SKILL_DIR}`, and in these sessions Codex read SKILL.md as plain text and substituted the skill folder's path itself.

Not tested: the IDE extension, the desktop app's own chat, Windows and Linux, a full picks session after the GitHub install (only a short check was run), and the `~/.agents/skills/` location. Result quality was not evaluated, and the numbers in this README come from Claude agents only. One Codex session reported about 320K input tokens (about 264K cached) and 8K output tokens, which is counted differently from the Claude figures above, so do not compare them.

Codex's sandbox changes what works:

- **Network is off by default**, so profile mode cannot reach api.openalex.org. The `profile` command then prints "OpenAlex request failed" and the agent should offer another input (BibTeX, titles or NeurIPS ids). The Codex docs give two ways to allow it: start Codex with `-c 'sandbox_workspace_write.network_access=true'`, or set `network_access = true` under `[sandbox_workspace_write]` in `~/.codex/config.toml`. Only the first was tried, together with `-c 'sandbox_mode="workspace-write"'`, and it worked in one profile-mode session. Profile mode also saves `profile.json`, so it needs a writable sandbox too. The default search needs no network.
- **Profile mode ran end to end once in Codex** (a well-known researcher's name, network allowed for that run): OpenAlex lookup, three areas, a search per area, and a 20-pick list in the skill's format with the default 50/30/20 split. That session used about 1.7M input tokens (about 1.6M cached) and 19K output tokens, against about 0.3M input for the single-paper sessions. Besides the skill's steps, the agent wrote its own OpenAlex download scripts (one got an HTTP 401), ran three web searches and fetched 23 neurips.cc pages to check session times. One session and one researcher, so do not expect these numbers.
- **A folder Codex has not marked as trusted started read-only** in my `codex exec` tests. The agent then cannot write scratch files or `.ics` and `.csv` files. SKILL.md tells it to pass the search brief inline and print deliverables in its reply, and that worked for a calendar request. In `workspace-write`, `/tmp` and the project folder are writable.
- `codex exec` cannot answer the budget question, so it uses Standard.
- In six of the seven sessions Codex read part or most of `search.py` before using it, which adds tokens.

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
