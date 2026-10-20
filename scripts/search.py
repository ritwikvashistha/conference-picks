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
"""
import argparse, difflib, gzip, json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "papers.json.gz")
INST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "institutions.json")
STOP = set("""a about above after again all also am an and any are as at be because been before being below between both but by can
could did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its
just me more most my no nor not now of off on once only or other our out over own same she should so some such than that the their
them then there these they this those through to too under until up us very was we were what when where which while who whom why
will with would you your""".split())


def terms(text):
    w = [t for t in re.findall(r"[a-z0-9]{2,}", text.lower()) if t not in STOP]
    return w + [a + " " + b for a, b in zip(w, w[1:])]


def load():
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        return json.load(f)


def build(papers):
    """TF-IDF (sublinear tf, smooth idf, unigrams + bigrams, min_df 2, L2) with an inverted index.
    ponytail: rebuilt every run (a few seconds); cache to disk if that gets annoying."""
    ids = [i for i, p in enumerate(papers) if p["type"] == "Poster" and p["abstract"] and p["id"]]  # 6 reproducibility-track posters have no poster page/id, so cannot be linked
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
    m = re.findall(r"\d{4,7}", s)
    return int(m[-1]) if m else None


def place(p):
    tag = " [oral]" if p.get("oral_event") else ""
    if not p.get("local_start"):
        return "-" + tag
    return f"{p['city']} {datetime.strptime(p['local_start'], '%Y-%m-%d %H:%M'):%a %Y-%m-%d %H:%M}{tag}"  # local time at that site


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
    queries, own = [], set()
    for s in a.paper or []:
        i = by_id.get(paper_id(s))
        if i is None or i not in vecs:
            sys.exit(f"not a NeurIPS 2026 poster with an abstract: {s}")
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
    top = sorted((i for i in score if i not in own and not any(name_key(n) in ban for n, _ in papers[i]["authors"])), key=lambda i: -score[i])[: a.k]
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
        print(f"### {p['id']} | {p['title']}\nauthors: {who}\nwhere: {place(p)} | {p['url']}\n{ab}")


def fold(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(ch))


def institutions(query):
    """Canonical institution names a query refers to ('UT Austin', 'MIT', 'Tsinghua'), plus the raw-affiliation -> names table."""
    data = json.load(open(INST))
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
        if p["type"] == "Poster" and hit:
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
    table = json.load(open(INST))["raw"]
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
                    p.get("local_start", ""), p.get("local_end", ""), p.get("hall", ""), "yes" if p.get("oral_event") else "", p["url"], reasons.get(p["id"], "")])


def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics(a):
    """ponytail: needs zoneinfo (Python 3.9+, tz data on Windows needs `pip install tzdata`); long lines are not folded."""
    from zoneinfo import ZoneInfo
    zones = {"Sydney": "Australia/Sydney", "Atlanta": "America/New_York", "Paris": "Europe/Paris"}
    by_id = {p["id"]: p for p in load() if p["id"]}
    utc = lambda t, city: t.replace(tzinfo=ZoneInfo(zones[city])).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//neurips-picks//EN"]
    for s in a.ids.split(","):
        p = by_id.get(paper_id(s))
        if not p or not p.get("local_start"):
            print(f"skipped {s}: no session yet", file=sys.stderr); continue
        t0 = datetime.strptime(p["local_start"], "%Y-%m-%d %H:%M")
        t1 = datetime.strptime(p["local_end"], "%Y-%m-%d %H:%M") if p.get("local_end") else t0 + timedelta(hours=2)
        who = ", ".join(n for n, _ in p["authors"][:4]) + (" et al." if len(p["authors"]) > 4 else "")
        out += ["BEGIN:VEVENT", f"UID:{p['id']}@neurips2026-picks", f"DTSTAMP:{now}", f"DTSTART:{utc(t0, p['city'])}", f"DTEND:{utc(t1, p['city'])}",
                f"SUMMARY:{esc(p['title'])}", f"LOCATION:{esc(p['hall'] + ', ' + p['city'])}", f"URL:{p['url']}", f"DESCRIPTION:{esc(who)}", "END:VEVENT"]
    print("\r\n".join(out + ["END:VCALENDAR"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find"); f.set_defaults(fn=find)
    f.add_argument("--paper", action="append", help="your NeurIPS 2026 paper: id or neurips.cc URL (repeatable)")
    f.add_argument("--text"); f.add_argument("--text-file", action="append", help="repeatable; each file is one query")
    f.add_argument("--profile", help="works saved by the profile command"); f.add_argument("--use", help="work numbers from the profile list, e.g. 1,4,7")
    f.add_argument("--exclude-name", action="append", help="drop papers by this author (the user), repeatable")
    f.add_argument("-k", type=int, default=150, help="pool size (default 150)")
    s = sub.add_parser("show"); s.set_defaults(fn=show)
    s.add_argument("ids", help="comma-separated paper ids"); s.add_argument("--chars", type=int, help="truncate abstracts"); s.add_argument("--no-abstract", action="store_true", help="title, authors, where only")
    w = sub.add_parser("who"); w.set_defaults(fn=who)
    w.add_argument("--name", help="author name (all words must match)"); w.add_argument("--affil", help="regex on affiliation")
    c = sub.add_parser("ics"); c.set_defaults(fn=ics)
    c.add_argument("ids", help="comma-separated paper ids")
    pr = sub.add_parser("profile"); pr.set_defaults(fn=profile)
    pr.add_argument("--name"); pr.add_argument("--affil", help="rank name matches by institution")
    pr.add_argument("--id", help="OpenAlex author id"); pr.add_argument("--orcid")
    pr.add_argument("--bibtex", help="BibTeX export, for example from a Google Scholar profile"); pr.add_argument("--titles-file", help="one paper title per line")
    pr.add_argument("--lookup", action="store_true", help="fetch abstracts from OpenAlex by title"); pr.add_argument("--since", type=int, default=datetime.now().year - 5)
    pr.add_argument("-n", type=int, default=30, help="max works (default 30)"); pr.add_argument("--chars", type=int, default=450)
    pr.add_argument("--no-abstract", action="store_true"); pr.add_argument("--save", help="write the works to this JSON file")
    v = sub.add_parser("csv"); v.set_defaults(fn=to_csv)
    v.add_argument("ids", help="comma-separated paper ids, best first"); v.add_argument("--reasons", help="TSV file: id, tab, one-line reason")
    a = ap.parse_args()
    a.fn(a)
