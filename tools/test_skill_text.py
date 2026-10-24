#!/usr/bin/env python3
"""Checks on the skill's text: the NeurIPS wording stays as it was, the new instructions exist, and their commands and example work.

Run: python3 tools/test_skill_text.py
"""
import csv, difflib, os, re, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILL = os.path.join(ROOT, "plugins", "conference-picks", "skills", "conference-picks")
SKILL_MD, OTHER, TEXT = os.path.join(SKILL, "SKILL.md"), os.path.join(SKILL, "OTHER_CONFERENCES.md"), os.path.join(SKILL, "TEXT_PROGRAMS.md")
BASELINE = "neurips-only-0.1.2:plugins/neurips-picks/skills/neurips-picks/SKILL.md"  # the shipped NeurIPS-only skill text
POINTER = "For another conference, or a dataset the user supplies, read `OTHER_CONFERENCES.md` in this folder first: it overrides the NeurIPS-specific parts below."
sys.path.insert(0, HERE)
import test_importer as ti  # its CSV fixture has the columns of a NeurIPS/ICML/ICLR "Downloads" file
import test_text_entries as tt  # its two synthetic programs are what the examples in TEXT_PROGRAMS.md are imported against


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def description():
    return re.search(r"^description: (.+)$", read(SKILL_MD), re.M).group(1)


class SkillText(unittest.TestCase):
    def baseline(self):
        r = subprocess.run(["git", "-C", ROOT, "show", BASELINE], capture_output=True, text=True)
        if r.returncode:
            self.skipTest("the tag neurips-only-0.1.2 is not in this clone")
        return r.stdout.replace("neurips-picks", "conference-picks")  # the rename is the only other difference

    def test_the_name_matches_the_folder_and_the_description_fits_claude_ai(self):
        self.assertEqual(re.search(r"^name: (.+)$", read(SKILL_MD), re.M).group(1), "conference-picks")
        self.assertLessEqual(len(description()), 1024)

    def test_the_description_names_neurips_and_other_conferences(self):
        self.assertIn("NeurIPS 2026", description())
        self.assertIn("another conference", description())

    def test_skill_md_differs_from_the_neurips_only_text_by_the_description_and_one_pointer(self):
        diff = list(difflib.unified_diff(self.baseline().splitlines(), read(SKILL_MD).splitlines(), lineterm="", n=0))
        removed = [x[1:] for x in diff if x.startswith("-") and not x.startswith("---")]
        added = [x[1:] for x in diff if x.startswith("+") and not x.startswith("+++")]
        self.assertEqual(len(removed), 1)
        self.assertTrue(removed[0].startswith("description:"))
        self.assertEqual([x for x in added if x.strip() and not x.startswith("description:")], [POINTER])

    def test_skill_md_grew_by_at_most_300_bytes(self):
        self.assertLessEqual(len(read(SKILL_MD).encode()) - len(self.baseline().encode()), 300)

    def test_the_pointer_file_exists_and_stays_short(self):
        self.assertTrue(os.path.isfile(OTHER), "OTHER_CONFERENCES.md is missing")
        self.assertLessEqual(len(read(OTHER).splitlines()), 55)

    def test_the_instructions_that_keep_an_agent_cheap_and_safe_are_there(self):
        text = read(OTHER).lower()
        for phrase in ("write no parsing script", "do not download", "show the user the report", "--data"):
            self.assertIn(phrase, text)

    def test_every_script_command_in_it_exists_with_the_options_it_uses(self):
        for doc, least in ((OTHER, 4), (TEXT, 2)):
            found = re.findall(r"scripts/(search|import_dataset)\.py (\w+)([^\n`]*)", read(doc))
            self.assertGreaterEqual(len(found), least, doc)
            for script, sub, rest in found:
                r = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", script + ".py"), sub, "-h"], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, "%s %s: %s" % (script, sub, r.stderr))
                for option in re.findall(r"(?<![\w-])(--[a-z][a-z-]*)", rest):
                    self.assertIn(option, r.stdout, "%s %s has no %s" % (script, sub, option))

    def test_the_example_mapping_imports_a_template_csv(self):
        block = re.search(r"```json\n(.*?)\n```", read(OTHER), re.S)
        self.assertTrue(block, "no json block in OTHER_CONFERENCES.md")
        with tempfile.TemporaryDirectory() as d:
            src, out = os.path.join(d, "events.csv"), os.path.join(d, "out")
            rows = ti.csv_rows()
            with open(src, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader(); w.writerows(rows)
            with open(os.path.join(d, "map.json"), "w") as f:
                f.write(block.group(1))
            r = ti.sh(ti.IMPORTER, "import", src, "--mapping", os.path.join(d, "map.json"), "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("records: 63", r.stdout)

    def test_the_text_programs_file_exists_stays_short_and_keeps_the_book_out_of_the_chat(self):
        self.assertTrue(os.path.isfile(TEXT), "TEXT_PROGRAMS.md is missing")
        self.assertLessEqual(len(read(TEXT).splitlines()), 45)
        text = read(TEXT).lower()
        for phrase in ("by path", "never read", "pdftotext -layout", "never install", "inspect", "day_overrides", "write no parsing script",
                       "file-reading tool", "end_before", "exact room values", "the `text:` line"):
            self.assertIn(phrase, text)

    def test_every_json_block_in_it_imports_a_synthetic_program(self):
        blocks = re.findall(r"```json\n(.*?)\n```", read(TEXT), re.S)
        self.assertGreaterEqual(len(blocks), 2, "one example per layout")
        for block in blocks:
            layout = "a" if "Presenter" in block else "b"
            with tempfile.TemporaryDirectory() as d:
                with open(os.path.join(d, "book.txt"), "w", encoding="utf-8", newline="\n") as f:
                    f.write(tt.Program(layout).text)
                with open(os.path.join(d, "map.json"), "w", encoding="utf-8") as f:
                    f.write(block)
                r = ti.sh(ti.IMPORTER, "import", os.path.join(d, "book.txt"), "--mapping", os.path.join(d, "map.json"), "--out", os.path.join(d, "out"))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("text: 60 entries", r.stdout)

    def test_the_pointer_in_other_conferences_and_the_readme_cover_pdf_programs(self):
        self.assertIn("TEXT_PROGRAMS.md", read(OTHER))
        readme = read(os.path.join(ROOT, "README.md"))
        for phrase in ("pdftotext", "TEXT_PROGRAMS.md", "estimate"):
            self.assertIn(phrase, readme)

    def test_data_notice_says_other_conferences_stay_on_the_users_machine(self):
        self.assertIn("~/.conference-picks", read(os.path.join(SKILL, "DATA_NOTICE.md")))

    def test_every_relative_link_in_the_readme_exists(self):
        for target in re.findall(r"\]\(([^)#\s]+)\)", read(os.path.join(ROOT, "README.md"))):
            if not target.startswith(("http://", "https://", "mailto:")):
                self.assertTrue(os.path.exists(os.path.join(ROOT, target)), "README links to a missing file: " + target)

    def test_the_readme_explains_other_conferences(self):
        self.assertIn("Other conferences", read(os.path.join(ROOT, "README.md")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
