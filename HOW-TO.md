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

## Archiving a copy

We keep a copy of every document on this site whenever the original's permissions allow it, so links on a printed agenda still work years later even if a Drive folder, OneDrive account or external site goes away. The original stays the canonical version and keeps the credit; the copy is clearly labelled as a copy.

Put the file under `files/<strand>/` (PDF preferred; Word/PowerPoint also fine) and add an `archive` block to the card. The build refuses to publish a hosted file without one.

```yaml
- slug: assessment-security-resource-guide
  title: Assessment Security and AI Resource Guide
  ...
  url: https://myuva-my.sharepoint.com/...          # original; stays the canonical link
  file: files/assessment-security/assessment-security-resource-guide.pdf
  archive:
    cloned: 2026-11-03                              # the date the copy was taken
    source_url: https://myuva-my.sharepoint.com/... # optional if identical to url
    permission: Author permission (Matthew Pryal, 2026-11-03); free to use and adapt with attribution
    note: Exported from Word to PDF; content unchanged.   # optional
```

For material the workshop team wrote itself, where this repository *is* the home, use `original_here: true` instead of `source_url`:

```yaml
  archive:
    cloned: 2026-10-23
    original_here: true
    permission: Written by Paul Torrey for the workshop; free to use and adapt with attribution
```

What `permission` should say, by source:

| Source | Typical permission line |
| --- | --- |
| A team member's own document | `Author permission (Name, date); free to use and adapt with attribution` |
| VDOE standards and guides | `Public document of the Virginia Department of Education; mirrored unchanged` |
| GoOpenVA lesson plans | The license shown on the GoOpenVA page, usually `CC BY 4.0`, plus the author's name |
| Anything else | Ask first. If the license is unclear or "all rights reserved", link only (no `file`) |

The resource page shows the original link first, the archived copy second, and a provenance line; every archived file is also listed on `/attribution/`, generated automatically from these fields.

Rules of thumb: never edit a copied document (export to PDF is fine; changing content is not); if an original is updated, replace the file and bump `cloned`; if an author asks for a copy to be removed, delete the file and the `archive` block in the same commit and note it in `CHANGELOG.md`.

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
