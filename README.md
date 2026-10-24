# Teaching in the Age of AI — resource hub

The website behind **bit.ly/BIORESOURCES**: prompts, worksheets, lesson plans and guides from the
*Teaching in the Age of AI* teacher workshop series (University of Virginia), organized by topic and
by Virginia Standard of Learning. Each workshop has its own subject title; the first was
*Teaching Life Sciences in the Age of AI* (October 24, 2026).

Live site: https://teaching-with-ai-va.github.io

## How it works

Everything is generated from plain-text files; no HTML is edited by hand.

| Input | Contents |
| --- | --- |
| `site.yaml` | Title, short links, organizers, sponsors, and the list of topics (strands) |
| `standards.yaml` | The SOL courses we tag against and the one-line text of each standard |
| `catalog/*.yaml` | Resource cards, one file per topic |
| `events/*.yaml` | One file per workshop (agenda, speakers, rotations and the cards each used) |
| `files/` | Files hosted on the site: agenda PDFs, handouts, VDOE instructional-guide mirrors |

`build.py` validates the inputs (unique slugs, known strands and SOL prefixes, `/copy` links for
make-a-copy items, every slug an event names exists) and renders the site into `_site/`.
A GitHub Actions workflow runs it on every push to `main` and deploys to GitHub Pages; pull
requests build and validate without deploying. A weekly job checks that every external link still
resolves.

See **HOW-TO.md** (also published at `/facilitators/how-to/`) for adding a resource, a workshop
or a topic.

## Local build

```
pip install -r requirements.txt
python build.py --check
python build.py
python -m http.server -d _site 8000
```

## One-time setup on GitHub

In the repository settings, under **Pages**, set *Source* to **GitHub Actions**. The first push to
`main` after that publishes the site.
