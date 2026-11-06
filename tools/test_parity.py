#!/usr/bin/env python3
"""Tests for `parity.py record --rebaseline-data`: a deliberate refresh of the bundled data must be possible without hand-editing the
baseline, and must still prove that the engine is the frozen one.

Each test works in a local clone of this repository, with this tree's tools/parity.py copied in, so the real baseline is never touched.
Run: python3 tools/test_parity.py   (about a minute: a record or a check runs the 22 parity cases)
"""
import gzip, hashlib, json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILL = os.path.join("plugins", "conference-picks", "skills", "conference-picks")
PY = "%d.%d" % sys.version_info[:2]


def parity(clone, *args):
    return subprocess.run([sys.executable, os.path.join("tools", "parity.py"), *args], cwd=clone, capture_output=True, text=True)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Rebaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.clone = os.path.join(cls.tmp.name, "clone")
        subprocess.run(["git", "clone", "-q", "--local", ROOT, cls.clone], check=True)
        shutil.copy(os.path.join(HERE, "parity.py"), os.path.join(cls.clone, "tools", "parity.py"))  # the working copy, not the committed one
        cls.data = os.path.join(cls.clone, SKILL, "data")
        with gzip.open(os.path.join(cls.data, "papers.json.gz"), "rt", encoding="utf-8") as f:
            papers = json.load(f)
        papers[0]["title"] += " (edited)"  # a refresh: the bundled data now differs from the tag's
        with gzip.open(os.path.join(cls.data, "papers.json.gz"), "wt", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, separators=(",", ":"))
        cls.manifest = os.path.join(cls.clone, "tools", "parity_baseline.json")
        with open(cls.manifest, "rb") as f:
            cls.original = f.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        with open(self.manifest, "wb") as f:
            f.write(self.original)
        subprocess.run(["git", "checkout", "--", os.path.join(SKILL, "scripts", "search.py")], cwd=self.clone, check=True)

    def test_a_plain_record_still_refuses_changed_data(self):
        r = parity(self.clone, "record")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("rebaseline-data", r.stderr)
        with open(self.manifest, "rb") as f:
            self.assertEqual(f.read(), self.original, "a refused record must not touch the baseline")

    def test_check_refuses_until_the_data_is_rebaselined(self):
        r = parity(self.clone, "check")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("differs from the recorded baseline", r.stderr)

    def test_rebaseline_records_the_new_data_drops_the_other_pythons_and_check_then_passes(self):
        r = parity(self.clone, "record", "--rebaseline-data")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(self.manifest, encoding="utf-8") as f:
            m = json.load(f)
        self.assertEqual(m["data_sha256"], {f: sha(os.path.join(self.data, f)) for f in ("papers.json.gz", "institutions.json")})
        self.assertEqual(list(m["python"]), [PY], "results recorded for the old data under other Pythons are stale")
        r = parity(self.clone, "check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("22/22", r.stdout)

    def test_the_baseline_still_comes_from_the_frozen_engine_not_from_this_tree(self):
        self.assertEqual(parity(self.clone, "record", "--rebaseline-data").returncode, 0)
        engine = os.path.join(self.clone, SKILL, "scripts", "search.py")
        with open(engine, "a", encoding="utf-8") as f:
            f.write("\nraise SystemExit('broken')\n")  # a changed engine must now fail the parity check
        r = parity(self.clone, "check")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FAIL", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
