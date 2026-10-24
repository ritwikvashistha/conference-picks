#!/usr/bin/env python3
"""Turn a conference's paper list (CSV, JSON or JSONL, optionally .gz) or the text of its book of abstracts into a dataset folder for search.py. Python 3 standard library only.

  import_dataset.py inspect FILE                                   # format, rows, columns with sample values (a .txt or .pdf book: its structure)
  import_dataset.py import FILE --mapping map.json [--out DIR]     # check, convert, write papers.json.gz, meta.json, institutions.json

The mapping (JSON) says which column holds what. The script checks it and writes nothing if the data is not good enough:
  {"records": "results",              # JSON object only: dotted path to the list of records
   "fields": {"id": "col" | {"column": "url", "regex": "/(\\\\d+)$"}, "title": "col",       # id and title are required
              "abstract": "col", "url": "col", "type": "col", "session": "col", "hall": "col", "city": "col", "start": "col", "end": "col"},
   "authors": {"column": "col"} | {"column": "col", "name": "key", "affil": "key"},       # a "Name (Affil), ..." string | a list of objects
   "keep_types": ["Poster"],          # optional: drop every other type
   "time": {"zone": "Europe/Paris"} | {"zones": {"<city>": "<zone>"}},                   # + "format": strptime format for times already local
   "meta": {"name": "ICML 2026", "slug": "icml2026", "paper_types": ["Poster"], "link_template": "https://.../{id}", "year": 2026}}
Times with an offset (ISO, the default) are converted to the zone of their site. Default output: $CONFERENCE_PICKS_HOME or ~/.conference-picks, then the slug.
{"id": {"sequence": true}} numbers the records 1, 2, ... in file order.

A book of abstracts takes a "text" block; give FILE as the .txt from `pdftotext -layout book.pdf book.txt` (poppler), or as the .pdf itself when pdftotext is on PATH.
Its entries become the records, and the mapping names their columns:
  "text": {"year": 2026, "start_after": "^Sunday 28 June$",         # the body starts at the first line that matches; "end_before" ends it (the index at the back)
           "drop": ["^Programme\\s+Index$", "^\\d{1,3}$"],          # footer and page-number lines
           "headings": {"day": "^...$", "block": "^(?P<block>.+): (?P<start>\\d+:\\d\\d)-(?P<end>\\d+:\\d\\d)$", "session": "^(?P<session>.+) \\((?P<room>.+)\\)$"},
           "entry": {"marker": "^Presenter: (?P<presenter>.+)$"},     # one line per entry: the lines above it are the title, the lines below it the abstract
           "day_overrides": {"Monday 30 June": "2026-06-29"},          # a day heading whose date or weekday the book prints wrongly
           "expect_sessions": 70}                                     # optional: warn if the body has another number of session headings
Every named group becomes a column, next to title, abstract and day (and page when "page_offset" is set: book page = the PDF page of the marker line + offset); headings carry forward.
"""
import argparse, collections, csv, datetime as dt, gzip, hashlib, html, json, os, re, shutil, subprocess, sys, unicodedata
from zoneinfo import ZoneInfo

TEXT_FILES = (".txt", ".pdf")
MONTHS, WEEKDAYS = "jan feb mar apr may jun jul aug sep oct nov dec".split(), "mon tue wed thu fri sat sun".split()
HERE = os.path.dirname(os.path.abspath(__file__))
SHIPPED = os.path.join(HERE, "..", "data", "institutions.json")  # its curated patterns also drive the table written for the new dataset
MIN_RECORDS, MAX_NO_TITLE, MIN_ABSTRACTS, WARN_ABSTRACTS, MAX_DUP, MAX_SPAN_DAYS = 50, 0.05, 0.5, 0.8, 0.005, 21
TEXT_NO_TITLE, TEXT_NO_DAY, TEXT_WORDS, TEXT_WORDS_SHARE, TEXT_REPEATS = 0.01, 0.02, 20, 0.9, 20  # text entries: the share of entries without title or day that is refused, abstracts of at least 20 words that is expected, a line repeated this often


def fail(*msgs):
    sys.exit("refusing to import:\n" + "\n".join("- " + m for m in msgs))


def load_records(path, key=None):
    base = path[:-3] if path.endswith(".gz") else path
    ext = os.path.splitext(base)[1].lower()
    with (gzip.open(path, "rt", encoding="utf-8-sig", newline="") if path.endswith(".gz") else open(path, encoding="utf-8-sig", newline="")) as f:
        if ext == ".csv":
            csv.field_size_limit(sys.maxsize)
            return "csv", list(csv.DictReader(f)), None
        if ext == ".jsonl":
            return "jsonl", [json.loads(line) for line in f if line.strip()], None
        if ext == ".json":
            data = json.load(f)
            if isinstance(data, dict):
                key = key or next((k for k, v in data.items() if isinstance(v, list) and v and isinstance(v[0], dict)), None)
                if not key:
                    sys.exit('no list of records found in the JSON: give "records" (a dotted path) in the mapping')
                for part in key.split("."):
                    data = data[part]
            return "json", data, key
    sys.exit("unknown file type %r: use .csv, .json or .jsonl (optionally .gz)" % ext)


def inspect(path):
    if os.path.splitext(path)[1].lower() in TEXT_FILES:
        return inspect_text(path, read_text(path))
    fmt, recs, key = load_records(path)
    cols = list(dict.fromkeys(k for r in recs for k in r))
    lines = ["file: %s  format: %s  rows: %d" % (os.path.basename(path), fmt, len(recs))] + (["records: " + key] if key else [])
    for c in cols[:30]:
        vals = [r.get(c) for r in recs if r.get(c) not in (None, "", [], {})]
        samples = []
        for v in vals:
            s = (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)).replace("\n", " ")
            s = s[:55] + ("..." if len(s) > 55 else "")
            if s not in samples:
                samples.append(s)
            if len(samples) == 2:
                break
        lines.append("  %s  %d%%  %s" % (c, 100 * len(vals) // max(len(recs), 1), " | ".join(samples)))
    out = "\n".join(lines + (["  ... %d more columns" % (len(cols) - 30)] if len(cols) > 30 else []))
    emit(out)


def emit(out):
    print(out if len(out) <= 3000 else out[:2950] + "\n... (cut)")


def read_text(path):
    """The text of a book: a .txt as it is; a .pdf through `pdftotext -layout` when that is on PATH, else the command for the user to run."""
    if path.lower().endswith(".pdf"):
        exe = shutil.which("pdftotext")
        if not exe:
            sys.exit('pdftotext (poppler) is not on PATH, so this PDF cannot be read here. Do not install anything: ask the user to run\n  pdftotext -layout "%s" "%s"\nand to give you the .txt file.' % (path, os.path.splitext(path)[0] + ".txt"))
        r = subprocess.run([exe, "-layout", path, "-"], capture_output=True)
        if r.returncode:
            sys.exit("pdftotext failed: " + r.stderr.decode("utf-8", "replace").strip()[:300])
        return r.stdout.decode("utf-8", errors="replace")
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def inspect_text(path, text):
    """What an agent needs to write the text patterns without reading the book: counts, the lines around the first entry, and one line per shape of day and time heading."""
    lines = [x.strip() for x in text.split("\n")]
    show = lambda n: "L%d  %s" % (n + 1, lines[n][:90])
    labels = collections.Counter(m[1] for x in lines for m in [re.match(r"([A-Z][A-Za-z ]{2,24}):\s*\S", x)] if m)
    top = [(k, c) for k, c in labels.most_common(4) if c >= 5]
    out = ["file: %s  format: text  lines: %d  pages: %d  characters: %d" % (os.path.basename(path), len(lines), text.rstrip().count("\f") + 1, len(text)),
           "marker candidates (label: lines): " + (", ".join("%s: %d" % t for t in top) or "none with 5 or more lines")]
    first = last = 0
    if top:
        at = [i for i, x in enumerate(lines) if x.startswith(top[0][0] + ":")]
        first, last = at[0], at[-1]
        out += ["around the first %s line:" % top[0][0]] + [show(i) for i in range(max(first - 10, 0), min(first + 4, len(lines)))]
    seen, heads = set(), []
    for n, x in enumerate(lines[:last or len(lines)]):  # not the index at the back
        if 3 < len(x) <= 60 and ". ." not in x and (parse_day(x, 2000) or re.search(r"\d{1,2}[:.]\d\d\s*[–—-]\s*\d{1,2}[:.]\d\d", x)):
            shape = re.sub(r"[A-Za-z]+", "a", re.sub(r"\d+", "9", x))
            if shape not in seen:
                seen.add(shape); heads.append(show(n))
    out += ["day and time lines, one per shape:"] + heads[:6]
    ends = {}
    for n, x in enumerate(lines):
        m = re.search(r"\(([^()]{1,25})\)$", x)
        if m and len(x) <= 140:
            ends.setdefault(m[0], [n, 0])[1] += 1
    ends = sorted(((k, v) for k, v in ends.items() if v[1] >= 3), key=lambda kv: -kv[1][1])[:5]
    if ends:
        out.append("lines ending in (...): " + ", ".join("%s %dx first L%d" % (k, v[1], v[0] + 1) for k, v in ends))
    rep = [(" ".join(k.split())[:50], c) for k, c in collections.Counter(" ".join(x.split()) for x in lines if x).most_common(4) if c >= 5]
    if rep:
        out.append("repeated lines (footers?): " + ", ".join("%dx %s" % (c, k) for k, c in rep))
    emit("\n".join(out))


def parse_day(s, year):
    """'Sunday 28 June', 'June 28th', 'Tue, Mar 9 2027' -> (date, weekday number or None), or None when no date can be read."""
    low, months = s.lower(), "|".join(MONTHS)
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(%s)[a-z]*\b|\b(%s)[a-z]*\.?\s+(\d{1,2})\b" % (months, months), low)
    y = re.search(r"\b(\d{4})\b", s)
    if not m:
        return None
    day, mon = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
    try:
        d = dt.date(int(y.group(1)) if y else year, MONTHS.index(mon) + 1, int(day))
    except (TypeError, ValueError):
        return None
    w = re.search(r"\b(%s)[a-z]*" % "|".join(WEEKDAYS), low)
    return d, WEEKDAYS.index(w.group(1)) if w else None


def extract(text, cfg, year):
    """The text of a book of abstracts -> (records, errors, warnings, summary line). One record per entry: title, abstract, day, the named groups of the patterns carried
    forward (a new day clears the block, a new block clears the session; start and end become 'YYYY-MM-DD HH:MM') and page when cfg has page_offset."""
    heads, entry, word, errors, warns = cfg.get("headings") or {}, cfg.get("entry") or {}, r"[^\W\d_]+(?:-[^\W\d_]+)*", [], []

    def rx(name, pattern):
        try:
            return re.compile(pattern)
        except (re.error, TypeError) as e:
            errors.append("text.%s is not a regular expression: %s" % (name, e))

    if not entry.get("marker"):
        fail("the text mapping needs entry.marker: a regular expression for the one line that starts every entry")
    kinds, marker = [(k, rx("headings." + k, heads[k])) for k in ("day", "block", "session") if k in heads], rx("entry.marker", entry["marker"])
    start, stop = [rx(k, cfg[k]) if cfg.get(k) else None for k in ("start_after", "end_before")]
    drops = [rx("drop[%d]" % j, d) for j, d in enumerate(cfg.get("drop") or [])]
    if errors:
        fail(*errors)
    lines, page = [], 1
    for raw in text.split("\n"):
        page += raw.count("\f")  # pdftotext starts every page with a form feed
        lines.append((raw.strip(), page))
    lo = next((i for i, (s, _) in enumerate(lines) if start.search(s)), None) if start else 0
    if lo is None:
        fail("text.start_after matched no line")
    hi = next((i for i in range(lo, len(lines)) if stop.search(lines[i][0])), None) if stop else len(lines)
    if hi is None:
        fail("text.end_before matched no line after the start")
    body = [(None if s and any(d.search(s) for d in drops) else s, p) for s, p in lines[lo:hi]]  # None: a dropped line (a footer), the page seam

    def kind(s):
        for k, r in kinds:
            m = r.search(s)
            if m:
                return k, m

    st, items, i = collections.Counter(), [], 0  # items: None for a blank line, False for a dropped one, else ("text", line, page), ("head", kind, match, line, page) or ("mark", line, match, page)
    while i < len(body):
        s, pg = body[i]
        if s is None:
            items.append(False); i += 1
            continue
        h = kind(s) if s else None
        if s and not h and not marker.search(s) and i + 1 < len(body):  # a heading wrapped over two lines: joined only when the joined text is a heading and neither line is one alone
            t = body[i + 1][0]
            h = kind(s + " " + t) if t and not kind(t) and not marker.search(t) else None
            if h:
                s, i, st["joins"] = s + " " + t, i + 1, st["joins"] + 1
        i += 1
        mk = marker.search(s) if s and not h else None
        items.append(("head", h[0], h[1], s, pg) if h else ("mark", s, mk, pg) if mk else ("text", s, pg) if s else None)

    seen = collections.Counter(it[1] for it in items if it and it[0] == "head")
    gone = ["text.headings.%s matched no line" % k for k, _ in kinds if not seen[k]] + ([] if any(it and it[0] == "mark" for it in items) else ["text.entry.marker matched no line"])
    if gone:
        fail(*gone)
    toks = {w for s, _ in body if s for w in re.findall(word, s.lower())}  # the words the document itself spells without a line break

    def joined(parts):
        """Lines -> text. A line that ends in a hyphen before a lowercase word is joined to it; the hyphen stays only if the document spells the hyphenated form elsewhere and the joined form nowhere."""
        out = ""
        for s in parts:
            left, right = re.search("(%s)-$" % word, out) if out.endswith("-") else None, re.match(word, s)
            if left and right and s[:1].islower():
                keep = (left[1] + "-" + right[0]).lower() in toks and (left[1] + right[0]).lower() not in toks
                st["kept" if keep else "unhyphenated"] += 1
                out = out + s if keep else out[:-1] + s
            else:
                out = (out + " " if out else "") + s
        return out

    overrides, days = cfg.get("day_overrides") or {}, {}

    def day_of(s):
        """A day heading -> 'YYYY-MM-DD' ('' if unreadable). A weekday that does not match its date is an error until day_overrides gives the real date."""
        if s not in days:
            d, got = None, parse_day(s, year)
            if s in overrides:
                try:
                    d = dt.date.fromisoformat(overrides[s])
                except ValueError:
                    errors.append("text.day_overrides[%s] is not a date (use YYYY-MM-DD)" % json.dumps(s, ensure_ascii=False))
            elif not got:
                errors.append("cannot read a date from the day heading %s%s" % (json.dumps(s, ensure_ascii=False), "" if year else ": set text.year"))
            else:
                d = got[0]
                if got[1] is not None and got[1] != d.weekday():
                    errors.append("the day heading %s is %s, which is a %s: ask the user whether the date or the weekday is wrong, then give the real date in text.day_overrides, e.g. {%s: \"YYYY-MM-DD\"}" % (
                        json.dumps(s, ensure_ascii=False), d, "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()[d.weekday()], json.dumps(s, ensure_ascii=False)))
            days[s] = d
        return days[s].isoformat() if days[s] else ""

    cur, ents = {"day": "", "block": None, "session": None}, []
    for n, it in enumerate(items):
        if it and it[0] == "head":
            _, k, m, s, _ = it
            g = {name: (v or "").strip() for name, v in m.groupdict().items()}
            cur = {"day": day_of(s), "block": None, "session": None} if k == "day" else dict(cur, block=g, session=None) if k == "block" else dict(cur, session=g)
        elif it and it[0] == "mark":
            k = n
            while k and not items[k - 1]:
                k -= 1
            top = k if False in items[k:n] else n  # a page break between the title and its marker (the marker starts the page): the title is above it
            while top and items[top - 1] and items[top - 1][0] == "text":  # the title: the lines right above, up to a blank line or a heading
                top -= 1
            title = [x for x in items[top:n] if x]
            ents.append(dict(at=n, top=top, title=[x[1] for x in title], page=it[3], groups={k: (v or "").strip() for k, v in it[2].groupdict().items()}, state=cur))
    columns = {name for _, r in kinds + [("entry", marker)] for name in r.groupindex}
    recs = []
    for e, nxt in zip(ents, ents[1:] + [None]):
        rec = dict.fromkeys(columns, "")
        for g in (e["groups"], e["state"]["block"], e["state"]["session"]):
            rec.update(g or {})
        day = e["state"]["day"]
        for k in ("start", "end"):
            hm = re.fullmatch(r"(\d{1,2}):(\d\d)", rec.get(k, ""))
            if hm and day:
                rec[k] = "%s %02d:%s" % (day, int(hm[1]), hm[2])
        below = [x[1] for x in items[e["at"] + 1:nxt["top"] if nxt else len(items)] if x and x[0] == "text"]  # up to the next entry's title
        rec.update(title=joined(e["title"]), abstract=joined(below), day=day)
        if "page_offset" in cfg:
            rec["page"] = str(e["page"] + cfg["page_offset"])
        recs.append(rec)
    n, untitled, wordy = len(recs), sum(not r["title"] for r in recs), sum(len(r["abstract"].split()) >= TEXT_WORDS for r in recs)
    if untitled / n > TEXT_NO_TITLE:
        errors.append("%d of %d entries have no title (over %d%%): the title is the lines right above entry.marker, set off from the abstract before it by a blank line" % (untitled, n, TEXT_NO_TITLE * 100))
    for k in ("day", "block"):
        miss = sum(e["state"][k] in ("", None) for e in ents)
        if k in heads and miss / n > TEXT_NO_DAY:
            errors.append("%d of %d entries have no %s (over %d%%): headings.%s must match every %s heading, and the body must start at or before the first" % (miss, n, k, TEXT_NO_DAY * 100, k, k))
    if wordy / n < TEXT_WORDS_SHARE:
        warns.append("abstracts of %d words or more on only %d%% of the entries (under %d%%)" % (TEXT_WORDS, 100 * wordy // n, TEXT_WORDS_SHARE * 100))
    if [d for d in days.values() if d] != sorted(d for d in days.values() if d):
        warns.append("the day headings are not in date order: check them (and day_overrides)")
    warns += ["day_overrides has no heading %r" % k for k in overrides if k not in days]
    if cfg.get("expect_sessions") is not None and cfg["expect_sessions"] != seen["session"]:
        warns.append("expected %s session headings, found %d" % (cfg["expect_sessions"], seen["session"]))
    warns += ["line repeated %d times: %r (a footer? add it to text.drop)" % (c, t[:60]) for t, c in collections.Counter(" ".join(s.split()) for s, _ in body if s).most_common(3) if c >= TEXT_REPEATS]
    return recs, errors, warns, "text: %d entries%s; headings: %s; wrapped headings joined %d; line-end hyphens joined %d, kept %d" % (
        n, " (%d with a session)" % sum(bool(r.get("session")) for r in recs) if "session" in heads else "",
        ", ".join("%s %d" % (k, seen[k]) for k, _ in kinds), st["joins"], st["unhyphenated"], st["kept"])


def unescape(s):
    while (t := html.unescape(s)) != s:
        s = t
    return s.replace("\r\n", "\n").replace("\r", "\n").strip()


def split_authors(s, sep):
    """'Ann Lee (UT Austin), Bo Chen (MIT)' -> [[name, affiliation], ...]: split at depth 0, the last top-level (...) is the affiliation."""
    parts, depth, cur, i = [], 0, "", 0
    while i < len(s):
        depth += (s[i] == "(") - (s[i] == ")")
        if depth == 0 and s.startswith(sep, i):
            parts.append(cur); cur, i = "", i + len(sep)
            continue
        cur += s[i]; i += 1
    parts.append(cur)
    out = []
    for p in (x for x in parts if x.strip()):
        if p.endswith(")"):
            d, j = 0, len(p) - 1
            while j >= 0:
                d += (p[j] == ")") - (p[j] == "(")
                if d == 0:
                    break
                j -= 1
            out.append([p[:j].strip(), p[j + 1:-1].strip()])
        else:
            out.append([p.strip(), ""])
    return out


def fold(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(ch))


def institutions_table(records):
    """Raw affiliation -> canonical names: the curated patterns first, the rest merged by a normalised key (as for the bundled data)."""
    with open(SHIPPED, encoding="utf-8") as f:
        patterns = json.load(f)["patterns"]
    comp = [(c, re.compile(i), re.compile(e[0]) if e else None) for c, i, *e in patterns]
    key = lambda s: " ".join(re.sub(r"\b(the|of)\b", " ", re.sub(r"[^a-z0-9 ]", " ", fold(s).replace("&", " and "))).split())
    strings = collections.Counter(a[1] for p in records for a in p["authors"])
    out, merged = {}, collections.defaultdict(collections.Counter)
    for raw, n in strings.items():
        hit = [c for c, i, e in comp if i.search(fold(raw)) and not (e and e.search(fold(raw)))]
        if hit:
            out[raw] = hit
        elif raw.strip():
            pieces = list(dict.fromkeys(x.strip() for x in raw.split(",")))
            clean = ", ".join(pieces) if len(pieces) < len(raw.split(",")) else raw.strip()
            merged[key(clean)][clean] += n
            out[raw] = ("~", key(clean))
        else:
            out[raw] = []
    return patterns, {raw: ([merged[v[1]].most_common(1)[0][0]] if isinstance(v, tuple) else v) for raw, v in out.items()}


def convert(recs, m):
    f, au, tc = m["fields"], m.get("authors"), m.get("time") or {}
    zones, fixed = tc.get("zones") or {}, tc.get("zone")
    for z in list(zones.values()) + ([fixed] if fixed else []):
        try:
            ZoneInfo(z)
        except Exception:
            fail("unknown time zone %r" % z)
    cell = lambda r, c: "" if r.get(c) is None else r[c] if isinstance(r[c], (list, dict)) else str(r[c])
    out, errs = [], collections.defaultdict(list)
    for n, r in enumerate(recs, 1):
        typ = unescape(cell(r, f["type"])) if "type" in f else ""
        if m.get("keep_types") and typ not in m["keep_types"]:
            continue
        spec = f["id"]
        raw_id = str(n) if isinstance(spec, dict) and spec.get("sequence") else cell(r, spec["column"] if isinstance(spec, dict) else spec)
        if isinstance(spec, dict) and spec.get("regex"):
            hit = re.search(spec["regex"], raw_id)
            raw_id = hit.group(1) if hit else ""
        p = {"id": raw_id.strip() or None, "title": unescape(cell(r, f["title"])),
             "abstract": unescape(cell(r, f["abstract"])) if "abstract" in f else ""}
        if au:
            v = r.get(au["column"])
            if "name" in au:  # a list of objects (or a JSON string of one)
                v = json.loads(v) if isinstance(v, str) and v.strip() else v or []
                p["authors"] = [[unescape(str(a.get(au["name"]) or "")), unescape(str(a.get(au.get("affil", "")) or ""))] if isinstance(a, dict) else [unescape(str(a)), ""] for a in v]
            else:
                p["authors"] = split_authors(unescape(cell(r, au["column"])), au.get("sep", ", "))
        else:
            p["authors"] = []
        for k in ("url", "session", "hall", "city", "page"):
            if k in f and unescape(cell(r, f[k])):
                p[k] = unescape(cell(r, f[k]))
        if typ:
            p["type"] = typ
        start = cell(r, f["start"]).strip() if "start" in f else ""
        if start:
            zone = zones.get(p.get("city")) or fixed
            if not zone:
                errs["zone"].append(p.get("city") or "-")
                continue
            try:
                for k, raw in (("local_start", start), ("local_end", cell(r, f["end"]).strip() if "end" in f else "")):
                    if raw:
                        d = dt.datetime.fromisoformat(raw.replace("Z", "+00:00")) if tc.get("format", "iso") == "iso" else dt.datetime.strptime(raw, tc["format"])
                        p[k] = (d.astimezone(ZoneInfo(zone)).replace(tzinfo=None) if d.tzinfo else d).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                errs["format"].append(start)
                continue
            if p.get("local_end") and p["local_end"] <= p["local_start"]:
                errs["order"].append(p["id"] or p["title"][:30])
        out.append(p)
    return out, errs


def check(path, recs, m, found=((), ())):
    """-> (records without repeated ids, warnings); exits with every problem found if the data is not good enough. found: errors and warnings the text extractor already has."""
    out, errs = convert(recs, m)
    errors, warns, n = list(found[0]), list(found[1]), len(out)
    if errs["zone"]:
        errors.append("times need a time zone: set time.zone or time.zones in the mapping (no zone for site %s)" % ", ".join(sorted({repr(c) for c in errs["zone"]})))
    if errs["format"]:
        errors.append("cannot read %d time value(s), e.g. %r: set time.format (a strptime pattern) if they are not ISO" % (len(errs["format"]), errs["format"][0]))
    if errs["order"]:
        errors.append("end not after start for %d record(s), e.g. %s" % (len(errs["order"]), errs["order"][0]))
    if n < MIN_RECORDS:
        errors.append("only %d records; at least %d are needed" % (n, MIN_RECORDS))
    if n and sum(not p["title"] for p in out) / n > MAX_NO_TITLE:
        errors.append("%d of %d records have no title (over %d%%)" % (sum(not p["title"] for p in out), n, MAX_NO_TITLE * 100))
    types = m.get("meta", {}).get("paper_types")
    base = [p for p in out if not types or p.get("type") in types]
    if not base:
        errors.append("no record has a type in paper_types %s" % types)
    else:
        share = sum(bool(p["abstract"]) for p in base) / len(base)
        if share < MIN_ABSTRACTS:
            errors.append("abstracts on only %d%% of the searched records (at least %d%% are needed): search would run on titles alone" % (share * 100, MIN_ABSTRACTS * 100))
        elif share < WARN_ABSTRACTS:
            warns.append("abstracts on %d%% of the searched records (under %d%%)" % (share * 100, WARN_ABSTRACTS * 100))
    first, keep, dups, same = {}, [], 0, 0
    for p in out:
        if p["id"] is None:  # records without an id are kept: they are not each other's duplicates
            keep.append(p)
        elif p["id"] not in first:
            first[p["id"]] = p; keep.append(p)
        elif p == first[p["id"]]:  # the same row listed again: harmless
            same += 1
        else:  # one id, different records: a sign of a wrong id column or regex
            dups += 1
    if n and dups / n > MAX_DUP:
        errors.append("%d duplicate ids in %d records (over %.1f%%): check the id column or regex" % (dups, n, MAX_DUP * 100))
    elif dups:
        warns.append("%d duplicate id dropped (the first record is kept)" % dups)
    if same:
        warns.append("%d identical duplicate rows dropped" % same)
    if errors:
        fail(*errors)
    if sum(p["id"] is None for p in keep):
        warns.append("%d records have no id (they cannot be shown or linked)" % sum(p["id"] is None for p in keep))
    if sum(not p["authors"] for p in keep) / len(keep) > 0.1:
        warns.append("authors are empty on %d records" % sum(not p["authors"] for p in keep))
    if sum(bool(re.search(r"&(?:[a-z]+|#\d+);", p["title"] + p["abstract"])) for p in keep) / len(keep) > 0.01:
        warns.append("HTML entities are left in the titles or abstracts")
    days = sorted(p["local_start"][:10] for p in keep if p.get("local_start"))
    if days and (dt.date.fromisoformat(days[-1]) - dt.date.fromisoformat(days[0])).days > MAX_SPAN_DAYS:
        warns.append("the schedule spans %s to %s (over %d days): check the time zone and the format" % (days[0], days[-1], MAX_SPAN_DAYS))
    return keep, warns


def do_import(path, mapfile, out_dir):
    with open(mapfile, encoding="utf-8") as f:
        m = json.load(f)
    meta_in = m.get("meta") or {}
    if "id" not in m.get("fields", {}) or "title" not in m["fields"]:
        sys.exit("the mapping needs fields.id and fields.title")
    if not meta_in.get("name") or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", meta_in.get("slug", "")):
        sys.exit("the mapping needs meta.name and meta.slug (lowercase letters, digits, - _ . only: it is the folder name)")
    if bool(m.get("text")) != (os.path.splitext(path)[1].lower() in TEXT_FILES):
        fail('the mapping has a "text" block but %s is not a .txt or .pdf file' % os.path.basename(path) if m.get("text") else
             '%s is a book (.txt or .pdf), so the mapping needs a "text" block (see TEXT_PROGRAMS.md)' % os.path.basename(path))
    found = ((), ())
    if m.get("text"):  # a book of abstracts: its entries are the records
        recs, errs, warns, summary = extract(read_text(path), m["text"], m["text"].get("year") or meta_in.get("year"))
        found = (errs, warns)
    else:
        fmt, recs, _ = load_records(path, m.get("records"))
        summary = None
    cols = {k for r in recs for k in r}
    used = [v if isinstance(v, str) else v["column"] for v in m["fields"].values() if isinstance(v, str) or "column" in v] + ([m["authors"]["column"]] if m.get("authors") else [])
    if [c for c in used if c not in cols]:
        sys.exit("unknown column in the mapping: %s; the file has: %s" % (", ".join(repr(c) for c in used if c not in cols), ", ".join(sorted(cols))))
    keep, warns = check(path, recs, m, found)
    out_dir = out_dir or os.path.join(os.environ.get("CONFERENCE_PICKS_HOME") or os.path.expanduser("~/.conference-picks"), meta_in["slug"])
    today = dt.date.today().isoformat()
    meta = dict(meta_in, source=meta_in.get("source") or os.path.basename(path), snapshot_date=meta_in.get("snapshot_date") or today,
                records=len(keep), imported_with="import_dataset.py")
    meta.setdefault("notice", "Imported by you from %s on %s; %scheck the official program." % (
        meta["source"], meta["snapshot_date"], "the entries were cut out of the book's text by patterns, so a few may be wrong: " if m.get("text") else ""))
    with open(path, "rb") as f:
        meta["source_sha256"] = hashlib.sha256(f.read()).hexdigest()
    tc = m.get("time") or {}
    meta.update({k: tc[k] for k in ("zone", "zones") if tc.get(k)})
    patterns, table = institutions_table(keep)
    os.makedirs(out_dir, exist_ok=True)
    with gzip.open(os.path.join(out_dir, "papers.json.gz"), "wt", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "institutions.json"), "w", encoding="utf-8") as f:
        json.dump({"patterns": patterns, "raw": table}, f, ensure_ascii=False, separators=(",", ":"))
    report(keep, meta, warns, out_dir, summary)


def report(keep, meta, warns, out_dir, summary=None):
    n, types = len(keep), meta.get("paper_types")
    base = [p for p in keep if not types or p.get("type") in types]
    slots = [a for p in keep for a in p["authors"]]
    timed = sorted(p["local_start"][:10] for p in keep if p.get("local_start"))
    print("imported %s -> %s" % (meta["name"], out_dir))
    print("records: %d  types: %s" % (n, ", ".join("%s %d" % t for t in collections.Counter(p.get("type", "-") for p in keep).most_common())))
    print("abstracts: %d%% of %d searched records  authors with an affiliation: %d%% of %d slots" % (
        100 * sum(bool(p["abstract"]) for p in base) // max(len(base), 1), len(base), 100 * sum(bool(a[1]) for a in slots) // max(len(slots), 1), len(slots)))
    print("schedule: " + ("none (no start times: picks are ranked without session times, no calendar)" if not timed else
                          "%d records with times, %s to %s" % (len(timed), timed[0], timed[-1])))
    if summary:
        print(summary)
    for w in warns:
        print("warning: " + w)
    for k, i in enumerate(sorted({0, n // 2, n - 1}), 1):
        p = dict(keep[i], abstract=keep[i]["abstract"][:300], authors=keep[i]["authors"][:6])  # one line per field keeps it short
        print("sample %d/3:" % k)
        for field, value in p.items():
            print("  %s: %s" % (field, json.dumps(value, ensure_ascii=False)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("inspect"); i.add_argument("file")
    c = sub.add_parser("import"); c.add_argument("file"); c.add_argument("--mapping", required=True); c.add_argument("--out", help="dataset folder (default: under ~/.conference-picks)")
    a = ap.parse_args()
    inspect(a.file) if a.cmd == "inspect" else do_import(a.file, a.mapping, a.out)
