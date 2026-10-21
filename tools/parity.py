#!/usr/bin/env python3
"""Parity test: the NeurIPS path of search.py must not change.

  python3 tools/parity.py record [--ref neurips-only-0.1.2]   run the frozen engine from git, store its output hashes for THIS Python
  python3 tools/parity.py check [--engine PATH] [--data DIR]  run the engine of this tree and compare with the stored hashes
  python3 tools/parity.py convert DIR                         write the bundled data as a --data dataset folder (use with check --data)

`find` orders tied matched terms by set order, so the hash seed must be real: PYTHONHASHSEED=0 is set and the engine is run
WITHOUT -I (-I ignores it). Hashes are stored per Python minor version, DTSTAMP is masked, and the bundled data files are
hashed too, so a changed dataset cannot pass as a parity result. Help text is not compared.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILL = os.path.join(ROOT, "plugins", "conference-picks", "skills", "conference-picks")
ENGINE = os.path.join(SKILL, "scripts", "search.py")
FIX = os.path.join(HERE, "fixtures")
MANIFEST = os.path.join(HERE, "parity_baseline.json")
REF_DIR = "plugins/neurips-picks/skills/neurips-picks"  # where the frozen skill lives at the baseline ref
DATA_FILES = ["papers.json.gz", "institutions.json"]
PY = "%d.%d" % sys.version_info[:2]
F = "{fix}/"
# ids: 148353 and 153320 are the maintainer's papers; 153871 has no session; 154534 is an oral; 155770 Paris; 139361 Atlanta;
# 137484 workshop; 137747 tutorial; 178419 invited talk
CASES = {
    "find_paper": [["find", "--paper", "148353"]],
    "find_two_papers_k60": [["find", "--paper", "148353", "--paper", "https://neurips.cc/virtual/2026/poster/153320", "-k", "60"]],
    "find_paper_brief": [["find", "--paper", "148353", "--text-file", F + "brief_fixture.txt"]],
    "find_text": [["find", "--text", "kernel two-sample test with maximum mean discrepancy", "-k", "40"]],
    "find_text_files": [["find", "--text-file", F + "brief_fixture.txt", "--text-file", F + "abstract_fixture.txt", "-k", "40"]],
    "find_profile": [["profile", "--titles-file", F + "titles.txt", "--save", "p.json"],
                     ["find", "--profile", "p.json", "--use", "1,2", "--exclude-name", "Ritwik Vashistha", "-k", "30"]],
    "profile_bibtex": [["profile", "--bibtex", F + "works.bib", "--save", "b.json"]],
    "show_batch": [["show", "148353,153320,137484,137747,178419", "--chars", "300"]],
    "show_no_abstract": [["show", "154534,139558,153871,155770,139361", "--no-abstract"]],
    "show_missing": [["show", "999999,148353", "--no-abstract"]],
    "who_name": [["who", "--name", "Arya Farahi"]],
    "who_name_affil": [["who", "--name", "farahi", "--affil", "UT Austin"]],
    "who_affil_ut": [["who", "--affil", "UT Austin"]],
    "who_affil_mit": [["who", "--affil", "MIT"]],
    "who_affil_regex": [["who", "--affil", "Fictional Lab"]],
    "who_none": [["who", "--name", "Zzzzz Qqqqq"]],
    "who_noargs_error": [["who"]],
    "find_noargs_error": [["find"]],
    "find_bad_paper_error": [["find", "--paper", "12"]],
    "ics": [["ics", "148353,153320,153871,154534,155770,139361"]],
    "csv": [["csv", "148353,153320,153871,154534,999999", "--reasons", F + "reasons_fixture.txt"]],
    "csv_no_reasons": [["csv", "139558,155770"]],
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_case(engine, name, extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env.update(PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    out = []
    with tempfile.TemporaryDirectory() as tmp:  # files such as p.json land here, not in the repo
        for args in CASES[name]:
            args = [a.replace("{fix}", FIX) for a in args]
            if extra and args[0] != "profile":
                args = args[:1] + extra + args[1:]
            r = subprocess.run([sys.executable, engine] + args, cwd=tmp, env=env, capture_output=True)
            stdout = re.sub(rb"DTSTAMP:\d{8}T\d{6}Z", b"DTSTAMP:MASKED", r.stdout)
            out.append({"rc": r.returncode, "stdout": sha(stdout), "stderr": sha(r.stderr), "bytes": len(stdout)})
    return out


def run_all(engine, extra):
    with cf.ThreadPoolExecutor(6) as ex:
        return dict(zip(CASES, ex.map(lambda n: run_case(engine, n, extra), CASES)))


def data_hashes(base=None):
    return {f: sha(open(os.path.join(base or os.path.join(SKILL, "data"), f), "rb").read()) for f in DATA_FILES}


def record(ref):
    ref_files = {}
    for f in DATA_FILES:
        ref_files[f] = sha(subprocess.run(["git", "-C", ROOT, "show", "%s:%s/data/%s" % (ref, REF_DIR, f)], capture_output=True, check=True).stdout)
    if ref_files != data_hashes():
        sys.exit("the bundled data differs from %s: re-baselining would hide a data change" % ref)
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "scripts"))
        engine = os.path.join(tmp, "scripts", "search.py")
        open(engine, "wb").write(subprocess.run(["git", "-C", ROOT, "show", "%s:%s/scripts/search.py" % (ref, REF_DIR)], capture_output=True, check=True).stdout)
        os.symlink(os.path.join(SKILL, "data"), os.path.join(tmp, "data"))  # same bytes as at the ref, checked above
        results = run_all(engine, [])
    m = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {"python": {}}
    m.update(ref=ref, data_sha256=ref_files)
    m["python"][PY] = results
    json.dump(m, open(MANIFEST, "w"), indent=1, sort_keys=True)
    print("recorded %d cases for Python %s from %s" % (len(results), PY, ref))


def check(engine, data):
    m = json.load(open(MANIFEST))
    if PY not in m["python"]:
        sys.exit("no baseline for Python %s: run `python%s tools/parity.py record` first" % (PY, PY))
    if m["data_sha256"] != data_hashes():
        sys.exit("the bundled data differs from the recorded baseline: parity is meaningless, check the data first")
    got = run_all(engine, ["--data", data] if data else [])
    bad = [n for n in CASES if got[n] != m["python"][PY][n]]
    for n in CASES:
        print("%-22s %s" % (n, "FAIL" if n in bad else "ok"))
        want = m["python"][PY][n]
        if n in bad and len(want) != len(got[n]):
            print("    number of commands differs")
        for i, (x, y) in enumerate(zip(want, got[n]) if n in bad else []):
            if x != y:
                print("    command %d differs in: %s" % (i + 1, ", ".join(k for k in x if x[k] != y[k])))
    print("%d/%d cases identical to the %s baseline (Python %s%s)" % (len(CASES) - len(bad), len(CASES), m["ref"], PY, ", --data " + data if data else ""))
    sys.exit(1 if bad else 0)


def convert(dst):
    os.makedirs(dst, exist_ok=True)
    for f in DATA_FILES:
        shutil.copy(os.path.join(SKILL, "data", f), dst)
    meta = {"name": "NeurIPS 2026", "slug": "neurips2026", "item": "poster", "paper_types": ["Poster"],
            "zones": {"Sydney": "Australia/Sydney", "Atlanta": "America/New_York", "Paris": "Europe/Paris"}}
    json.dump(meta, open(os.path.join(dst, "meta.json"), "w"), indent=1)
    print("wrote dataset folder", dst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record"); r.add_argument("--ref", default="neurips-only-0.1.2")
    c = sub.add_parser("check"); c.add_argument("--engine", default=ENGINE); c.add_argument("--data")
    v = sub.add_parser("convert"); v.add_argument("dir")
    a = ap.parse_args()
    {"record": lambda: record(a.ref), "check": lambda: check(a.engine, a.data), "convert": lambda: convert(a.dir)}[a.cmd]()
