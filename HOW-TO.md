# Adding content

The site is generated from a handful of plain-text files in this repository. You never edit HTML. Add a row, push, and GitHub rebuilds the site in about a minute.

## Add a resource

Open the catalog file for its topic (`catalog/assessment-security.yaml`, `catalog/differentiation.yaml`, `catalog/data-visualization.yaml`, `catalog/planning-investigations.yaml`) and add a card:

```yaml
- slug: my-new-worksheet            # lowercase-with-dashes, never changes once published
  title: Photosynthesis data worksheet
  type: worksheet                   # slides · worksheet · guide · prompt · lesson-plan · demo · reading
  strand: data-visualization        # must match a strand slug in site.yaml
  url: https://docs.google.com/document/d/.../copy
  access: make-a-copy               # view · make-a-copy · download · external
  summary: One or two sentences teachers will read on the card.
  sol: [BIO.3, LS.5]                # optional; codes exactly as VDOE prints them
  grade_band: HS                    # MS · HS · both
  audience: teacher                 # teacher · facilitator · both (facilitator items stay off public pages)
  author: Your Name
  updated: 2027-02-01
  start_here: false                 # true puts it in the "Start here" group on the topic page
  related: [another-slug]           # optional "Pairs with" links
```

For a **prompt**, leave out `url` and add the text instead:

```yaml
  prompt_text: |
    I teach high-school biology. Make me ...
  tips: Any set-up (files to upload first) and reflection questions.
```

To host a file in the repository (a PDF handout, say), put it under `files/` and set `file: files/my-handout.pdf`; the card shows a download button alongside any `url`.

Rules the build enforces (it refuses to publish otherwise): every slug unique and kebab-case; `make-a-copy` links end in `/copy`; SOL codes use a known prefix (LS, BIO, EC, GEN, BIOII); `related` slugs exist; prompts have `prompt_text`.

If you tag a standard that is not yet in `standards.yaml` under `statements:`, add its one-line text there so the crosswalk can show it.

## Add a workshop

1. Copy `events/2026-10.yaml` to `events/<yyyy-mm>.yaml` and edit the date, venue, speakers, schedule and rotations. Each rotation lists the slugs of the resources it uses. Reused resources need nothing new; their cards' "Used in" lists grow automatically.
2. Put the agenda PDF at `files/agenda-<yyyy-mm>.pdf` and set `agenda_file`.
3. Push. The new workshop becomes the one shown on the home page (the newest date wins), and the previous one moves to the Workshops list.
4. Re-point **bit.ly/AIAFTERNOON** at `/workshops/<yyyy-mm>/`. Never re-point bit.ly/BIORESOURCES.
5. After the event, add links to the evaluation results and takeaways under `facilitator:` in the event file, and add a line to `CHANGELOG.md`.

## Add a topic (strand)

Add an entry under `strands:` in `site.yaml` (slug, name, short, lead, summary) and create `catalog/<slug>.yaml`. Give it a color by adding `--c-<slug>` in `static/style.css` if you want the tile and headings tinted.

## Build locally

```
pip install -r requirements.txt
python build.py --check     # validate only
python build.py             # writes _site/
python -m http.server -d _site 8000
```

## Where things live

| What | Where |
| --- | --- |
| Site settings, strands, sponsors | `site.yaml` |
| SOL courses and standard text | `standards.yaml` |
| Resource cards | `catalog/*.yaml` |
| Workshops | `events/*.yaml` |
| Hosted files (PDFs, VDOE guide mirrors) | `files/` |
| Page templates | `templates/` |
| Styles | `static/style.css` |
| This page | `HOW-TO.md` |
| Changelog | `CHANGELOG.md` |
