#!/usr/bin/env python3
"""Turn a conference's paper list (CSV, JSON or JSONL, optionally .gz) into a dataset folder for search.py. Python 3 standard library only.

  import_dataset.py inspect FILE                                   # format, rows, columns with sample values
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
"""
import argparse, collections, csv, datetime as dt, gzip, hashlib, html, json, os, re, sys, unicodedata
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
SHIPPED = os.path.join(HERE, "..", "data", "institutions.json")  # its curated patterns also drive the table written for the new dataset
MIN_RECORDS, MAX_NO_TITLE, MIN_ABSTRACTS, WARN_ABSTRACTS, MAX_DUP, MAX_SPAN_DAYS = 50, 0.05, 0.5, 0.8, 0.005, 21


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
    print(out if len(out) <= 3000 else out[:2950] + "\n... (cut)")


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
    for r in recs:
        typ = unescape(cell(r, f["type"])) if "type" in f else ""
        if m.get("keep_types") and typ not in m["keep_types"]:
            continue
        spec = f["id"]
        raw_id = cell(r, spec["column"] if isinstance(spec, dict) else spec)
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
        for k in ("url", "session", "hall", "city"):
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


def check(path, recs, m):
    """-> (records without repeated ids, warnings); exits with every problem found if the data is not good enough."""
    out, errs = convert(recs, m)
    errors, warns, n = [], [], len(out)
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
    fmt, recs, _ = load_records(path, m.get("records"))
    cols = {k for r in recs for k in r}
    used = [v["column"] if isinstance(v, dict) else v for v in m["fields"].values()] + ([m["authors"]["column"]] if m.get("authors") else [])
    if [c for c in used if c not in cols]:
        sys.exit("unknown column in the mapping: %s; the file has: %s" % (", ".join(repr(c) for c in used if c not in cols), ", ".join(sorted(cols))))
    keep, warns = check(path, recs, m)
    out_dir = out_dir or os.path.join(os.environ.get("CONFERENCE_PICKS_HOME") or os.path.expanduser("~/.conference-picks"), meta_in["slug"])
    today = dt.date.today().isoformat()
    meta = dict(meta_in, source=meta_in.get("source") or os.path.basename(path), snapshot_date=meta_in.get("snapshot_date") or today,
                records=len(keep), imported_with="import_dataset.py")
    meta.setdefault("notice", "Imported by you from %s on %s; check the official program." % (meta["source"], meta["snapshot_date"]))
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
    report(keep, meta, warns, out_dir)


def report(keep, meta, warns, out_dir):
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
