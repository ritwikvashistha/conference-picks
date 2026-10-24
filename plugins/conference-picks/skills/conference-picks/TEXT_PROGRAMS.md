# A book of abstracts (PDF or text)

Read this instead of steps 3-4 of `OTHER_CONFERENCES.md` when the program is a book of abstracts as a PDF or text file, not a CSV or JSON; steps 1, 2 and 5 stay. Say in your first line that the entries were cut out of the book by patterns, so a few may be wrong.

## Keep the book out of the chat
- The script reads the book on this machine for free. Give it the book by path. Never read, paste or attach the book or its text, and never open the PDF with a file-reading tool, beyond the lines `inspect` prints and a few dozen lines of the text (read them with an offset and a limit): a 190-page book is about 940,000 characters, roughly 235K tokens (estimate).
- Your cost is the `inspect` output (under 3 KB), the mapping, any retry and the report. Write no parsing scripts: edit the mapping.
- From a PDF, run `pdftotext -layout book.pdf <scratch folder>/book.txt` (poppler) and use that .txt from then on; the script also takes the .pdf, but you cannot look at a PDF cheaply. If `pdftotext` is missing, tell the user the command `pdftotext -layout book.pdf book.txt` and stop. Never install anything.

## What it handles
One column of text. Each entry is a title (may wrap), one marker line (`Presenter: Name`, or `Authors: Name (Affil), ...`) and the abstract, with a blank line before the next entry. Day, time-block and session headings above the entries carry forward; footers and page numbers are dropped. Not handled: two columns, scanned books (no OCR), tables, figures, an author list wrapped over several lines. If the book is not like this, say so and stop.

## 1. Look, then write the mapping
`python3 ${CLAUDE_SKILL_DIR}/scripts/import_dataset.py inspect <book.txt or book.pdf>` prints counts, marker candidates, the lines around the first entry (with line numbers), day and time heading shapes, room-like endings and repeated lines (footers). Patterns are Python regular expressions, searched on each stripped line: anchor them with `^` and `$`. `start_after`: the first matching line starts the body (use the first day heading, not its contents line, which has dots and a page number). `end_before`: ends it: `inspect` shows the lines after the last entry, so if an index follows, give its heading (if it is not shown, read a few lines around the end of the text). `time.zone` is the venue's: read the first 20 lines of the text for it, or ask the user; never guess. `drop`: footers and page numbers. Use the exact room values `inspect` shows: a wider pattern such as `\d{4}` also matches a year in a title. A heading wrapped over two lines is joined for you. Every named group becomes a column beside `title`, `abstract` and `day`; `start` and `end` become `YYYY-MM-DD HH:MM`. A book with sessions and rooms:

```json
{"text": {"year": 2027, "start_after": "^Sunday 14 March$", "end_before": "^Presenter Index$", "drop": ["^Programme 2027\\s+Index$", "^\\d{1,3}$"],
  "headings": {"day": "^(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday) \\d{1,2} March$", "block": "^(?P<block>.+?): (?P<start>\\d{1,2}:\\d\\d)[–-](?P<end>\\d{1,2}:\\d\\d)$", "session": "^(?P<session>.+?) \\((?:Room )?(?P<room>A1|B2|C3|Main Hall)\\)$"},
  "entry": {"marker": "^Presenter: (?P<presenter>.+)$"}, "expect_sessions": 11},
 "fields": {"id": {"sequence": true}, "title": "title", "abstract": "abstract", "session": "session", "hall": "room", "start": "start", "end": "end"},
 "authors": {"column": "presenter"}, "time": {"zone": "Asia/Tokyo", "format": "%Y-%m-%d %H:%M"}, "meta": {"name": "Example Meeting 2027", "slug": "example2027", "year": 2027}}
```

Another marker, other heading words, no sessions:

```json
{"text": {"year": 2027, "start_after": "^DAY 1 – Thursday, April 8$", "end_before": "^Author Index$", "drop": ["^Book of Abstracts 2027$", "^– \\d{1,3} –$"],
  "headings": {"day": "^DAY \\d – (?:Thursday|Friday|Saturday), April \\d{1,2}$", "block": "^(?P<block>.+?) \\((?P<start>\\d{1,2}:\\d\\d) - (?P<end>\\d{1,2}:\\d\\d)\\)$"}, "entry": {"marker": "^Authors: (?P<authors>.+)$"}},
 "fields": {"id": {"sequence": true}, "title": "title", "abstract": "abstract", "start": "start", "end": "end"},
 "authors": {"column": "authors"}, "time": {"zone": "Asia/Kolkata", "format": "%Y-%m-%d %H:%M"}, "meta": {"name": "Example Workshop 2027", "slug": "example-b", "year": 2027}}
```

Optional: `"expect_sessions": N` warns if the body has another number; `"page_offset": -10` with `"page": "page"` under `fields` gives each entry a book page (PDF page + offset).

## 2. Import, then the report
`python3 ${CLAUDE_SKILL_DIR}/scripts/import_dataset.py import <book> --mapping mapping.json` (`--out` as in `OTHER_CONFERENCES.md`). Show the user the report, with its `text:` line and three samples, before any picks, then stop and wait for the user's reply, even if they answered an earlier question; search only after they say it looks right. Check the `text:` line first: the sessions found and the entries with a session must fit what you saw (posters and plenary talks have none). A warning about one very long abstract means the index at the back is inside the body. If it says a weekday does not match its date, show the message, ask which is right and put the real date in `day_overrides`; never guess. If it refuses, fix the patterns from the message.

## 3. Picks, and what to tell the user
There are no links, and never invent any (no placeholder URLs): cite the `book page` that `show` prints, or, without page numbers, the day, time and title. Session times are those of the block, not of each talk. Tell the user: only the presenter (or the listed authors) is known, with affiliations only if the book prints them, so `who --affil` and the own-group check are weak; the default pool is a fifth of the entries (40 to 150); a few entries can be wrong (a title split over a page, a second presenter line), so check the samples.
