#!/usr/bin/env python3
"""Tests for the text-entries input of scripts/import_dataset.py: programs that exist only as the text of a book of abstracts.

Two synthetic programs are built from code, in our own words, so nothing from a real book is in the repo:
  A  Presenter lines, sessions with rooms (one wrapped, one on its own line), posters without a room, footers and page numbers
  B  "Authors: Name (Affil), ..." lines, other heading words, no sessions or rooms at all, a header on every page

Run: python3 tools/test_text_entries.py   (about a minute: each test runs the importer, some also run search.py)
"""
import collections, csv, datetime, gzip, json, os, subprocess, sys, tempfile, textwrap, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_importer as ti

TOPICS = ["graph sampling", "quantile forecasting", "sparse regression", "survival curves", "network inference", "image calibration", "spatial prediction", "model selection"]
METHODS = ["kernel smoothing", "variational updates", "random projections", "adaptive splines", "tempered sampling", "block bootstrap"]
SETTINGS = ["noise", "missing data", "heavy-tailed noise", "limited budgets", "distribution shift"]
NAMES = ["Ann Lee", "Bo Chen", "Cy Dunn", "Di Evans", "Fay Gold", "Gus Hill", "Ivy Jones", "Kai Lund", "Mia Novak", "Ned Okafor", "Ola Park", "Pia Quinn"]
AUTHORS_B = ["Ann Lee (UT Austin), Bo Chen (MIT)", "Cy Dunn (Example Institute), Di Evans (University of Texas at Austin), Fay Gold (MIT)",
             "Gus Hill (Other University)", "Ivy Jones (UT Austin), Kai Lund (Example Institute)"]
# entry -> (word, characters before the line break): the word is split over two lines (it gets a hyphen unless it has one there already)
SPLITS = {9: ("spike-and-slab", 10), 13: ("estimation", 6), 17: ("multilevel", 5)}
EXTRA = {4: " We place a spike-and-slab prior on the weights.", 9: " We place a spike-and-slab prior on the weights.", 17: " A multilevel model handles the sites."}
SCHEDULE_A = [  # (day, [(block, start, end, [sessions (name, room, how the room is printed) or None], entries per session)])
    (0, [("Plenary Talk 1", "9:00", "10:00", [None], 1), ("Plenary Talk 2", "10:15", "11:15", [None], 1),
         ("Parallel Sessions 1", "11:30", "13:00", [("Sampling methods", "A1", "line"), ("Spatial models", "B2", "wrap"), ("Causal questions", "C3", "line"), ("Open forum", "Main Hall", "bare")], 3),
         ("Poster Session I", "15:00", "17:00", [None], 14)]),
    (1, [("Parallel Sessions 2", "9:00", "10:30", [("Sampling methods II", "A1", "line"), ("Spatial models II", "B2", "wrap"), ("Causal questions II", "C3", "bare"), ("Closing forum", "Main Hall", "line")], 3),
         ("Poster Session 2", "15:00", "17:00", [None], 14)]),
    (2, [("Parallel Sessions 3", "9:00", "10:30", [("Survival analysis", "A1", "wrap"), ("Networks", "B2", "line"), ("Computation", "C3", "line")], 2)])]
SCHEDULE_B = [(0, [("Oral block O1", "9:30", "11:00", [None], 10), ("Oral block O2", "11:30", "13:00", [None], 10), ("Poster block P1", "14:00", "15:30", [None], 10)]),
              (1, [("Oral block O3", "9:30", "11:00", [None], 10), ("Poster block P2", "14:00", "15:30", [None], 10)]),
              (2, [("Poster block P3", "10:00", "11:30", [None], 10)])]


def session_lines(name, room, how):
    return {"line": ["%s (Room %s)" % (name, room)], "wrap": ["%s (Room" % name, room + ")"], "bare": [name, "(Room %s)" % room]}[how]


LAYOUTS = {
    "a": dict(day0=datetime.date(2027, 3, 14), schedule=SCHEDULE_A, per=26,
              day=lambda k, d, wrong: "%s %d %s" % ("Monday" if wrong else d.strftime("%A"), d.day, d.strftime("%B")),
              block=lambda n, s, e: "%s: %s–%s" % (n, s, e), marker=lambda i: "Presenter: " + NAMES[i % len(NAMES)],
              front=["Programme and Abstracts 2027", "", "Contents", "Sunday 14 March . . . . . . . . . . . . 5", "Parallel Sessions 1: 11:30–13:00 . . . . . . 6",
                     "Poster Session I: 15:00–17:00 . . . . . . . 9", "", "Welcome", "We are glad to host this meeting."],
              head=lambda page: [], foot=lambda page: ["", "Programme 2027" + " " * 40 + "Index", " " * 30 + str(page)], back=["Presenter Index", ""] + ["%s %d" % (n, 5 + k) for k, n in enumerate(NAMES)]),
    "b": dict(day0=datetime.date(2027, 4, 8), schedule=SCHEDULE_B, per=28,
              day=lambda k, d, wrong: "DAY %d – %s, %s %d" % (k + 1, d.strftime("%A"), d.strftime("%B"), d.day),
              block=lambda n, s, e: "%s (%s - %s)" % (n, s, e), marker=lambda i: "Authors: " + AUTHORS_B[i % 4],
              front=["Conference Book 2027", "", "Contents", "DAY 1 – Thursday, April 8 . . . . . . . . . 4", "Oral block O1 (9:30 - 11:00) . . . . . . . 4", ""],
              head=lambda page: ["Book of Abstracts 2027"], foot=lambda page: ["", "– %d –" % page], back=["Author Index", ""] + ["%s %d" % (n, 5 + k) for k, n in enumerate(NAMES)])}


def authors(layout, i):
    if layout == "a":
        return [[NAMES[i % len(NAMES)], ""]]
    return [[n, a.rstrip(")")] for n, a in (x.split(" (") for x in AUTHORS_B[i % 4].split("), "))]


def title_of(i):
    return "Case %d: %s for %s under %s" % (i, METHODS[i % 6], TOPICS[i % 8], SETTINGS[i % 5])


def abstract_of(i):
    t, m, s = TOPICS[i % 8], METHODS[i % 6], SETTINGS[i % 5]
    return ("We study %s using %s when the data show %s. Our estimation procedure is simple and its error shrinks as the sample grows. "
            "Simulations in scenario %d and a real data set agree with the theory. All code for case %d is available on request." % (t, m, s, i, i)) + EXTRA.get(i, "")


def wrap_abstract(text, i):
    if i not in SPLITS:
        return textwrap.wrap(text, 70, break_on_hyphens=False)
    word, k = SPLITS[i]
    cut = text.index(word) + k
    head, tail = text[:cut] + ("" if text[cut - 1] == "-" else "-"), text[cut:]
    return textwrap.wrap(head, 70, break_on_hyphens=False) + textwrap.wrap(tail, 70, break_on_hyphens=False)


def paginate(tagged, per, head, foot):
    """-> (text, entries whose abstract a page break splits). A page starts with a form feed, as pdftotext prints it."""
    out, page, n, split, prev, ff = [], 1, 0, set(), None, False

    def put(text):
        nonlocal ff
        out.append(("\f" if ff else "") + text); ff = False

    for text, tag in tagged:
        if n >= per and not (tag == prev and tag[0] == "title"):  # a title is not split over two pages, but its marker may start the next one, as in a real book
            if prev and prev[0] == "abs" and tag == prev:
                split.add(tag[1])
            for x in foot(page):
                put(x)
            page += 1; n = 0; ff = True
            for x in head(page):
                put(x)
        put(text); n += 1; prev = tag
    return "\n".join(out) + "\n", split


class Program:
    """text, the true record of every entry (truth), entries split by a page break, number of wrapped headings and of session headings."""
    def __init__(self, layout, wrong_weekday=False, no_title=(), short=()):
        L, a = LAYOUTS[layout], layout == "a"
        tagged, self.truth, self.joins, self.sessions, i = [(x, "front") for x in L["front"]], [], 0, 0, 0
        for k, (offset, blocks) in enumerate(L["schedule"]):
            d = L["day0"] + datetime.timedelta(days=offset)
            tagged.append((L["day"](k, d, wrong_weekday and a and k == 2), "head"))
            for name, s, e, sessions, n in blocks:
                tagged.append((L["block"](name, s, e), "head"))
                for session in sessions:
                    if session:
                        tagged += [(x, "head") for x in session_lines(*session[0:2], session[2])]
                        self.joins += session[2] != "line"; self.sessions += 1
                    for _ in range(n):
                        title = title_of(i)
                        text = "A short note on case %d." % i if i in short else abstract_of(i)
                        tagged += [(x, ("title", i)) for x in textwrap.wrap(title, 56, break_on_hyphens=False) if i not in no_title]
                        tagged += [(L["marker"](i), "marker")] + [(x, ("abs", i)) for x in (textwrap.wrap(text, 70) if i in short else wrap_abstract(text, i))] + [("", "gap")] * 2
                        ts = lambda t: "%s %02d:%s" % (d, int(t.split(":")[0]), t.split(":")[1])
                        self.truth.append(dict(title="" if i in no_title else title, abstract=text, authors=authors(layout, i), start=ts(s), end=ts(e),
                                               session=session[0] if session else None, room=session[1] if session else None))
                        i += 1
        tagged += [(x, "back") for x in L["back"]]
        self.text, self.split = paginate(tagged, L["per"], L["head"], L["foot"])


def mapping(layout, **text):
    a = layout == "a"
    heads = {"day": "^(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday) \\d{1,2} March$" if a else "^DAY \\d – (?:Thursday|Friday|Saturday), April \\d{1,2}$",
             "block": "^(?P<block>.+?): (?P<start>\\d{1,2}:\\d\\d)[–-](?P<end>\\d{1,2}:\\d\\d)$" if a else "^(?P<block>.+?) \\((?P<start>\\d{1,2}:\\d\\d) - (?P<end>\\d{1,2}:\\d\\d)\\)$"}
    if a:
        heads["session"] = "^(?P<session>.+?) \\((?:Room )?(?P<room>A1|B2|C3|Main Hall)\\)$"
    t = {"year": 2027, "start_after": "^%s$" % LAYOUTS[layout]["day"](0, LAYOUTS[layout]["day0"], False), "end_before": "^(?:Presenter|Author) Index$",
         "drop": ["^Programme 2027\\s+Index$", "^\\d{1,3}$"] if a else ["^Book of Abstracts 2027$", "^– \\d{1,3} –$"],
         "headings": heads, "entry": {"marker": "^Presenter: (?P<presenter>.+)$" if a else "^Authors: (?P<authors>.+)$"}}
    t.update(text)
    fields = {"id": {"sequence": True}, "title": "title", "abstract": "abstract", "start": "start", "end": "end"}
    if a:
        fields.update(session="session", hall="room")
    return {"text": t, "fields": fields, "authors": {"column": "presenter" if a else "authors"},
            "time": {"zone": "Asia/Tokyo" if a else "Asia/Kolkata", "format": "%Y-%m-%d %H:%M"},
            "meta": {"name": "Synthetic Meeting " + layout.upper(), "slug": "synth-" + layout, "year": 2027}}


def run(script, *args, path=None):
    env = dict(ti.ENV, **({"PATH": path} if path is not None else {}))
    return subprocess.run([sys.executable, script, *args], capture_output=True, text=True, env=env)


class TextEntries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a, cls.b = Program("a"), Program("b")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def write(self, name, text):
        with open(self.path(name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return self.path(name)

    def do_import(self, prog, m, name="book.txt", path=None, src=None):
        self.write("map.json", json.dumps(m))
        return run(ti.IMPORTER, "import", src or self.write(name, prog.text), "--mapping", self.path("map.json"), "--out", self.out, path=path)

    def imported(self, prog, m, **kw):
        r = self.do_import(prog, m, **kw)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def records(self):
        with gzip.open(os.path.join(self.out, "papers.json.gz"), "rt", encoding="utf-8") as f:
            return json.load(f)

    def refused(self, r, *words):
        self.assertEqual(r.returncode, 1, r.stdout)
        for w in words:
            self.assertIn(w.lower(), r.stderr.lower())
        self.assertFalse(os.path.exists(self.out), "nothing may be written when the import is refused")

    def check_all(self, prog, recs):
        self.assertEqual(len(recs), len(prog.truth))
        for k, (r, t) in enumerate(zip(recs, prog.truth), 1):
            self.assertEqual(r["id"], str(k))
            self.assertEqual((r["title"], r["abstract"], r["authors"]), (t["title"], t["abstract"], t["authors"]), "entry %d" % k)
            self.assertEqual((r.get("local_start"), r.get("local_end")), (t["start"], t["end"]), "entry %d" % k)
            self.assertEqual((r.get("session"), r.get("hall")), (t["session"], t["room"]), "entry %d" % k)

    # --- layout A: what comes out
    def test_every_entry_comes_out_with_its_title_abstract_presenter_day_block_session_and_room(self):
        self.assertEqual(len(self.a.truth), 60)
        self.assertIn("\fPresenter:", self.a.text)  # a title above a page break, its marker at the top of the next page
        self.assertIn("Book of Abstracts 2027\nAuthors:", self.b.text)
        self.imported(self.a, mapping("a"))
        self.check_all(self.a, self.records())

    def test_footers_page_numbers_and_the_index_at_the_back_stay_out_and_a_page_break_inside_an_abstract_joins_up(self):
        self.assertTrue(self.a.split, "the fixture needs an abstract that a page break splits")
        self.assertGreater(self.a.text.count("\f"), 15)
        self.imported(self.a, mapping("a"))
        recs = self.records()
        self.assertEqual({r["abstract"] for r in recs if "Index" in r["abstract"] or "Programme" in r["abstract"]}, set())
        self.assertEqual(recs[-1]["abstract"], self.a.truth[-1]["abstract"])  # the index after the last entry is not part of it
        self.assertEqual(recs[sorted(self.a.split)[0]]["abstract"], self.a.truth[sorted(self.a.split)[0]]["abstract"])

    def test_line_end_hyphens_are_joined_unless_the_document_spells_the_word_with_a_hyphen(self):
        r = self.imported(self.a, mapping("a"))
        recs = self.records()
        self.assertIn("spike-and-slab prior", recs[9]["abstract"])  # kept: the hyphenated form is used elsewhere, the joined one is not
        self.assertIn("estimation procedure", recs[13]["abstract"])  # joined: "estimation" is used elsewhere
        self.assertIn("multilevel model", recs[17]["abstract"])  # joined: neither form is used elsewhere
        self.assertIn("line-end hyphens joined 2, kept 1", r.stdout)

    def test_the_report_counts_entries_headings_and_joins(self):
        r = self.imported(self.a, mapping("a"))
        self.assertIn("text: 60 entries (30 with a session); headings: day 3, block 7, session 11; wrapped headings joined %d;" % self.a.joins, r.stdout)
        with open(os.path.join(self.out, "meta.json"), encoding="utf-8") as f:
            self.assertIn("cut out of the book's text by patterns", json.load(f)["notice"])

    def test_a_wrapped_room_and_a_room_on_its_own_line_are_joined_to_the_session_heading(self):
        self.imported(self.a, mapping("a"))
        by = collections.Counter((r.get("session"), r.get("hall")) for r in self.records())
        self.assertEqual(by[("Spatial models", "B2")], 3)  # "Spatial models (Room" + "B2)"
        self.assertEqual(by[("Open forum", "Main Hall")], 3)  # "Open forum" + "(Room Main Hall)"
        self.assertEqual(by[(None, None)], 30)  # plenary talks and posters: no session, no hall

    def test_day_and_block_are_carried_to_every_entry_and_the_poster_block_clears_the_session(self):
        self.imported(self.a, mapping("a"))
        posters = [r for r in self.records() if r.get("local_start", "").endswith("15:00")]
        self.assertEqual(len(posters), 28)
        self.assertEqual({r["local_start"][:10] for r in posters}, {"2027-03-14", "2027-03-15"})
        self.assertFalse([r for r in posters if "session" in r or "hall" in r])

    def test_times_are_local_at_the_site_and_the_calendar_converts_them_to_utc(self):
        self.imported(self.a, mapping("a"))
        plenary = run(ti.ENGINE, "ics", "--data", self.out, "1").stdout.splitlines()
        self.assertIn("DTSTART:20270314T000000Z", plenary)  # 9:00 in Tokyo
        self.assertFalse([x for x in plenary if x.startswith("LOCATION")])
        talk = run(ti.ENGINE, "ics", "--data", self.out, "3").stdout.splitlines()
        self.assertIn("DTSTART:20270314T023000Z", talk)  # 11:30 in Tokyo
        self.assertIn("DTEND:20270314T040000Z", talk)
        self.assertIn("LOCATION:A1", talk)

    def test_a_weekday_that_does_not_match_its_date_is_an_error_until_day_overrides_settles_it(self):
        wrong = Program("a", wrong_weekday=True)
        self.refused(self.do_import(wrong, mapping("a")), "Monday 16 March", "Tuesday", "day_overrides")
        self.imported(wrong, mapping("a", day_overrides={"Monday 16 March": "2027-03-16"}))
        self.assertEqual(self.records()[-1]["local_start"], "2027-03-16 09:00")

    def test_a_misspelt_override_is_a_warning(self):
        r = self.imported(self.a, mapping("a", day_overrides={"Funday 1 March": "2027-03-01"}))
        self.assertRegex(r.stdout, r"warning: .*Funday 1 March")

    def test_sequence_ids_are_unique_and_follow_the_document(self):
        self.imported(self.a, mapping("a"))
        self.assertEqual([r["id"] for r in self.records()], [str(k) for k in range(1, 61)])

    # --- what is refused or warned about
    def test_a_heading_pattern_that_matches_nothing_is_refused_and_named(self):
        m = mapping("a"); m["text"]["headings"]["block"] = "^NO SUCH HEADING$"
        self.refused(self.do_import(self.a, m), "headings.block")

    def test_an_entry_marker_that_matches_nothing_and_a_missing_marker_are_refused(self):
        m = mapping("a"); m["text"]["entry"]["marker"] = "^Speaker: (?P<presenter>.+)$"
        self.refused(self.do_import(self.a, m), "entry.marker")
        m = mapping("a"); del m["text"]["entry"]
        self.refused(self.do_import(self.a, m), "entry.marker")

    def test_a_pattern_that_is_not_a_regular_expression_is_refused_and_named(self):
        m = mapping("a"); m["text"]["headings"]["day"] = "(unclosed"
        self.refused(self.do_import(self.a, m), "headings.day")

    def test_a_start_pattern_that_matches_nothing_is_refused(self):
        self.refused(self.do_import(self.a, mapping("a", start_after="^Nothing like this$")), "start_after")

    def test_one_entry_in_sixty_without_a_title_is_over_the_one_percent_limit(self):
        self.refused(self.do_import(Program("a", no_title=(7,)), mapping("a")), "title")

    def test_a_text_mapping_needs_a_text_file_and_a_text_file_needs_a_text_mapping(self):
        self.refused(self.do_import(self.a, mapping("a"), name="book.csv"), "text")
        m = mapping("a"); del m["text"]
        self.refused(self.do_import(self.a, m), "text")

    def test_short_abstracts_warn_when_under_90_percent_have_20_words(self):
        r = self.imported(Program("a", short=tuple(range(0, 60, 5))), mapping("a"))  # 12 of 60 are short
        self.assertRegex(r.stdout, r"warning: .*20 words or more")

    def test_a_footer_left_in_the_text_is_reported_as_a_repeated_line(self):
        m = mapping("a"); m["text"]["drop"] = ["^\\d{1,3}$"]
        r = self.imported(self.a, m)
        self.assertRegex(r.stdout, r"warning: .*repeated.*Programme 2027")

    def test_an_unexpected_session_count_is_a_warning_showing_both_numbers(self):
        r = self.imported(self.a, mapping("a", expect_sessions=12))
        self.assertRegex(r.stdout, r"warning: .*expected 12.*found 11")
        self.assertNotIn("expected", self.imported_again(mapping("a", expect_sessions=11)).stdout)

    def imported_again(self, m):
        return run(ti.IMPORTER, "import", self.path("book.txt"), "--mapping", self.write("map.json", json.dumps(m)), "--out", self.out + "2")

    # --- inspect, pdf, book pages, search
    def test_inspect_shows_the_structure_in_under_3_kb(self):
        for prog, label in ((self.a, "Presenter: 60"), (self.b, "Authors: 60")):
            r = run(ti.IMPORTER, "inspect", self.write("book.txt", prog.text))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertLessEqual(len(r.stdout), 3000)
            self.assertIn(label, r.stdout)
            lines = prog.text.split("\n")
            first_marker = next(n for n, x in enumerate(lines, 1) if x.startswith(label.split(":")[0] + ":"))
            self.assertIn("L%d" % first_marker, r.stdout)
            self.assertIn("pages: %d" % (prog.text.count("\f") + 1), r.stdout)

    def test_a_pdf_goes_through_pdftotext_when_it_is_on_the_path(self):
        txt, args = self.write("book.txt", self.a.text), self.path("args.txt")
        os.makedirs(self.path("bin"))
        with open(self.path("bin/pdftotext"), "w") as f:
            f.write('#!/bin/sh\necho "$@" > "%s"\n/bin/cat "%s"\n' % (args, txt))
        os.chmod(self.path("bin/pdftotext"), 0o755)
        pdf = self.path("book.pdf")
        with open(pdf, "wb") as f:
            f.write(b"%PDF-1.4 not a real pdf")
        self.imported(self.a, mapping("a"), src=pdf, path=self.path("bin"))
        self.check_all(self.a, self.records())
        self.assertEqual(open(args).read().split(), ["-layout", pdf, "-"])
        r = run(ti.IMPORTER, "inspect", pdf, path=self.path("bin"))
        self.assertIn("Presenter: 60", r.stdout)

    def test_a_pdf_without_pdftotext_prints_the_command_and_stops(self):
        pdf = self.path("book.pdf")
        with open(pdf, "wb") as f:
            f.write(b"%PDF-1.4 not a real pdf")
        os.makedirs(self.path("empty"))
        self.refused(self.do_import(self.a, mapping("a"), src=pdf, path=self.path("empty")), "pdftotext -layout", pdf, "book.txt")
        self.assertEqual(run(ti.IMPORTER, "inspect", pdf, path=self.path("empty")).returncode, 1)

    def test_book_pages_come_from_the_page_breaks_and_show_prints_them(self):
        m = mapping("a", page_offset=-1); m["fields"]["page"] = "page"
        self.imported(self.a, m)
        lines, page, where = self.a.text.split("\n"), 1, {}
        for x in lines:
            page += x.count("\f")
            where.setdefault(x.strip(), page)
        first = lambda k: textwrap.wrap(title_of(k), 56, break_on_hyphens=False)[0]
        for k in (0, 29, 59):
            self.assertEqual(self.records()[k]["page"], str(where[first(k)] - 1))
            self.assertIn("book page %d" % (where[first(k)] - 1), run(ti.ENGINE, "show", str(k + 1), "--data", self.out, "--no-abstract").stdout)
        self.imported_again(mapping("a"))  # no page_offset: no pages
        self.assertNotIn("book page", run(ti.ENGINE, "show", "1", "--data", self.out + "2").stdout)

    def test_the_default_pool_is_a_fifth_of_the_dataset_between_40_and_150(self):
        self.imported(self.a, mapping("a"))
        rows = lambda *a: run(ti.ENGINE, "find", "--paper", "1", *a).stdout.splitlines()
        self.assertEqual(rows("--data", self.out), rows("--data", self.out, "-k", "40"))  # 60 entries: 40
        self.assertEqual(len(rows("--data", self.out)), 41)
        big = os.path.join(self.tmp.name, "big.csv")
        with open(big, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=ti.CSV_COLS)
            w.writeheader(); w.writerows(ti.csv_rows(300))
        self.write("csvmap.json", json.dumps(ti.CSV_MAP))
        self.assertEqual(run(ti.IMPORTER, "import", big, "--mapping", self.path("csvmap.json"), "--out", self.path("big")).returncode, 0)
        pool = lambda *a: run(ti.ENGINE, "find", "--data", self.path("big"), "--paper", "1001", *a).stdout.splitlines()
        self.assertEqual(pool(), pool("-k", "60"))  # 300 posters: 60

    # --- layout B: another marker, other heading words, no sessions or rooms
    def test_the_authors_layout_imports_with_affiliations_and_without_sessions_or_rooms(self):
        r = self.imported(self.b, mapping("b"))
        self.check_all(self.b, self.records())
        self.assertIn("text: 60 entries; headings: day 3, block 6; wrapped headings joined 0;", r.stdout)
        self.assertFalse([x for x in self.records() if "session" in x or "hall" in x])

    def test_who_finds_the_authors_of_the_authors_layout_by_institution(self):
        self.imported(self.b, mapping("b"))
        want = sum(any(a in ("UT Austin", "University of Texas at Austin") for _, a in authors("b", i)) for i in range(60))
        r = run(ti.ENGINE, "who", "--data", self.out, "--affil", "UT Austin")
        self.assertTrue(r.stdout.startswith("# %d papers" % want), r.stdout[:200])
        self.assertIn("University of Texas at Austin", r.stdout.splitlines()[0])
        self.assertEqual(run(ti.ENGINE, "find", "--data", self.out, "--paper", "5").returncode, 0)

    def test_the_authors_layout_calendar_has_utc_times_and_no_location(self):
        self.imported(self.b, mapping("b"))
        ics = run(ti.ENGINE, "ics", "--data", self.out, "1").stdout.splitlines()
        self.assertIn("DTSTART:20270408T040000Z", ics)  # 9:30 in Kolkata
        self.assertFalse([x for x in ics if x.startswith("LOCATION")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
