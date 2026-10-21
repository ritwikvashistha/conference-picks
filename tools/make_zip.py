"""Build dist/conference-picks.zip for claude.ai (Settings > upload a skill): one folder, conference-picks/, with SKILL.md at its top.
Run from the repo root: python3 tools/make_zip.py
"""
import os, zipfile

SRC = "plugins/conference-picks/skills/conference-picks"
os.makedirs("dist", exist_ok=True)
with zipfile.ZipFile("dist/conference-picks.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f != ".DS_Store":
                z.write(os.path.join(root, f), os.path.join("conference-picks", os.path.relpath(os.path.join(root, f), SRC)))
    z.write("LICENSE", "conference-picks/LICENSE")
print("dist/conference-picks.zip", os.path.getsize("dist/conference-picks.zip") // 1000, "KB")
