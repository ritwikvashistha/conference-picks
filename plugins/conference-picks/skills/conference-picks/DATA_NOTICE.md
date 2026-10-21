# Data notice

`conference-picks` ships a snapshot of public NeurIPS 2026 program data so that it can run offline on your own machine. This page says what is in it, where it came from, and how to ask for a correction or removal.

## What is included

For each of the 9,245 NeurIPS 2026 events (9,111 posters, plus workshops, tutorials and invited talks):

- title, author names with the affiliations given on the NeurIPS site, and abstract
- the link to the paper's official NeurIPS page
- for posters, the site (Sydney, Atlanta or Paris), session, hall, and local start and end time
- an oral flag
- a canonical institution name for each affiliation, produced by our own matching rules (`data/institutions.json`)

Not included: paper PDFs or full texts, reviews, discussions, email addresses, or any private data.

## Where it came from

- The event list was downloaded from the NeurIPS 2026 Downloads page on neurips.cc on 2026-10-17.
- Sessions, halls and times for posters missing from the official orals-and-posters file were read from each paper's public page on neurips.cc, one page at a time, slowly (roughly one page per second or two), with a plain user agent, from paths that robots.txt allows.
- The canonical institution names and the merged schedule fields are our own work and may contain mistakes.

## Why we think reuse is fine

- Our reading of neurips.cc is that its pages state no licence or terms for this data either way, and that NeurIPS itself offers the event list for download.
- NeurIPS 2026 papers are handled through OpenReview. Its Terms of Use (https://openreview.net/legal/terms) define a work's metadata to include its title, authors and abstract, and dedicate that metadata to the public domain under CC0 1.0, to the extent anyone holds a copyright interest in it.
- Authors keep the copyright in their papers (https://neurips.cc/FAQ/Copyright). This repository does not contain papers, only the metadata above, and every record links back to the official page.
- This is our own summary of public terms, checked on 2026-10-20. It is not legal advice and it can go out of date.

## Personal data

Author names and affiliations are shown publicly on neurips.cc and are repeated here as published. If you are listed and want a record corrected or removed from future releases, tell us and we will do it:

Contact: ritwikvashistha@gmail.com

## Accuracy and freshness

- This is a snapshot from 2026-10-17, with schedule details read on 2026-10-18 to 2026-10-20. Sessions and times can change, and poster board numbers were not published when we collected the data. Check neurips.cc for the official schedule.
- Institution names are merged heuristically. Some institutions may be split across spellings or merged by mistake; reports are welcome.
- This project is independent. It is not affiliated with, or endorsed by, NeurIPS or OpenReview. "NeurIPS" is used only to say which conference the data is about.

## Other conferences

`conference-picks` ships no data for any other conference. If you import a paper list yourself, the dataset stays on your machine, in `~/.conference-picks/`, under the terms of the source you got it from. The importer makes no network calls and records the source and its checksum in the dataset's `meta.json`.

## Licence

The code and our derived tables (the institution mapping and the merged schedule fields) are released under the MIT License; see `LICENSE`. We claim no rights in the underlying NeurIPS and OpenReview metadata.
