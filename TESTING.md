# Testing conference-picks

Thanks for testing. It takes about 30 minutes: run the skill on your own work, then rate the papers it picks. The ratings are what matter. Nobody can tell whether the picks are any good without people who know the field.

## 1. Run it

- Install it as described under "Install" in [README.md](README.md) (Claude, ChatGPT, Claude Code or Codex).
- Ask your agent, with your own NeurIPS 2026 paper id (if you have none, paste an abstract):

  > I'm going to NeurIPS 2026. My paper there is id <your paper id>. Which papers should I see?

- If it asks how much to read, choose Standard. Please skip profile mode for this test, so everyone is tested the same way.
- Read the list as you normally would.

## 2. Rate each pick

Rate every pick from 0 to 3, using the paper's title and abstract (open its link) and not the agent's one-line reason:

- 0 = unrelated
- 1 = same broad area, but no specific link to your paper's problem or method
- 2 = closely related topic, method or setting; you would likely want to read it
- 3 = directly relevant: the same problem or a very close variant, or a method your paper builds on or competes with; you would want to talk to its authors

Also mark `y` if you already knew the paper before today.

## 3. Anything missing?

List up to 3 NeurIPS 2026 papers you already know are closely related to your work and are not in the picks (id or title). "None" is fine. Please don't go searching for them.

## 4. Send it back

Send this to whoever gave you the link. One line per pick; the id is the number at the end of `neurips.cc/virtual/2026/poster/<id>`. Tabs or commas are both fine, and comments are optional.

```
tester: <initials>
agent: Claude Code / Codex / claude.ai / other (model if you know)
input: paper id / abstract
mode: Standard
install trouble: none / what went wrong
reasons accurate: yes / mostly / no
missing: <up to 3, or none>

id      rating (0-3)    knew it (y/n)    comment
```

If something breaks, send exactly what you typed and what you saw. That is as useful as the ratings. Please don't include unpublished abstracts or anything you don't want shared; paper ids are public.
