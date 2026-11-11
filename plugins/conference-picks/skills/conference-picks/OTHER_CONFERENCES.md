# Another conference, or the user's own dataset

Read this instead of the NeurIPS-only parts of SKILL.md when the user is not asking about NeurIPS 2026, or gives you a paper list. Steps 2-5 and profile mode work the same, with `--data <slug>` added to every `search.py` command except `profile`. Commands use `${CLAUDE_SKILL_DIR}` as in SKILL.md.

## Ignore, for this conference
- The sites Sydney, Atlanta and Paris, the neurips.cc links, DATA_NOTICE.md and the closing snapshot line.
- Group picks by what `where` shows: a site name if the data has one, else the date and time, and if `where` is `-` for every pick there is no schedule: rank them and say so. Link each title with the `link` column of `csv` or the link in `show`. Close with the dataset's own `notice` from `list`.

## 1. Is the dataset there?
`python3 ${CLAUDE_SKILL_DIR}/scripts/search.py list` prints one dataset per line: slug, name, snapshot, link template, source, notice. If the conference is listed, use its slug. If not, you need a file (step 2). Do not search the web and do not download anything yourself.

## 2. Ask the user for the file
Ask for the conference's paper list as CSV or JSON (title, authors, abstract; times are optional). Many conferences use the same site as NeurIPS: on its Downloads page (for example `icml.cc/Downloads/2026`) choose csv, keep every event type ticked and press Download Data. If the program is only a PDF or text book of abstracts, read `TEXT_PROGRAMS.md` in this folder instead of steps 3-4. If the user has no file, say what is needed and stop.

## 3. Look at it, then write the mapping
`python3 ${CLAUDE_SKILL_DIR}/scripts/import_dataset.py inspect <file>` lists the columns with samples. Write `mapping.json` in your scratch folder, here for a Downloads CSV:

```json
{"fields": {"id": {"column": "virtualsite_url", "regex": "/(\\d+)$"}, "title": "name", "abstract": "abstract", "url": "virtualsite_url", "type": "type"},
 "authors": {"column": "speakers/authors"},
 "meta": {"name": "ICML 2026", "slug": "icml2026", "year": 2026, "paper_types": ["Poster"]}}
```

`authors` is one "Name (Affil), ..." string, or `{"column", "name", "affil"}` for a list of objects. Times: `"start"` and `"end"` under `fields`, plus `"time": {"zone": "Europe/Paris"}` or `{"zones": {"<city>": "<zone>"}}` (add `"city"` under `fields`); ISO times with an offset are converted. `"keep_types"` drops other types. Only set `paper_types` if the file has a type column. Edit the mapping to fit the file; write no parsing scripts.

## 4. Import, then show the user the report
`python3 ${CLAUDE_SKILL_DIR}/scripts/import_dataset.py import <file> --mapping mapping.json` writes to `~/.conference-picks/<slug>/`. Add `--out <folder>` if you cannot write there, and pass the same folder to `--data`. Show the user the report before any picks: the record count, the abstract share, the schedule line, any warning and the three samples, and ask whether names, titles and times look right. The import has already saved the dataset: if the user says something is wrong, fix the mapping and import again (that replaces it), and if it cannot be fixed, delete the folder the import wrote so that later questions do not reuse it. If it refuses, fix the mapping from the message (it lists the real columns) or tell the user what the file lacks. Do not weaken the checks.

If you cannot write files at all, print the mapping JSON and the import command with the real paths (the user saves the mapping to a file first) for the user to run in their own terminal, and wait.

## 5. Then the usual steps
Follow SKILL.md from step 2 with `--data <slug>` on each command, for example `python3 ${CLAUDE_SKILL_DIR}/scripts/search.py find --data <slug> --text-file abstract.txt --text-file brief.txt` (or `--paper <id>` when the user's own paper is in the dataset). Say in your first line which conference and dataset (name and snapshot date) the picks come from.

## Tell the user
- With no schedule there is no calendar and no grouping by time.
- A dataset comes from one file. If abstracts and times are in different files, ask the user to join them first.
- A new site's format can import wrongly: check the three samples.
