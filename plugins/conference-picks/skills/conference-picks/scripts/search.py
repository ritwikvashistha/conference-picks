#!/usr/bin/env python3
"""Find NeurIPS 2026 papers related to yours. Python 3 standard library only.

  search.py find --paper 148353 --paper https://neurips.cc/virtual/2026/poster/153320   # your NeurIPS papers
  search.py find --text-file abstract.txt                                                # or pasted abstract(s)
  search.py show 101,102,103 [--chars 600]                                               # full abstracts of chosen ids
  search.py who --name "Arya Farahi" | --affil "UT Austin|University of Texas"          # find people / an institution's papers
  search.py ics 101,102,103 > picks.ics                                                  # calendar file for chosen ids
  search.py csv 101,102,103 [--reasons reasons.tsv] > picks.csv                          # spreadsheet of chosen ids
  search.py profile --name "First Last" [--affil "UT Austin"]                            # profile mode: find the author on OpenAlex
  search.py profile --id A123... | --orcid 0000-... | --bibtex scholar.bib --save profile.json   # list works, save them
  search.py find --profile profile.json --use 1,4,7 --text-file brief.txt                # search from chosen works
  search.py list                                                                         # datasets: the bundled NeurIPS 2026 data and your own
  search.py find --data icml2026 --paper 64869                                           # find, show, who, ics and csv take --data (slug or folder)
"""
import argparse, difflib, gzip, json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "papers.json.gz")
INST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "institutions.json")
HOME = os.environ.get("CONFERENCE_PICKS_HOME") or os.path.expanduser("~/.conference-picks")  # your own datasets, one folder each
NEURIPS = {"name": "NeurIPS 2026", "slug": "neurips2026", "item": "poster", "paper_types": ["Poster"], "snapshot_date": "2026-11-05",
           "zones": {"Sydney": "Australia/Sydney", "Atlanta": "America/New_York", "Paris": "Europe/Paris"}, "notice": "bundled snapshot, see DATA_NOTICE.md"}
CTX = {"data": DATA, "inst": INST, "meta": NEURIPS, "ids": set()}  # the dataset in use: the bundled NeurIPS data unless --data says otherwise
STOP = set("""a about above after again all also am an and any are as at be because been before being below between both but by can
could did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its
just me more most my no nor not now of off on once only or other our out over own same she should so some such than that the their
them then there these they this those through to too under until up us very was we were what when where which while who whom why
will with would you your""".split())


def terms(text):
    w = [t for t in re.findall(r"[a-z0-9]{2,}", text.lower()) if t not in STOP]
    return w + [a + " " + b for a, b in zip(w, w[1:])]


def use_data(arg):
    """--data PATH | SLUG: a dataset folder (papers.json.gz, meta.json, optional institutions.json), or one under HOME."""
    if not arg:
        return
    d = os.path.expanduser(arg) if re.search(r"[/\\]|^[.~]", arg) else os.path.join(HOME, arg)
    if not all(os.path.isfile(os.path.join(d, f)) for f in ("papers.json.gz", "meta.json")):
        sys.exit(f"no dataset at {d}: run `search.py list` to see what is installed (your datasets live in {HOME})")
    with open(os.path.join(d, "meta.json"), encoding="utf-8") as f:
        CTX.update(data=os.path.join(d, "papers.json.gz"), inst=os.path.join(d, "institutions.json"), meta=json.load(f))


def load():
    with gzip.open(CTX["data"], "rt", encoding="utf-8") as f:
        papers = json.load(f)
    for p in papers:  # ids are strings everywhere: OpenReview and ACL ids are not numbers (the bundled data has ints)
        p["id"] = str(p["id"]) if p.get("id") not in (None, "") else None
    CTX["ids"] = {p["id"] for p in papers if p["id"]}
    return papers


def wanted(p):
    """Records that count as papers: the types in meta paper_types, any type when meta has none."""
    types = CTX["meta"].get("paper_types")
    return not types or p.get("type") in types


def link(p):
    t = CTX["meta"].get("link_template")
    return p.get("url") or (t.format(id=p["id"]) if t and p.get("id") else "")


def inst_data():
    try:
        with open(CTX["inst"], encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:  # a dataset without an institutions table: `who --affil` falls back to a regex on the raw text
        return {"patterns": [], "raw": {}}


def build(papers):
    """TF-IDF (sublinear tf, smooth idf, unigrams + bigrams, min_df 2, L2) with an inverted index.
    ponytail: rebuilt every run (a few seconds); cache to disk if that gets annoying."""
    ids = [i for i, p in enumerate(papers) if wanted(p) and p.get("abstract") and p["id"]]  # 6 reproducibility-track posters have no poster page/id, so cannot be linked
    tf = {i: Counter(terms(papers[i]["title"] + ". " + papers[i]["abstract"])) for i in ids}
    df = Counter(t for c in tf.values() for t in c)
    idf = {t: math.log((1 + len(ids)) / (1 + n)) + 1 for t, n in df.items() if n >= 2}

    def vec(c):
        v = {t: (1 + math.log(n)) * idf[t] for t, n in c.items() if t in idf}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        return {t: x / norm for t, x in v.items()}

    vecs = {i: vec(c) for i, c in tf.items()}
    post = defaultdict(list)
    for i, v in vecs.items():
        for t, x in v.items():
            post[t].append((i, x))
    return vec, vecs, post


def paper_id(s):
    """An id as typed: the exact id (any shape), the id at the end of a URL or in its ?id=, else the last 4-7 digit run."""
    s = s.strip()
    for c in [s, s.rstrip("/").rsplit("/", 1)[-1].split("?")[0], *re.findall(r"[?&]id=([^&#]+)", s)]:
        if c in CTX["ids"]:
            return c
    m = re.findall(r"\d{4,7}", s)
    return str(int(m[-1])) if m else None


def place(p):
    tag = " [oral]" if p.get("oral_event") else ""
    if not p.get("local_start"):
        return "-" + tag
    when = f"{datetime.strptime(p['local_start'], '%Y-%m-%d %H:%M'):%a %Y-%m-%d %H:%M}"
    return (p["city"] + " " if p.get("city") else "") + when + tag  # local time at that site


def cut(text, n):
    """First ~n chars, ending at a sentence if one ends in the last quarter, else at a word."""
    if not n or len(text) <= n:
        return text
    k = text.rfind(". ", 0, n)
    return text[: k + 1] if k > n * 3 // 4 else text[:n].rsplit(" ", 1)[0] + " ..."


def name_key(n):
    return " ".join(re.findall(r"[a-z]+", fold(n)))


def find(a):
    papers = load()
    by_id = {p["id"]: i for i, p in enumerate(papers) if p["id"]}
    vec, vecs, post = build(papers)
    k = a.k or min(150, max(40, sum(map(wanted, papers)) // 5))  # a fifth of the papers, 40 to 150 (NeurIPS: 150)
    queries, own = [], set()
    for s in a.paper or []:
        i = by_id.get(paper_id(s))
        if i is None or i not in vecs:
            sys.exit(f"not a {CTX['meta']['name']} {CTX['meta'].get('item', 'paper')} with an abstract: {s}")
        queries.append(vecs[i]); own.add(i)
    texts = [a.text] if a.text else []
    texts += [open(f, encoding="utf-8").read() for f in a.text_file or []]
    if a.profile:  # works saved by `profile --save`; --use picks them by number
        works = json.load(open(a.profile, encoding="utf-8"))
        for n in a.use.split(","):
            w = works[int(n) - 1]
            texts.append(w["title"] + ". " + w["abstract"])
    queries += [vec(Counter(terms(t))) for t in texts]
    if not queries:
        sys.exit("give --paper, --text or --text-file")
    score = defaultdict(float)
    for q in queries:
        for t, qw in q.items():
            for i, dw in post[t]:
                score[i] += qw * dw / len(queries)
    ban = {name_key(n) for n in a.exclude_name or []}  # drop papers by the user (profile mode has no paper ids to exclude)
    top = sorted((i for i in score if i not in own and not any(name_key(n) in ban for n, _ in papers[i]["authors"])), key=lambda i: -score[i])[:k]
    print("rank\tid\tscore\twhere\ttitle\tmatched terms")
    for r, i in enumerate(top, 1):
        shared = sorted(set().union(*(q.keys() for q in queries)) & vecs[i].keys(),
                        key=lambda t: -sum(q.get(t, 0) for q in queries) * vecs[i][t])
        pick = []
        for t in shared:  # skip a unigram already inside a chosen bigram
            if not any(t in b.split() for b in pick):
                pick.append(t)
            if len(pick) == 4:
                break
        p = papers[i]
        print(f"{r}\t{p['id']}\t{score[i]:.3f}\t{place(p)}\t{p['title']}\t{', '.join(pick)}")


def show(a):
    papers = load()
    by_id = {p["id"]: p for p in papers if p["id"]}
    for s in a.ids.split(","):
        p = by_id.get(paper_id(s))
        if not p:
            print(f"### {s}: not found\n"); continue
        who = "; ".join(f"{n} ({af})" if af else n for n, af in p["authors"][:8]) + (" ..." if len(p["authors"]) > 8 else "")
        ab = "" if a.no_abstract else cut(p["abstract"], a.chars) + "\n"
        pointer = " | ".join(x for x in (link(p), f"book page {p['page']}" if p.get("page") else "") if x)  # a book of abstracts has pages, not links
        print(f"### {p['id']} | {p['title']}\nauthors: {who}\nwhere: {place(p)} | {pointer}\n{ab}")


def fold(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(ch))


def institutions(query):
    """Canonical institution names a query refers to ('UT Austin', 'MIT', 'Tsinghua'), plus the raw-affiliation -> names table."""
    data = inst_data()
    h = fold(query)
    hit = [c for c, inc, *exc in data["patterns"] if re.search(inc, h) and not (exc and re.search(exc[0], h))]
    if not hit:  # not a known alias: every query word as a whole word in a canonical name
        names = {c for v in data["raw"].values() for c in v}
        hit = sorted(c for c in names if all(re.search(r"\b" + re.escape(w) + r"\b", fold(c)) for w in h.split()))
    return hit, data["raw"]


def who(a):
    if not (a.name or a.affil):
        sys.exit("give --name and/or --affil")
    words = (a.name or "").lower().split()
    want, table = institutions(a.affil) if a.affil else ([], {})
    af = None if want or not a.affil else re.compile(a.affil, re.I)  # unknown institution: treat the text as a regex
    rows = []
    for p in load():
        hit = [f"{n} ({x})" for n, x in p["authors"] if all(w in n.lower() for w in words)
               and (not a.affil or (set(table.get(x, [])) & set(want) if want else af.search(x)))]
        if wanted(p) and hit:
            rows.append((p.get("city") or "~", p.get("local_start") or "~", p, hit))
    if a.affil:
        by = Counter(r[0] for r in rows)
        print(f"# {len(rows)} papers, {sum(len(r[3]) for r in rows)} author slots at {', '.join(want) or a.affil}; " + ", ".join(f"{c} {n}" for c, n in sorted(by.items())))
    print("id\twhere\ttitle\tmatching authors")
    for _, _, p, hit in sorted(rows, key=lambda r: r[:2]):
        print(f"{p['id']}\t{place(p)}\t{p['title']}\t{'; '.join(hit)}")


def oa(path, **params):
    url = "https://api.openalex.org/" + path + ("?" + urllib.parse.urlencode(params) if params else "")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "neurips-picks agent skill"}), timeout=30) as r:
            return json.load(r)
    except Exception as e:
        sys.exit(f"OpenAlex request failed ({e}). Offer another input: a BibTeX export, pasted titles, or NeurIPS paper ids.")


def inverted(ii):
    pos = {p: w for w, ps in (ii or {}).items() for p in ps}
    return " ".join(pos[i] for i in sorted(pos))


def bib_field(entry, names):
    m = re.search(r"(?is)\b(?:" + names + r")\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"([^\"]*)\")", entry)  # {braced} or "quoted" value
    return " ".join(re.sub(r"[{}]", "", m.group(1) or m.group(2) or "").split()) if m else ""


def bib_works(text):
    out = []
    for entry in re.split(r"(?m)^@", text)[1:]:
        title = bib_field(entry, "title")
        if title:
            y = re.search(r"(?i)\byear\s*=\s*[{\"]?(\d{4})", entry)
            out.append(dict(title=title, year=int(y.group(1)) if y else "", venue=bib_field(entry, "journal|booktitle"), cited="", abstract=""))
    return out


def profile(a):
    works = []
    if a.name:  # candidates only: names are ambiguous and OpenAlex sometimes merges different people
        res = oa("authors", search=a.name, **{"per-page": 8})["results"]
        if a.affil:
            res.sort(key=lambda x: not any(fold(a.affil) in fold(i.get("display_name", "")) for i in x.get("last_known_institutions") or []))
        print("openalex_id\tname\tinstitutions\tworks\tcitations\ttopics")
        for x in res[:5]:
            print("\t".join([x["id"].rsplit("/", 1)[-1], x["display_name"], "; ".join(i["display_name"] for i in x.get("last_known_institutions") or []),
                             str(x["works_count"]), str(x["cited_by_count"]), "; ".join(t["display_name"] for t in (x.get("topics") or [])[:4])]))
        print("# check institutions and topics with the user, then re-run with --id")
        return
    if a.id or a.orcid:
        aid = a.id.rsplit("/", 1)[-1] if a.id else oa("authors/orcid:" + a.orcid.rsplit("/", 1)[-1], select="id")["id"].rsplit("/", 1)[-1]
        d = oa("works", filter=f"author.id:{aid},from_publication_date:{a.since}-01-01", sort="publication_date:desc", select="title,publication_year,primary_location,cited_by_count,abstract_inverted_index", **{"per-page": a.n})
        works = [dict(title=w["title"] or "", year=w["publication_year"], venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
                      cited=w["cited_by_count"], abstract=inverted(w.get("abstract_inverted_index"))) for w in d["results"]]
    elif a.bibtex:
        works = bib_works(open(a.bibtex, encoding="utf-8", errors="replace").read())
    elif a.titles_file:
        works = [dict(title=t.strip(), year="", venue="", cited="", abstract="") for t in open(a.titles_file, encoding="utf-8") if t.strip()]
    else:
        sys.exit("give --name, --id, --orcid, --bibtex or --titles-file")
    works = works[: a.n]
    if a.lookup:  # abstracts for BibTeX or title lists, matched by title (a retitled paper may not be found)
        for w in works:
            if not w["abstract"]:
                for r in oa("works", search=w["title"], select="title,abstract_inverted_index", **{"per-page": 3})["results"]:
                    if difflib.SequenceMatcher(None, fold(w["title"]), fold(r["title"] or "")).ratio() > 0.85:
                        w["abstract"] = inverted(r.get("abstract_inverted_index")); break
                time.sleep(0.15)
    for n, w in enumerate(works, 1):
        print(f"#{n} {w['year']} | {w['title']} | {w['venue']}" + (f" | cited {w['cited']}" if w["cited"] != "" else "") + ("" if a.no_abstract or not w["abstract"] else "\n    " + cut(w["abstract"], a.chars)))
    print(f"# {len(works)} works, {sum(bool(w['abstract']) for w in works)} with abstracts" + (f"; saved to {a.save}" if a.save else ""))
    if a.save:
        json.dump(works, open(a.save, "w", encoding="utf-8"))


def to_csv(a):
    import csv as csvlib
    papers = {p["id"]: p for p in load() if p["id"]}
    table = inst_data()["raw"]
    reasons = {}
    if a.reasons:  # lines of: id <TAB> one-line reason
        for line in open(a.reasons, encoding="utf-8"):
            i, _, text = line.partition("\t")
            if paper_id(i):
                reasons[paper_id(i)] = text.strip()
    w = csvlib.writer(sys.stdout, lineterminator="\n")
    w.writerow(["rank", "id", "title", "authors", "institutions", "site", "session", "local_start", "local_end", "hall", "oral", "link", "reason"])
    for n, s in enumerate(a.ids.split(","), 1):
        p = papers.get(paper_id(s))
        if not p:
            print(f"skipped {s}: not found", file=sys.stderr); continue
        inst = list(dict.fromkeys(c for _, x in p["authors"] for c in table.get(x, [])))
        w.writerow([n, p["id"], p["title"], "; ".join(n_ for n_, _ in p["authors"]), "; ".join(inst), p.get("city", ""), p.get("session") or "",
                    p.get("local_start", ""), p.get("local_end", ""), p.get("hall", ""), "yes" if p.get("oral_event") else "", link(p), reasons.get(p["id"], "")])


def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics(a):
    """ponytail: needs zoneinfo (Python 3.9+, tz data on Windows needs `pip install tzdata`); long lines are not folded."""
    from zoneinfo import ZoneInfo
    meta = CTX["meta"]
    zone = lambda p: (meta.get("zones") or {}).get(p.get("city")) or meta.get("zone")  # per site, else one zone for the whole conference
    papers = load()
    if not any(p.get("local_start") for p in papers):
        sys.exit("this dataset has no session times, so there is nothing to put in a calendar")
    by_id = {p["id"]: p for p in papers if p["id"]}
    utc = lambda t, p: t.replace(tzinfo=ZoneInfo(zone(p))).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//neurips-picks//EN"]
    for s in a.ids.split(","):
        p = by_id.get(paper_id(s))
        if not p or not p.get("local_start"):
            print(f"skipped {s}: no session yet", file=sys.stderr); continue
        if not zone(p):
            print(f"skipped {s}: no time zone known for it", file=sys.stderr); continue
        t0 = datetime.strptime(p["local_start"], "%Y-%m-%d %H:%M")
        t1 = datetime.strptime(p["local_end"], "%Y-%m-%d %H:%M") if p.get("local_end") else t0 + timedelta(hours=2)
        who = ", ".join(n for n, _ in p["authors"][:4]) + (" et al." if len(p["authors"]) > 4 else "")
        where = ", ".join(x for x in (p.get("hall"), p.get("city")) if x)
        out += ["BEGIN:VEVENT", f"UID:{p['id']}@{meta.get('slug', 'conference')}-picks", f"DTSTAMP:{now}", f"DTSTART:{utc(t0, p)}", f"DTEND:{utc(t1, p)}",
                f"SUMMARY:{esc(p['title'])}"] + ([f"LOCATION:{esc(where)}"] if where else []) + ([f"URL:{link(p)}"] if link(p) else []) + [f"DESCRIPTION:{esc(who)}", "END:VEVENT"]
    print("\r\n".join(out + ["END:VCALENDAR"]))


def list_data(a):
    cols = ["slug", "name", "snapshot_date", "link_template", "source", "notice"]
    rows = [NEURIPS]
    for d in sorted(os.listdir(HOME)) if os.path.isdir(HOME) else []:
        if os.path.isfile(os.path.join(HOME, d, "meta.json")):
            with open(os.path.join(HOME, d, "meta.json"), encoding="utf-8") as f:
                rows.append(dict(json.load(f), slug=d))  # the folder name is what --data takes
    print("\t".join(cols))
    for m in rows:
        print("\t".join(str(m.get(c, "")).replace("\t", " ").replace("\n", " ") for c in cols))


if __name__ == "__main__":
    DATA_HELP = "dataset: a folder, or a slug under ~/.conference-picks (default: the bundled NeurIPS 2026 data)"
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find"); f.set_defaults(fn=find); f.add_argument("--data", help=DATA_HELP)
    f.add_argument("--paper", action="append", help="your NeurIPS 2026 paper: id or neurips.cc URL (repeatable)")
    f.add_argument("--text"); f.add_argument("--text-file", action="append", help="repeatable; each file is one query")
    f.add_argument("--profile", help="works saved by the profile command"); f.add_argument("--use", help="work numbers from the profile list, e.g. 1,4,7")
    f.add_argument("--exclude-name", action="append", help="drop papers by this author (the user), repeatable")
    f.add_argument("-k", type=int, help="pool size (default: a fifth of the dataset, between 40 and 150)")
    s = sub.add_parser("show"); s.set_defaults(fn=show); s.add_argument("--data", help=DATA_HELP)
    s.add_argument("ids", help="comma-separated paper ids"); s.add_argument("--chars", type=int, help="truncate abstracts"); s.add_argument("--no-abstract", action="store_true", help="title, authors, where only")
    w = sub.add_parser("who"); w.set_defaults(fn=who); w.add_argument("--data", help=DATA_HELP)
    w.add_argument("--name", help="author name (all words must match)"); w.add_argument("--affil", help="regex on affiliation")
    c = sub.add_parser("ics"); c.set_defaults(fn=ics); c.add_argument("--data", help=DATA_HELP)
    c.add_argument("ids", help="comma-separated paper ids")
    pr = sub.add_parser("profile"); pr.set_defaults(fn=profile)
    pr.add_argument("--name"); pr.add_argument("--affil", help="rank name matches by institution")
    pr.add_argument("--id", help="OpenAlex author id"); pr.add_argument("--orcid")
    pr.add_argument("--bibtex", help="BibTeX export, for example from a Google Scholar profile"); pr.add_argument("--titles-file", help="one paper title per line")
    pr.add_argument("--lookup", action="store_true", help="fetch abstracts from OpenAlex by title"); pr.add_argument("--since", type=int, default=datetime.now().year - 5)
    pr.add_argument("-n", type=int, default=30, help="max works (default 30)"); pr.add_argument("--chars", type=int, default=450)
    pr.add_argument("--no-abstract", action="store_true"); pr.add_argument("--save", help="write the works to this JSON file")
    v = sub.add_parser("csv"); v.set_defaults(fn=to_csv); v.add_argument("--data", help=DATA_HELP)
    v.add_argument("ids", help="comma-separated paper ids, best first"); v.add_argument("--reasons", help="TSV file: id, tab, one-line reason")
    sub.add_parser("list", help="the bundled and the installed datasets").set_defaults(fn=list_data)
    a = ap.parse_args()
    use_data(getattr(a, "data", None))
    a.fn(a)
