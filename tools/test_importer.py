#!/usr/bin/env python3
"""Tests for scripts/import_dataset.py (inspect and import) and for what search.py does with an imported dataset.

Run: python3 tools/test_importer.py   (about a minute: each test runs the importer, some also run search.py)
"""
import csv, datetime, gzip, hashlib, json, os, re, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(os.path.dirname(HERE), "plugins", "conference-picks", "skills", "conference-picks")
IMPORTER, ENGINE = os.path.join(SKILL, "scripts", "import_dataset.py"), os.path.join(SKILL, "scripts", "search.py")
ENV = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
ENV.update(PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
META = {"name": "Test Conf 2027", "slug": "test2027", "paper_types": ["Poster"]}
CSV_MAP = {"fields": {"id": {"column": "virtualsite_url", "regex": "/(\\d+)$"}, "title": "name", "abstract": "abstract",
                      "url": "virtualsite_url", "type": "type"},
           "authors": {"column": "speakers/authors"}, "meta": META}
CSV_COLS = ["type", "name", "virtualsite_url", "speakers/authors", "abstract"]
AUTHORS = ["Ann Lee (UT Austin)", "Cy Dunn (Example Institute), Di Evans (Other University)",
           "Bo Chen (University of Texas at Austin)", "Fay Gold (Example Institute)"]


def sh(script, *args, home=None):
    env = dict(ENV, **({"CONFERENCE_PICKS_HOME": home} if home else {}))
    return subprocess.run([sys.executable, script, *args], capture_output=True, text=True, env=env)


def csv_rows(n=60, start=1000):  # n posters with ids 1000.., then 3 tutorials whose URLs have no kind
    rows = [{"type": "Poster", "name": f"Paper {i} on topic{i % 7} &amp; methods", "virtualsite_url": f"https://conf.example/virtual/2027/poster/{start + i}",
             "speakers/authors": AUTHORS[i % 4], "abstract": f"We study topic{i % 7} with method {i}. The results are good &amp; clear."} for i in range(n)]
    rows += [{"type": "Tutorial", "name": f"Tutorial {j}", "virtualsite_url": f"https://conf.example/virtual/2027/{5000 + j}",
              "speakers/authors": "Gus Hill (Example Institute)", "abstract": f"A tutorial on topic{j}."} for j in range(3)]
    return rows


def json_records(n=60):  # half in Rio, half in Paris; times in UTC; both sessions start at 10:00 local
    out = []
    for i in range(n):
        rio = i % 2 == 0
        start = datetime.datetime(2027, 4, 26, 13 if rio else 8, 0, tzinfo=datetime.timezone.utc)
        out.append({"id": 100 + i, "name": f"Paper {i} on topic{i % 7}", "abstract": f"We study topic{i % 7} with method {i}.",
                    "authors": [{"fullname": "Ann Lee", "institution": "UT Austin"}, {"fullname": "Bo Chen", "institution": "Example Institute"}],
                    "site": "Rio" if rio else "Paris", "room_name": "Hall A", "session": "Poster Session 1",
                    "starttime": start.isoformat(), "endtime": (start + datetime.timedelta(hours=2)).isoformat()})
    return out


JSON_MAP = {"records": "results",
            "fields": {"id": "id", "title": "name", "abstract": "abstract", "city": "site", "hall": "room_name", "session": "session",
                       "start": "starttime", "end": "endtime"},
            "authors": {"column": "authors", "name": "fullname", "affil": "institution"},
            "time": {"zones": {"Rio": "America/Sao_Paulo", "Paris": "Europe/Paris"}},
            "meta": {"name": "Test Conf 2027", "slug": "test2027"}}  # no type column, so no paper_types: the importer refuses that mix


class Importer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def write_csv(self, rows, name="events.csv"):
        with open(self.path(name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        return self.path(name)

    def write_json(self, obj, name="events.json"):
        with open(self.path(name), "w", encoding="utf-8") as f:
            json.dump(obj, f)
        return self.path(name)

    def do_import(self, src, mapping, home=None, out=True):
        with open(self.path("map.json"), "w") as f:
            json.dump(mapping, f)
        return sh(IMPORTER, "import", src, "--mapping", self.path("map.json"), *(["--out", self.out] if out else []), home=home)

    def records(self):
        with gzip.open(os.path.join(self.out, "papers.json.gz"), "rt", encoding="utf-8") as f:
            return json.load(f)

    def meta(self):
        with open(os.path.join(self.out, "meta.json"), encoding="utf-8") as f:
            return json.load(f)

    def imported_csv(self, rows=None, mapping=None):
        r = self.do_import(self.write_csv(rows or csv_rows()), mapping or CSV_MAP)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def refuses(self, r, word):
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(word, r.stderr.lower())
        self.assertFalse(os.path.exists(self.out), "nothing may be written when the import is refused")

    # --- what a good import produces
    def test_import_writes_a_folder_that_search_can_use(self):
        self.imported_csv()
        r = sh(ENGINE, "find", "--data", self.out, "--paper", "1001", "-k", "3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertGreaterEqual(len(r.stdout.splitlines()), 2)

    def test_titles_are_unescaped_and_author_strings_are_split(self):
        self.imported_csv()
        by_id = {p["id"]: p for p in self.records()}
        self.assertEqual(by_id["1000"]["title"], "Paper 0 on topic0 & methods")
        self.assertIn("good & clear", by_id["1000"]["abstract"])
        self.assertEqual(by_id["1001"]["authors"], [["Cy Dunn", "Example Institute"], ["Di Evans", "Other University"]])

    def test_the_id_regex_reads_ids_from_urls_without_a_kind(self):
        self.imported_csv()
        self.assertTrue({"5000", "5001", "5002"} <= {p["id"] for p in self.records()})

    def test_meta_records_the_source_and_the_given_values(self):
        src = self.write_csv(csv_rows())
        r = self.do_import(src, CSV_MAP)
        self.assertEqual(r.returncode, 0, r.stderr)
        m = self.meta()
        self.assertEqual((m["name"], m["slug"], m["paper_types"]), ("Test Conf 2027", "test2027", ["Poster"]))
        self.assertEqual(m["source"], "events.csv")
        self.assertEqual(m["source_sha256"], hashlib.sha256(open(src, "rb").read()).hexdigest())
        self.assertEqual(m["records"], 63)
        self.assertRegex(m["snapshot_date"], r"^\d{4}-\d\d-\d\d$")
        self.assertTrue(m["notice"].startswith("Imported by you"))

    def test_a_dataset_without_times_is_valid(self):
        r = self.imported_csv()
        self.assertFalse([p for p in self.records() if "local_start" in p])
        self.assertIn("schedule: none", r.stdout)
        self.assertEqual(sh(ENGINE, "ics", "--data", self.out, "1000").returncode, 1)  # nothing to put in a calendar

    def test_the_report_shows_three_samples(self):
        r = self.imported_csv()
        self.assertEqual(len(re.findall(r"^sample \d/3", r.stdout, re.M)), 3)

    def test_the_institutions_table_merges_spellings_in_who_affil(self):
        self.imported_csv()
        r = sh(ENGINE, "who", "--data", self.out, "--affil", "UT Austin")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("# 30 papers"), r.stdout[:200])  # 15 say "UT Austin", 15 spell it out
        self.assertIn("University of Texas at Austin", r.stdout.splitlines()[0])

    def test_the_default_output_folder_is_under_conference_picks_home(self):
        home = self.path("home")
        r = self.do_import(self.write_csv(csv_rows()), CSV_MAP, home=home, out=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(home, "test2027", "papers.json.gz")))

    # --- json, jsonl, gzip, times
    def test_json_records_path_and_author_objects(self):
        r = self.do_import(self.write_json({"count": 60, "results": json_records()}), JSON_MAP)
        self.assertEqual(r.returncode, 0, r.stderr)
        p = {x["id"]: x for x in self.records()}["100"]
        self.assertEqual(p["authors"], [["Ann Lee", "UT Austin"], ["Bo Chen", "Example Institute"]])
        self.assertEqual((p["city"], p["hall"], p["session"]), ("Rio", "Hall A", "Poster Session 1"))

    def test_iso_times_become_local_times_in_the_site_zone(self):
        self.do_import(self.write_json({"results": json_records()}), JSON_MAP)
        by_id = {p["id"]: p for p in self.records()}
        self.assertEqual((by_id["100"]["local_start"], by_id["100"]["local_end"]), ("2027-04-26 10:00", "2027-04-26 12:00"))  # Rio
        self.assertEqual(by_id["101"]["local_start"], "2027-04-26 10:00")  # Paris
        self.assertEqual(self.meta()["zones"], {"Rio": "America/Sao_Paulo", "Paris": "Europe/Paris"})

    def test_search_can_make_a_calendar_from_an_imported_schedule(self):
        self.do_import(self.write_json({"results": json_records()}), JSON_MAP)
        r = sh(ENGINE, "ics", "--data", self.out, "100")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("DTSTART:20270426T130000Z", r.stdout.splitlines())  # 10:00 in Rio is 13:00 UTC

    def test_naive_times_are_kept_with_a_fixed_zone(self):
        rows = [dict(r, start="2027-04-26 10:00", end="2027-04-26 12:00") for r in csv_rows()]
        mapping = json.loads(json.dumps(CSV_MAP))
        mapping["fields"].update(start="start", end="end")
        mapping["time"] = {"zone": "Europe/Berlin", "format": "%Y-%m-%d %H:%M"}
        self.assertEqual(self.do_import(self.write_csv(rows), mapping).returncode, 0)
        self.assertEqual(self.records()[0]["local_start"], "2027-04-26 10:00")
        self.assertEqual(self.meta()["zone"], "Europe/Berlin")

    def test_gzipped_jsonl_is_read(self):
        path = self.path("events.jsonl.gz")
        with gzip.open(path, "wt", encoding="utf-8") as f:
            f.writelines(json.dumps(x) + "\n" for x in json_records())
        mapping = dict(JSON_MAP); del mapping["records"]
        r = self.do_import(path, mapping)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.records()), 60)

    # --- what is refused (and nothing is written)
    def test_refuses_fewer_than_50_records(self):
        self.refuses(self.do_import(self.write_csv(csv_rows(49)[:49]), CSV_MAP), "50")

    def test_refuses_when_over_5_percent_of_titles_are_missing(self):
        rows = csv_rows()
        for r in rows[:5]:
            r["name"] = ""
        self.refuses(self.do_import(self.write_csv(rows), CSV_MAP), "title")

    def test_refuses_when_under_half_of_the_abstracts_are_there(self):
        rows = csv_rows()
        for r in rows[:35]:
            r["abstract"] = ""
        self.refuses(self.do_import(self.write_csv(rows), CSV_MAP), "abstract")

    def test_refuses_when_over_half_a_percent_of_ids_repeat(self):
        rows = csv_rows()
        rows[1]["virtualsite_url"] = rows[0]["virtualsite_url"]
        rows[3]["virtualsite_url"] = rows[2]["virtualsite_url"]
        self.refuses(self.do_import(self.write_csv(rows), CSV_MAP), "duplicate")

    def test_refuses_times_without_a_time_zone(self):
        mapping = json.loads(json.dumps(JSON_MAP)); del mapping["time"]
        self.refuses(self.do_import(self.write_json({"results": json_records()}), mapping), "time zone")

    def test_refuses_an_end_that_is_not_after_the_start(self):
        recs = json_records()
        recs[3]["endtime"] = recs[3]["starttime"]
        self.refuses(self.do_import(self.write_json({"results": recs}), JSON_MAP), "end")

    def test_refuses_an_unknown_column_and_lists_the_real_ones(self):
        mapping = json.loads(json.dumps(CSV_MAP)); mapping["fields"]["title"] = "headline"
        r = self.do_import(self.write_csv(csv_rows()), mapping)
        self.refuses(r, "headline")
        self.assertIn("speakers/authors", r.stderr)

    def test_refuses_paper_types_that_no_record_has(self):
        mapping = json.loads(json.dumps(CSV_MAP)); del mapping["fields"]["type"]  # paper_types stays: nothing could ever match
        self.refuses(self.do_import(self.write_csv(csv_rows()), mapping), "paper_types")

    def test_line_breaks_inside_cells_become_plain_newlines(self):
        rows = csv_rows()
        rows[0]["abstract"] = "first line\r\nsecond line\r<br>third"
        self.assertEqual(self.do_import(self.write_csv(rows), CSV_MAP).returncode, 0)
        self.assertEqual({p["id"]: p for p in self.records()}["1000"]["abstract"], "first line\nsecond line\n<br>third")

    # --- warnings (the import still happens)
    def test_rows_repeated_exactly_are_dropped_with_a_warning_and_are_not_an_id_problem(self):
        rows = csv_rows()
        rows += rows[:20]  # some exports list every row twice
        r = self.do_import(self.write_csv(rows), CSV_MAP)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.records()), 63)
        self.assertRegex(r.stdout.lower(), r"warning: 20 identical duplicate rows")

    def test_records_without_an_id_are_kept_and_are_not_duplicates_of_each_other(self):
        rows = csv_rows()
        for r in rows[:3]:
            r["virtualsite_url"] = "https://conf.example/virtual/2027/session/x"  # the id regex finds nothing
        r = self.do_import(self.write_csv(rows), CSV_MAP)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.records()), 63)
        self.assertIn("warning: 3 records have no id", r.stdout.lower())

    def test_warns_when_abstracts_are_under_80_percent(self):
        rows = csv_rows()
        for r in rows[:15]:
            r["abstract"] = ""
        r = self.do_import(self.write_csv(rows), CSV_MAP)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.lower(), r"warning: .*abstract")

    def test_a_single_repeated_id_in_200_rows_is_dropped_with_a_warning(self):
        rows = csv_rows(200)
        rows[1]["virtualsite_url"] = rows[0]["virtualsite_url"]
        r = self.do_import(self.write_csv(rows), CSV_MAP)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.lower(), r"warning: .*duplicate")
        self.assertEqual(len(self.records()), 202)  # 203 rows, one dropped

    # --- inspect
    def test_inspect_lists_columns_with_samples_and_stays_short(self):
        r = sh(IMPORTER, "inspect", self.write_csv(csv_rows()))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertLessEqual(len(r.stdout), 3500)
        self.assertIn("rows: 63", r.stdout)
        self.assertIn("virtualsite_url", r.stdout)
        self.assertIn("Paper 0", r.stdout)

    def test_inspect_finds_the_records_inside_a_json_object(self):
        r = sh(IMPORTER, "inspect", self.write_json({"count": 60, "results": json_records()}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("records: results", r.stdout)
        self.assertIn("starttime", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
