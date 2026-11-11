# More details

Everything the [README](../README.md) leaves out: reading all your work, costs, how well it works, limits, privacy and the data.

## All your work

Instead of one paper, it can read your recent papers, group them into up to three research areas and ask which to focus on. Give it one of these:

- **A BibTeX file from Google Scholar.** On your Scholar profile, tick the box above your list of papers to select them all, click **Export**, choose **BibTeX**, and attach the file to the chat.
- **Your paper titles**, pasted one per line.
- **Your ORCID**, for example "My ORCID is 0000-0002-1825-0097". It finds your works on OpenAlex, or on your ORCID record if OpenAlex does not know you yet. This needs the internet, which chat apps often block (ChatGPT usually does); it then asks you for one of the other two.

A Google Scholar link alone will not work: Scholar blocks automated access, so it asks for the BibTeX file instead. Reading your work costs more tokens than starting from one paper.

When it reads all your work, it gets your recent works from [OpenAlex](https://openalex.org) by ORCID (or, when OpenAlex has not linked that ORCID, from the public ORCID record, with abstracts from OpenAlex by DOI or title), or from your BibTeX file or titles; with the internet it also looks up their abstracts. It groups them into research areas and proposes the top three. You choose which to prioritize, or accept its default (about half, 30% and 20% of the picks), and it searches each area separately. When the internet is blocked, the script says so and the agent asks for a BibTeX file or titles instead of searching the web.

## Reading budgets

The agent asks how much reading you want, or defaults to Standard. Measured extra tokens on top of an agent's baseline, in tests with Claude subagents (yours may differ):

| Mode | What the agent reads | Extra tokens |
| --- | --- | --- |
| Quick | the ranked list only | a few thousand (estimate) |
| Standard (default) | one line per candidate, then the start of about 30 abstracts | about 35K |
| Deep | the abstracts of all 150 candidates | about 115K |
| All your work, with Standard | your works from OpenAlex, three pools, about 30 abstracts | about 45K (one test) |

## How well does it work?

Checked on six papers from different research areas, with a separate LLM judging every paper in each 150-paper pool on a 0 to 3 scale without knowing which method picked what. Standard picked 56 of the 94 papers rated closely related (rated 2 or more), against 34 for the plain word search, and found all 18 papers rated 3. These are one LLM judge's ratings on six papers, not human ratings, and only Claude agents were used for this. Codex was checked only for running end to end, not for quality. Treat it as a good reading list, not a ground truth.

## Limits

- The word search ranks by overlap, so a shared buzzword can crowd the top of the list. The agent is told to judge, not trust the order.
- Poster board numbers were not published when the data was collected, and sessions can change.
- Author lookup in the NeurIPS data is by name or affiliation. When it reads all your work, OpenAlex sometimes merges different people with similar names, may not know a newer ORCID, or has missing or wrong abstracts, so the agent checks the list with you. From a BibTeX file or titles without the internet it has titles only, which make rougher picks than abstracts.

## Other commands

`who --name "..."` and `who --affil "UT Austin"` look people and institutions up (spelling variants merged), `ics` writes a calendar file, `csv` writes a spreadsheet of the picks.

## Privacy

The search script and the importer send nothing anywhere: they run on your computer, or in your Claude or ChatGPT chat's own sandbox. The one exception is the `profile` command, used when it reads all your work: it sends the name, ORCID or paper titles you give it to api.openalex.org, and an ORCID also to pub.orcid.org, to look up your works. A BibTeX file or titles in a chat without the internet stay in that chat. Whatever you give your agent goes to your agent's provider, as with any use of it.

## Data

A snapshot of public NeurIPS 2026 program data is bundled; no other conference's data is. See [DATA_NOTICE.md](../plugins/conference-picks/skills/conference-picks/DATA_NOTICE.md) for what it contains, where it came from, and how to ask for a correction or removal.
