#!/usr/bin/env python3
"""Profile mode without the network: the ORCID record fallback, abstracts by DOI and title, and what happens when a chat sandbox is offline.

No test here goes online. "Offline" is a proxy that refuses every connection (HTTPS_PROXY=http://127.0.0.1:9), as a sandbox without network does.
Run: python3 tools/test_profile.py
"""
import importlib.util, json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH = os.path.join(os.path.dirname(HERE), "plugins", "conference-picks", "skills", "conference-picks", "scripts", "search.py")
spec = importlib.util.spec_from_file_location("search", SEARCH)
search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(search)

RECORD = {"group": [  # the shape of pub.orcid.org/v3.0/<orcid>/works, with made-up works
    {"work-summary": [{"title": {"title": {"value": "An older paper"}}, "publication-date": {"year": {"value": "2022"}},
                       "external-ids": {"external-id": [{"external-id-type": "doi", "external-id-value": "10.1000/ABC.123"}]}}]},
    {"work-summary": [{"title": {"title": {"value": "A newer paper"}}, "publication-date": {"year": {"value": "2025"}},
                       "journal-title": {"value": "Journal of Tests"}, "external-ids": {"external-id": [{"external-id-type": "issn", "external-id-value": "1234-5678"}]}}]},
    {"work-summary": [{"title": {"title": {"value": "Undated preprint"}}, "publication-date": None}]},
    {"work-summary": [{"title": None}]},  # no title: skipped
]}


def run(*args, offline=True, cwd=None):
    env = dict(os.environ, **({"HTTPS_PROXY": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9"} if offline else {}))
    return subprocess.run([sys.executable, SEARCH, *args], capture_output=True, text=True, env=env, cwd=cwd)


class OrcidRecord(unittest.TestCase):
    def test_works_are_read_newest_first_with_lowercase_dois(self):
        works = search.orcid_works(RECORD)
        self.assertEqual([w["title"] for w in works], ["A newer paper", "An older paper", "Undated preprint"])
        self.assertEqual(works[0]["venue"], "Journal of Tests")
        self.assertEqual(works[1]["doi"], "10.1000/abc.123")
        self.assertEqual((works[0]["doi"], works[2]["year"]), ("", ""))

    def test_an_empty_or_missing_record_gives_no_works(self):
        self.assertEqual(search.orcid_works({}), [])
        self.assertEqual(search.orcid_works(None), [])


class Abstracts(unittest.TestCase):
    def setUp(self):
        self.real, self.sleep, self.calls = search.oa, search.time.sleep, []

        def fake(path, **params):
            self.calls.append(params)
            if "filter" in params:  # the DOI batch
                return {"results": [{"doi": "https://doi.org/10.1000/abc.123", "abstract_inverted_index": {"found": [0], "by": [1], "doi": [2]},
                                     "cited_by_count": 7, "primary_location": {"source": {"display_name": "Venue From OpenAlex"}}}]}
            return {"results": [{"title": "A newer paper", "abstract_inverted_index": {"found": [0], "by": [1], "title": [2]}}]}
        search.oa, search.time.sleep = fake, lambda s: None

    def tearDown(self):
        search.oa, search.time.sleep = self.real, self.sleep

    def test_dois_first_in_one_request_then_titles(self):
        works = search.orcid_works(RECORD)
        search.add_abstracts(works)
        by = {w["title"]: w for w in works}
        self.assertEqual(by["An older paper"]["abstract"], "found by doi")
        self.assertEqual((by["An older paper"]["cited"], by["An older paper"]["venue"]), (7, "Venue From OpenAlex"))
        self.assertEqual(by["A newer paper"]["abstract"], "found by title")
        self.assertEqual(by["Undated preprint"]["abstract"], "")  # the fake title search returns another title
        self.assertEqual(sum("filter" in c for c in self.calls), 1)


class Offline(unittest.TestCase):
    def test_an_orcid_says_the_sandbox_is_offline_and_what_to_ask_for(self):
        r = run("profile", "--orcid", "0009-0000-0000-0000")
        self.assertEqual(r.returncode, 1)
        for phrase in ("probably offline", "Do not search the web", "BibTeX", "--titles-file"):
            self.assertIn(phrase, r.stderr)

    def test_a_name_search_says_the_same(self):
        r = run("profile", "--name", "Ann Lee")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Do not search the web", r.stderr)

    def test_a_title_list_with_lookup_keeps_the_titles(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "t.txt"), "w", encoding="utf-8") as f:
                f.write("Kernel mean embeddings\nDiffusion models for imaging\n")
            r = run("profile", "--titles-file", "t.txt", "--lookup", "--save", "p.json", cwd=d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("continuing with titles only", r.stdout)
            with open(os.path.join(d, "p.json"), encoding="utf-8") as f:
                self.assertEqual([w["title"] for w in json.load(f)], ["Kernel mean embeddings", "Diffusion models for imaging"])

    def test_bibtex_and_titles_need_no_network(self):
        fixtures = os.path.join(HERE, "fixtures")
        for args in (["--bibtex", os.path.join(fixtures, "works.bib")], ["--titles-file", os.path.join(fixtures, "titles.txt")]):
            r = run("profile", *args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("could not", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
