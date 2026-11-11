# conference-picks

**Going to an academic conference (e.g. NeurIPS 2026)? Find the papers and people closest to your own work and network faster.**

[Install](#install) · [Use it](#use-it) · [How it works](#how-it-works) · [Other conferences](#other-conferences) · [More details](docs/details.md)

A skill for Claude and ChatGPT. Give it your NeurIPS 2026 paper, your name, an abstract or your past papers. It returns 15 to 25 papers worth seeing, each with a one-line reason, sorted by site (Sydney, Atlanta, Paris), session and local time, plus the people worth meeting. It runs in your own Claude or ChatGPT account: no sign-ups, no API keys.

The NeurIPS 2026 program inside is a snapshot taken on 2026-11-04 and 2026-11-05, so check neurips.cc for the official schedule. Other conferences work from a paper list you bring ([see below](#other-conferences)).

## Install

| You use | Plan | What you do |
| --- | --- | --- |
| **Claude**: website, desktop app or phone | Free or paid | [Add it by name](#claude), nothing to download |
| **ChatGPT**: website or app | Free or paid | [Upload one file](#chatgpt) |
| **Claude Code** or **Codex** | Claude Pro or above, or a ChatGPT plan with Codex | [Paste two commands](#claude-code-or-codex) |

Both chat routes were tested on Free accounts. Other routes, updates and sharing: [docs/install.md](docs/install.md).

### Claude

1. Open **Settings → Capabilities** and turn on **Code execution and file creation** (newer versions call it **Create and edit files**).
2. Open **Customize → Plugins**, click **Add**, then **Add marketplace**, and type `ritwikvashistha/conference-picks`.
3. **conference-picks** now appears among the plugins. Open it and click **Add**.
4. Start a new chat and ask your question.

No Plugins page? [Upload the zip instead](docs/install.md#no-plugins-page-upload-the-zip).

### ChatGPT

1. Download **[conference-picks-chatgpt.zip](https://github.com/ritwikvashistha/conference-picks/releases/latest/download/conference-picks-chatgpt.zip)** and keep it zipped ([what is in it?](docs/install.md#about-the-zip-files)).
2. Click **Plugins** in the sidebar, open **Skills**, click **Create**, then **Upload from your computer**, and choose the zip.
3. Start a new chat, type **@conference-picks** and ask your question.
4. If ChatGPT says it cannot open the skill's files, drag the same zip into the chat.

### Claude Code or Codex

Needs Python 3.9 or newer.

```bash
claude plugin marketplace add ritwikvashistha/conference-picks
claude plugin install conference-picks@conference-picks
```

```bash
codex plugin marketplace add ritwikvashistha/conference-picks
codex plugin add conference-picks@conference-picks
```

## Use it

Ask in plain words:

> I'm going to NeurIPS 2026. My paper there is id 148353. Which papers should I see?

The start of a real answer to that question (Claude Code, Standard budget; [full answer](docs/example-answer-neurips.md)):

> Your paper, [Noisy2Latent: Nonparametric Deconvolution and Denoising via Maximum Mean Discrepancy](https://neurips.cc/virtual/2026/poster/148353) (148353), is presented at **Sydney Tue 2026-12-08 10:00**.
>
> **Sydney Tue 2026-12-08 10:00**
>
> - **#5** [Bridging the Simulation-to-Experiment Gap with Adversarial Distribution Alignment](https://neurips.cc/virtual/2026/poster/151598): Kai Nelson, Tobias Kreiman, Sergey Levine, Aditi Krishnapriyan. They align a generative model with experimental data that only partly observe the system's state, so the model is fitted through an observation process. You do the same when you match the observed data to the noise-convolved model. **Same slot as your poster.**
>
> **Sydney Thu 2026-12-10 10:00**
>
> - **#1** [Empirical Bayes Flow Matching for Continuous Cryo-EM Heterogeneity](https://neurips.cc/virtual/2026/poster/151539): Daniel Aibinder, Azmi Haider, Dan Rosenbaum. They learn a flow-matching prior over latent variables directly from indirect, noisy observations (cryo-EM projections), inside a Monte Carlo EM framework. Your paper has the same goal: learn the latent distribution from noisy data and use it as a prior. Theirs takes a likelihood-based EM route with a non-linear forward operator, where yours uses a likelihood-free convMMD loss under additive noise.
>
> *... 18 more picks in Sydney, Atlanta and Paris, then the authors worth talking to.*

Your paper's id is the number at the end of its page, `neurips.cc/virtual/2026/poster/<id>`. Instead, you can give:

- your name ("My name is First Last") or a pasted abstract;
- **all your work**: a BibTeX file exported from Google Scholar, your paper titles, or your ORCID. It groups your papers into up to three areas and asks which to focus on ([how](docs/details.md#all-your-work)). A Scholar link alone will not work.

If it asks how much to read, choose **Standard** ([what each costs](docs/details.md#reading-budgets)). Afterwards, ask for "a calendar file" or "a spreadsheet" of the picks.

## Other conferences

NeurIPS 2026 is built in. For any other conference, give it the paper list. It reads the file, shows you what it found (the number of papers and three samples) and waits for your OK before it searches.

- **A CSV or JSON file** with title, authors and abstract. Conferences on the same website software as NeurIPS, such as ICML and ICLR, offer one on their Downloads page (for example `icml.cc/Downloads/2026`: choose csv, press **Download Data**).

  > I'm going to ICML 2026. Its paper list is `~/Downloads/ICML 2026 Events.csv`. My abstract is: ...

- **A PDF book of abstracts**, for conferences that publish only that ([which layouts work](docs/other-conferences.md#a-pdf-or-text-book-of-abstracts)). On your own computer this needs `pdftotext` (on a Mac, `brew install poppler`); the skill tells you if it is missing.

  > I'm going to ISBA 2026. Its program is `~/Downloads/isba2026_program.pdf`. My abstract is: ...

The start of the real ICML answer ([full answer](docs/example-answer-icml.md); the [ISBA answer](docs/example-answer-isba.md) groups its picks by day and time):

> These picks are from ICML 2026: your file `ICML 2026 Events.csv`, imported on 2026-11-11 as dataset `icml2026`. [...]
>
> - **#1 [Provable Bounds for the Learnability of Sample-Compressible Families from Noisy Samples](https://ICML.cc/virtual/2026/poster/62572)**: Arefe Boushehrian, Amir Najafi. It asks when a family of distributions on R^d can be learned at all, and with how many samples, when the samples are noisy (the noise appears in the title; the part I read covers sample complexity). This is the learning-theory side of your finite-sample bounds for recovering a latent density from noisy data.
>
> *... 18 more ranked picks, then the people worth talking to.*

ICML's file has no session times, so its picks are ranked only. In Claude Code or Codex the imported list is kept for later questions; in a chat, attach the file again in a new chat. Details and test status: [docs/other-conferences.md](docs/other-conferences.md).

## How it works

Steps marked *model* are done by the AI you run it in (Claude, ChatGPT, Codex) and use tokens. The *script* steps run on your computer or in the chat's own sandbox, cost nothing and send nothing anywhere.

```text
  You: a NeurIPS paper id, your name or an abstract
       (or all your work: BibTeX, titles, ORCID *)
                        |
                        v
  +------------------------------------------+
  | 1  BRIEF                           model |
  | ~25 short phrases: other names for       |
  | your ideas, neighbouring fields          |
  +------------------------------------------+
                        |
                        v
  +------------------------------------------+
  | 2  SEARCH                script, offline |
  | search.py scores the 9,145 posters       |
  | with an abstract by word overlap with    |
  | your abstract and the brief              |
  | -> 150 candidates                        |
  +------------------------------------------+
                        |
                        v
  +------------------------------------------+
  | 3  JUDGE                           model |
  | reads the promising ones (Standard:      |
  | about 30 abstracts), keeps 15 to 25,     |
  | one reason each                          |
  +------------------------------------------+
                        |
                        v
  +------------------------------------------+
  | 4  PLAN                   model + script |
  | the model groups the picks by site >     |
  | session > local time and names up to     |
  | 8 people to meet; scripts make the       |
  | calendar or spreadsheet if you ask       |
  +------------------------------------------+

  * All your work: the profile command reads your
    BibTeX file or titles, or fetches your works by
    ORCID. Looking up works and abstracts on
    OpenAlex and ORCID is the only step that goes
    online. The model groups your works into up to
    3 areas, and steps 1 to 3 run once per area.
```

Word overlap cannot tell a strong match from a shared buzzword, so the brief adds other names for your ideas and the model judges the 150 candidates instead of trusting their order. On six test papers, Standard picked 56 of the 94 papers an LLM judge rated closely related, against 34 for the word search alone ([how it was measured](docs/details.md#how-well-does-it-work), and the [limits](docs/details.md#limits)).

## Privacy

The search sends nothing anywhere. Only reading all your work goes online: it sends the name, ORCID or titles you give it to OpenAlex and ORCID. What you type goes to your AI provider, as with any chat ([more](docs/details.md#privacy)).

## Licence, data and contact

MIT, see [LICENSE](LICENSE). The bundled NeurIPS 2026 data is public program data; see [DATA_NOTICE.md](plugins/conference-picks/skills/conference-picks/DATA_NOTICE.md) for its sources and how to ask for a correction or removal. Contact: ritwikvashistha@gmail.com, [ritwikvashistha.github.io](https://ritwikvashistha.github.io/)
