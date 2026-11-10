"""Build the two upload zips. Run from the repo root: python3 tools/make_zip.py

  dist/conference-picks.zip           claude.ai (Settings > upload a skill): one folder, conference-picks/, with SKILL.md at its top
  dist/conference-picks-chatgpt.zip   ChatGPT (Plugins > Skills > Create > Upload from your computer): a plugin archive, with
                                      .claude-plugin/plugin.json and skills/conference-picks/SKILL.md at its root
"""
import os, zipfile

PLUGIN = "plugins/conference-picks"
SKILL = PLUGIN + "/skills/conference-picks"


def files(src):
    for root, dirs, names in os.walk(src):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(names):
            if f != ".DS_Store":
                yield os.path.join(root, f)


def build(path, src, prefix, extra=()):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files(src):
            z.write(f, os.path.join(prefix, os.path.relpath(f, src)))
        for f, name in extra:
            z.write(f, name)
    print(path, os.path.getsize(path) // 1000, "KB")


os.makedirs("dist", exist_ok=True)
build("dist/conference-picks.zip", SKILL, "conference-picks", [("LICENSE", "conference-picks/LICENSE")])
build("dist/conference-picks-chatgpt.zip", PLUGIN, "")  # the plugin folder holds its own LICENSE
