#!/usr/bin/env python3
"""Tests for the --data option, the `list` command and the optional record fields of search.py.

Run: python3 tools/test_data_option.py   (about a minute: the last test re-runs the parity suite on the bundled data
converted to a dataset folder)
"""
import csv, gzip, io, json, os, re, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENGINE = os.path.join(ROOT, "plugins", "conference-picks", "skills", "conference-picks", "scripts", "search.py")
ENV = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}  # no -I: it would ignore the hash seed
ENV.update(PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")

GNN = "We study graph neural networks for node classification when few labels are available, using message passing over the graph."
LABEL = "Label propagation spreads a few known labels over the graph for node classification with graph neural networks."
DIFF = "Diffusion models generate images and classifier guidance improves image generation quality."
FAST = "Fewer sampling steps make diffusion models faster for image generation."


def run(*args, home=None):
    env = dict(ENV, **({"CONFERENCE_PICKS_HOME": home} if home else {}))
    return subprocess.run([sys.executable, ENGINE, *args], capture_output=True, text=True, env=env)


def rec(id, title, abstract, authors, **extra):
    return dict(id=id, title=title, abstract=abstract, authors=authors, **extra)


def timed(id, title, abstract, day, **extra):  # a poster with a time but no city, hall or oral flag
    return rec(id, title, abstract, [["Gil Hart", "Example Institute"]], type="Poster", url="https://example.org/p/" + id,
               session="Poster Session 1", local_start=day + " 10:00", local_end=day + " 12:00", **extra)


def write_dataset(path, records, meta):
    os.makedirs(path)
    with gzip.open(os.path.join(path, "papers.json.gz"), "wt", encoding="utf-8") as f:
        json.dump(records, f)
    with open(os.path.join(path, "meta.json"), "w") as f:
        json.dump(meta, f)


def find_rows(stdout):  # rows of `find` output, header dropped
    return [line.split("\t") for line in stdout.splitlines()[1:]]


def who_rows(stdout):
    return [line.split("\t") for line in stdout.splitlines() if not line.startswith("#") and not line.startswith("id\t")]


# no schedule, no city, no type, no url, ids of the shapes OpenReview and others use
MINI = [
    rec("WNKKtAYqX0", "Graph neural networks for node classification", GNN, [["Ada Byron", "UT Austin, CS"], ["Bo Chen", "Example Institute"]]),
    rec("ab1c", "Label propagation for node classification", LABEL, [["Cy Dunn", "Example Institute"]]),
    rec("9xZ", "Message passing for molecular graphs", "Message passing neural networks predict properties of molecular graphs.", [["Di Evans", "Other University"]]),
    rec("k-77", "Diffusion models for image generation", DIFF, [["Ed Fox", "Other University"]]),
    rec("k-78", "Fast sampling for diffusion models", FAST, [["Fay Gold", "Example Institute"]]),
]
# times in one zone, no city or hall, one workshop that must not be searched
TIMED = [
    timed("t1", "Graph neural networks for node classification", GNN, "2027-04-26"),
    timed("t2", "Label propagation for node classification", LABEL, "2027-04-26"),
    timed("t3", "Diffusion models for image generation", DIFF, "2027-04-27"),
    timed("t4", "Fast sampling for diffusion models", FAST, "2027-04-27"),
    rec("w1", "Workshop on graph neural networks", "A workshop on graph neural networks and node classification.",
        [["Ivy Jones", "Example Institute"]], type="Workshop", url="https://example.org/w/w1"),
]


class DataOption(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.home = os.path.join(cls.tmp.name, "home")
        cls.mini, cls.timed = os.path.join(cls.home, "mini2027"), os.path.join(cls.home, "timed2027")
        write_dataset(cls.mini, MINI, {"name": "Mini Conf 2027", "slug": "mini2027", "link_template": "https://example.org/paper/{id}"})
        write_dataset(cls.timed, TIMED, {"name": "Timed Conf 2027", "slug": "timed2027", "zone": "Europe/Berlin", "paper_types": ["Poster"]})

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_find_takes_string_ids(self):
        r = run("find", "--data", self.mini, "--paper", "WNKKtAYqX0", "-k", "5")
        self.assertEqual(r.returncode, 0, r.stderr)
        ids = [x[1] for x in find_rows(r.stdout)]
        self.assertIn("ab1c", ids)
        self.assertNotIn("WNKKtAYqX0", ids)

    def test_find_takes_an_openreview_style_url(self):
        r = run("find", "--data", self.mini, "--paper", "https://openreview.net/forum?id=WNKKtAYqX0", "-k", "5")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("WNKKtAYqX0", [x[1] for x in find_rows(r.stdout)])

    def test_find_unknown_paper_names_the_conference(self):
        r = run("find", "--data", self.mini, "--paper", "nope-123")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Mini Conf 2027", r.stderr)

    def test_find_prints_a_dash_when_there_is_no_schedule(self):
        r = run("find", "--data", self.mini, "--paper", "WNKKtAYqX0", "-k", "5")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual({x[3] for x in find_rows(r.stdout)}, {"-"})

    def test_find_searches_only_the_paper_types_in_meta(self):
        r = run("find", "--data", self.timed, "--paper", "t1", "-k", "10")
        self.assertEqual(r.returncode, 0, r.stderr)
        ids = [x[1] for x in find_rows(r.stdout)]
        self.assertIn("t2", ids)
        self.assertNotIn("w1", ids)

    def test_where_has_no_site_when_records_have_no_city(self):
        r = run("find", "--data", self.timed, "--paper", "t1", "-k", "10")
        self.assertEqual(r.returncode, 0, r.stderr)
        where = {x[1]: x[3] for x in find_rows(r.stdout)}
        self.assertRegex(where["t2"], r"^[A-Z][a-z]{2} 2027-04-26 10:00$")

    def test_show_uses_the_link_template_when_a_record_has_no_url(self):
        r = run("show", "--data", self.mini, "WNKKtAYqX0", "--no-abstract")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("https://example.org/paper/WNKKtAYqX0", r.stdout)

    def test_show_reports_an_unknown_id(self):
        r = run("show", "--data", self.mini, "nope-123")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nope-123: not found", r.stdout)

    def test_who_finds_a_name(self):
        r = run("who", "--data", self.mini, "--name", "ada byron")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([x[0] for x in who_rows(r.stdout)], ["WNKKtAYqX0"])

    def test_who_affil_falls_back_to_regex_without_an_institutions_table(self):
        r = run("who", "--data", self.mini, "--affil", "UT Austin")  # a NeurIPS alias, but this dataset has no table
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([x[0] for x in who_rows(r.stdout)], ["WNKKtAYqX0"])
        self.assertNotIn("University of Texas at Austin", r.stdout)

    def test_csv_uses_the_link_template_and_leaves_site_and_institutions_empty(self):
        r = run("csv", "--data", self.mini, "WNKKtAYqX0,ab1c")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = list(csv.DictReader(io.StringIO(r.stdout)))
        self.assertEqual([x["id"] for x in rows], ["WNKKtAYqX0", "ab1c"])
        self.assertEqual(rows[0]["link"], "https://example.org/paper/WNKKtAYqX0")
        self.assertEqual((rows[0]["site"], rows[0]["institutions"]), ("", ""))

    def test_ics_refuses_a_dataset_without_times(self):
        r = run("ics", "--data", self.mini, "WNKKtAYqX0")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no session times", r.stderr)

    def test_ics_uses_the_dataset_time_zone_and_slug(self):
        r = run("ics", "--data", self.timed, "t2")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertIn("DTSTART:20270426T080000Z", lines)  # 10:00 in Berlin (UTC+2 in April)
        self.assertIn("DTEND:20270426T100000Z", lines)
        self.assertIn("UID:t2@timed2027-picks", lines)
        self.assertIn("PRODID:-//neurips-picks//EN", lines)  # unchanged on purpose for now
        self.assertFalse([x for x in lines if x.startswith("LOCATION")])  # no hall and no city

    def test_a_missing_dataset_folder_points_to_list(self):
        r = run("find", "--data", "/nonexistent/xyz", "--paper", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("/nonexistent/xyz", r.stderr)
        self.assertIn("list", r.stderr)

    def test_an_unknown_slug_points_to_list(self):
        r = run("find", "--data", "nosuch", "--paper", "x", home=self.home)
        self.assertEqual(r.returncode, 1)
        self.assertIn("nosuch", r.stderr)
        self.assertIn("list", r.stderr)

    def test_a_slug_resolves_under_conference_picks_home(self):
        r = run("find", "--data", "mini2027", "--paper", "WNKKtAYqX0", "-k", "5", home=self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ab1c", [x[1] for x in find_rows(r.stdout)])

    def test_list_shows_the_bundled_and_the_installed_datasets(self):
        r = run("list", home=self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [x.split("\t") for x in r.stdout.splitlines()]
        self.assertEqual(lines[0][:2], ["slug", "name"])
        self.assertEqual({x[0]: x[1] for x in lines[1:]},
                         {"neurips2026": "NeurIPS 2026", "mini2027": "Mini Conf 2027", "timed2027": "Timed Conf 2027"})

    def test_bundled_data_as_a_dataset_folder_matches_the_baseline(self):  # slow
        with tempfile.TemporaryDirectory() as d:
            dst = os.path.join(d, "neurips2026")
            subprocess.run([sys.executable, os.path.join(HERE, "parity.py"), "convert", dst], check=True, capture_output=True)
            r = subprocess.run([sys.executable, os.path.join(HERE, "parity.py"), "check", "--data", dst], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
