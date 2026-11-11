# Installing conference-picks

The short version is under [Install](../README.md#install) in the README. This page has the other routes and the details.

## Claude

Add it once on the website or desktop app. It then belongs to your Claude account, so you can ask from the phone app too (the phone has not been tried yet). If you also use Claude Code with the same account, it shows up there by itself.

**Updates.** To get new versions as they come out, turn on **Sync automatically** for this marketplace in Customize → Plugins, or click **Check for updates** there now and then.

### No Plugins page? Upload the zip

A work account can turn the Plugins page off. Upload the skill as a file instead:

1. Download **[conference-picks.zip](https://github.com/ritwikvashistha/conference-picks/releases/latest/download/conference-picks.zip)**. Do not unzip it (see [About the zip files](#about-the-zip-files)).
2. Open **Customize → Skills**, click **+**, then **Create skill → Upload a skill**, and choose the zip.

An uploaded copy does not update itself: upload the new zip when a new version comes out.

**Sharing.** Each person adds their own copy. On Team and Enterprise plans you can share the skill with colleagues from its ••• menu in Customize → Skills.

## ChatGPT

ChatGPT has no way to add it by name yet, so the zip is the only route. On a work or school account, your administrator may have to allow uploads first.

OpenAI documents skills for Business, Enterprise, Healthcare and Edu plans; a Free account accepted the upload too. When ChatGPT loads the skill's instructions but cannot run its scripts, the skill tells it to ask for the zip, unzip it and run it from there. In a workspace, you can share the skill from its ••• menu; sharing stays inside the workspace. There is no custom GPT version: OpenAI retires custom GPTs on 2026-12-11.

## About the zip files

You never open or run a zip on your computer: you hand it to ChatGPT or Claude, which unpack it and run its scripts in their own sandbox. Each zip holds the skill's instructions, its Python scripts and the NeurIPS 2026 data, all readable in [plugins/conference-picks](../plugins/conference-picks). From version 0.3.5 on, GitHub builds both zips from that code for each release, not on anyone's own computer, and publishes a signed record of the build. Anyone with GitHub's command-line tool can check that a downloaded zip is the one GitHub built: `gh attestation verify conference-picks-chatgpt.zip --repo ritwikvashistha/conference-picks`.

## In a terminal

Claude Code and Codex run the skill on your own computer, which needs Python 3.9 or newer. Tested on macOS with Python 3.9, 3.10, 3.12 and 3.13; Windows and Linux are untested. After installing, start a new session and ask your question. You can also call it by name: `/conference-picks:conference-picks` in Claude Code, `$conference-picks` in Codex.

**Standalone skill in Claude Code:**

```bash
git clone https://github.com/ritwikvashistha/conference-picks
cp -r conference-picks/plugins/conference-picks/skills/conference-picks ~/.claude/skills/
```

**Standalone skill in Codex.** Codex looks in `~/.agents/skills/` (all projects) and in `.agents/skills/` from the project folder up to the repository root (that repository only):

```bash
git clone https://github.com/ritwikvashistha/conference-picks
mkdir -p ~/.agents/skills
cp -r conference-picks/plugins/conference-picks/skills/conference-picks ~/.agents/skills/
```

**Other agents:** untested. Point the agent at `plugins/conference-picks/skills/conference-picks/SKILL.md` and tell it to follow it.

## For maintainers

**Building the zips yourself:** `python3 tools/make_zip.py` writes both to `dist/`. `conference-picks.zip` is one `conference-picks/` folder with `SKILL.md` at its top, as Claude expects. `conference-picks-chatgpt.zip` holds the same skill laid out as the plugin archive ChatGPT asks for, with `.claude-plugin/plugin.json` and `skills/conference-picks/` at its root.

**Making a release:** raise `version` in `plugins/conference-picks/.claude-plugin/plugin.json`, then push a tag with that version, such as `v0.3.5`. The [release workflow](../.github/workflows/release.yml) refuses a tag that does not match, runs the tests with Python 3.9, builds both zips, signs a record of the build and puts the zips on a draft release; write the notes and publish it. Add marketplace (in Claude and in the terminal commands) installs from `main`, not from a release, so whatever is pushed to `main` reaches everyone who syncs: keep `main` working.
