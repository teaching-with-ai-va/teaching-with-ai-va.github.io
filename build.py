#!/usr/bin/env python3
"""Build the Teaching Life Sciences in the Age of AI resource hub.

Inputs (all plain text, all in this repository):
  site.yaml            site-wide settings and the list of strands
  standards.yaml       the SOL courses we cover (code prefix, name, grade band, links)
  catalog/*.yaml       resource cards, one list per file (one file per strand)
  events/*.yaml        one file per workshop
  CHANGELOG.md         dated log, rendered on the facilitator changelog page
  HOW-TO.md            the extension recipe, rendered on the facilitator how-to page

Output: a static site in _site/ (configurable with --out).

Usage:
  python build.py            # build
  python build.py --check    # validate only, no output
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown

ROOT = Path(__file__).resolve().parent

TYPES = {
    "slides": "Slides",
    "worksheet": "Worksheet",
    "guide": "Guide",
    "prompt": "Prompt",
    "lesson-plan": "Lesson plan",
    "demo": "Demo",
    "standard": "Standards",
    "reading": "Reading",
}
# Order in which groups appear on a strand page.
TYPE_ORDER = ["prompt", "lesson-plan", "worksheet", "demo", "slides", "guide", "reading", "standard"]
ACCESS = {
    "view": "View",
    "make-a-copy": "Make a copy",
    "download": "Download",
    "external": "External site",
}
ACCESS_HINT = {
    "view": "Opens a read-only document",
    "make-a-copy": "Google will offer to copy this into your own Drive",
    "download": "Downloads a file",
    "external": "Leaves this site",
}
GRADE_BANDS = {"MS": "Middle school", "HS": "High school", "both": "Middle & high school"}
AUDIENCES = {"teacher", "facilitator", "both"}
REQUIRED = ["slug", "title", "type", "strand", "access"]
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class BuildError(Exception):
    pass


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {} if data is None else data


def load_inputs():
    site = load_yaml(ROOT / "site.yaml")
    standards = load_yaml(ROOT / "standards.yaml")
    catalog = []
    for path in sorted((ROOT / "catalog").glob("*.yaml")):
        rows = load_yaml(path)
        if rows is None:
            continue
        if not isinstance(rows, list):
            raise BuildError(f"{path.name}: expected a list of cards")
        for row in rows:
            row["_file"] = path.name
            catalog.append(row)
    events = []
    for path in sorted((ROOT / "events").glob("*.yaml")):
        ev = load_yaml(path)
        ev["_file"] = path.name
        ev["slug"] = path.stem
        events.append(ev)
    events.sort(key=lambda e: str(e["date"]), reverse=True)
    return site, standards, catalog, events


def validate(site, standards, catalog, events):
    errors = []
    strands = {s["slug"]: s for s in site["strands"]}
    strands["general"] = {"slug": "general", "name": "General"}
    prefixes = {c["prefix"] for c in standards["courses"]}
    code_re = re.compile(r"^(" + "|".join(re.escape(p) for p in prefixes) + r")\.\d+$")
    slugs = {}

    for row in catalog:
        where = f"{row['_file']} / {row.get('slug', '?')}"
        for field in REQUIRED:
            if not row.get(field):
                errors.append(f"{where}: missing required field '{field}'")
        slug = row.get("slug", "")
        if slug and not SLUG_RE.match(slug):
            errors.append(f"{where}: slug must be lowercase kebab-case")
        if slug in slugs:
            errors.append(f"{where}: duplicate slug (also in {slugs[slug]})")
        slugs[slug] = row["_file"]
        if row.get("type") not in TYPES:
            errors.append(f"{where}: unknown type '{row.get('type')}' (one of {', '.join(TYPES)})")
        if row.get("strand") not in strands:
            errors.append(f"{where}: unknown strand '{row.get('strand')}'")
        if row.get("access") not in ACCESS:
            errors.append(f"{where}: unknown access '{row.get('access')}'")
        if row.get("type") == "prompt":
            if not row.get("prompt_text"):
                errors.append(f"{where}: a prompt needs prompt_text")
        elif not row.get("url") and not row.get("file"):
            errors.append(f"{where}: needs a url or a file")
        if row.get("access") == "make-a-copy" and row.get("url") and not row["url"].rstrip("/").endswith("/copy"):
            errors.append(f"{where}: make-a-copy links must end in /copy")
        if row.get("file") and not (ROOT / row["file"]).exists():
            errors.append(f"{where}: file not found: {row['file']}")
        # Any file hosted here must say where it came from and on what terms.
        if row.get("file"):
            arc = row.get("archive") or {}
            for field in ("cloned", "permission"):
                if not arc.get(field):
                    errors.append(f"{where}: a hosted file needs archive.{field} (see HOW-TO: Archiving a copy)")
            if arc.get("cloned") and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(arc["cloned"])):
                errors.append(f"{where}: archive.cloned must be a YYYY-MM-DD date")
            if not arc.get("source_url") and not row.get("url") and not arc.get("original_here"):
                errors.append(f"{where}: archive needs source_url (or original_here: true if this repo is the original)")
        for code in row.get("sol", []) or []:
            if not code_re.match(str(code)):
                errors.append(f"{where}: SOL code '{code}' does not match a known course prefix")
        gb = row.get("grade_band")
        if gb and gb not in GRADE_BANDS:
            errors.append(f"{where}: grade_band must be one of {', '.join(GRADE_BANDS)}")
        aud = row.get("audience", "teacher")
        if aud not in AUDIENCES:
            errors.append(f"{where}: audience must be one of {', '.join(sorted(AUDIENCES))}")
        for rel in row.get("related", []) or []:
            if rel not in {r.get("slug") for r in catalog}:
                errors.append(f"{where}: related slug '{rel}' not in catalog")

    for ev in events:
        where = ev["_file"]
        if not re.match(r"^\d{4}-\d{2}$", ev["slug"]):
            errors.append(f"{where}: event files are named yyyy-mm.yaml")
        for field in ("date", "title"):
            if not ev.get(field):
                errors.append(f"{where}: missing '{field}'")
        for rot in ev.get("rotations", []) or []:
            if rot.get("strand") not in strands:
                errors.append(f"{where}: rotation strand '{rot.get('strand')}' unknown")
            for s in rot.get("resources", []) or []:
                if s not in slugs:
                    errors.append(f"{where}: rotation '{rot.get('strand')}' names unknown slug '{s}'")

    if errors:
        raise BuildError("\n".join(errors))


def enrich(site, standards, catalog, events):
    """Attach derived fields the templates use."""
    by_slug = {r["slug"]: r for r in catalog}
    strands = {s["slug"]: s for s in site["strands"]}
    courses = {c["prefix"]: c for c in standards["courses"]}

    for r in catalog:
        r.setdefault("audience", "teacher")
        r.setdefault("sol", [])
        r.setdefault("related", [])
        r["type_label"] = TYPES[r["type"]]
        r["access_label"] = ACCESS[r["access"]]
        r["access_hint"] = ACCESS_HINT[r["access"]]
        r["grade_label"] = GRADE_BANDS.get(r.get("grade_band"), "")
        r["strand_obj"] = strands.get(r["strand"], {"slug": "general", "name": "General"})
        r["href"] = r.get("url") or (f"/{r['file']}" if r.get("file") else None)
        r["file_href"] = f"/{r['file']}" if r.get("file") else None
        r["file_ext"] = Path(r["file"]).suffix.lstrip(".").upper() if r.get("file") else ""
        arc = r.get("archive") or {}
        if r.get("file"):
            r["archive"] = {
                "source_url": arc.get("source_url") or (None if arc.get("original_here") else r.get("url")),
                "cloned": str(arc.get("cloned", "")),
                "permission": arc.get("permission", ""),
                "note": arc.get("note", ""),
                "original_here": bool(arc.get("original_here")),
            }
        else:
            r["archive"] = None
        r["used_in"] = []
        r["related_objs"] = [by_slug[s] for s in r["related"] if s in by_slug]
        r["sol_objs"] = []
        for code in r["sol"]:
            prefix, _, num = str(code).partition(".")
            c = courses[prefix]
            text = (standards.get("statements", {}) or {}).get(code, "")
            r["sol_objs"].append({"code": code, "course": c, "text": text})

    for ev in events:
        ev["date_obj"] = ev["date"] if isinstance(ev["date"], date) else date.fromisoformat(str(ev["date"]))
        ev["date_label"] = ev["date_obj"].strftime("%B %-d, %Y")
        ev["short_label"] = ev["date_obj"].strftime("%b %Y")
        for rot in ev.get("rotations", []) or []:
            rot["strand_obj"] = strands[rot["strand"]]
            rot["resource_objs"] = [by_slug[s] for s in rot.get("resources", []) or []]
            for res in rot["resource_objs"]:
                res["used_in"].append(ev)

    # Strand -> items grouped by type (teacher-facing only)
    for s in site["strands"]:
        items = [r for r in catalog if r["strand"] == s["slug"] and r["audience"] != "facilitator"]
        s["start_here"] = [r for r in items if r.get("start_here")]
        groups = defaultdict(list)
        for r in items:
            groups[r["type"]].append(r)
        s["groups"] = [(TYPES[t], groups[t]) for t in TYPE_ORDER if groups.get(t)]
        s["count"] = len(items)
        s["facilitator_items"] = [r for r in catalog if r["strand"] == s["slug"] and r["audience"] in ("facilitator", "both")]
        s["events"] = [ev for ev in events if any(rot["strand"] == s["slug"] for rot in ev.get("rotations", []) or [])]

    # Crosswalk: course -> code -> resources
    crosswalk = []
    statements = standards.get("statements", {}) or {}
    for c in standards["courses"]:
        codes = defaultdict(list)
        for r in catalog:
            if r["audience"] == "facilitator":
                continue
            for code in r["sol"]:
                if str(code).split(".")[0] == c["prefix"]:
                    codes[code].append(r)
        rows = []
        for code in sorted(codes, key=lambda k: int(k.split(".")[1])):
            rows.append({"code": code, "text": statements.get(code, ""), "resources": codes[code]})
        crosswalk.append({"course": c, "rows": rows})

    prompts = [r for r in catalog if r["type"] == "prompt" and r["audience"] != "facilitator"]

    # Attribution register: every file hosted on this site, with its provenance.
    archived = []
    for r in catalog:
        if r["archive"]:
            archived.append({"title": r["title"], "href": r["file_href"], "ext": r["file_ext"], "page": f"/resources/{r['slug']}/",
                             "author": r.get("author", ""), **r["archive"]})
    for c in standards["courses"]:
        if c.get("guide_file"):
            arc = c.get("archive") or {}
            archived.append({"title": f"{c['name']} instructional guide", "href": f"/{c['guide_file']}", "ext": Path(c["guide_file"]).suffix.lstrip(".").upper(),
                             "page": "/standards/", "author": "Virginia Department of Education",
                             "source_url": arc.get("source_url") or standards.get("vdoe_url"), "cloned": str(arc.get("cloned", "")),
                             "permission": arc.get("permission", ""), "note": arc.get("note", ""), "original_here": False})
    for ev in events:
        if ev.get("agenda_file"):
            archived.append({"title": f"Agenda, {ev['date_label']}", "href": f"/{ev['agenda_file']}", "ext": Path(ev["agenda_file"]).suffix.lstrip(".").upper(),
                             "page": f"/workshops/{ev['slug']}/", "author": "Workshop organizers", "source_url": None,
                             "cloned": str(ev.get("date", "")), "permission": "Produced by the workshop team", "note": "", "original_here": True})
    archived.sort(key=lambda a: a["title"].lower())
    return {"by_slug": by_slug, "crosswalk": crosswalk, "prompts": prompts, "archived": archived}


def render_markdown_file(path: Path) -> str:
    if not path.exists():
        return ""
    return markdown.markdown(path.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])


def build(out: Path, check_only: bool = False):
    site, standards, catalog, events = load_inputs()
    validate(site, standards, catalog, events)
    derived = enrich(site, standards, catalog, events)
    if check_only:
        print(f"OK: {len(catalog)} cards, {len(events)} events, {len(derived['prompts'])} prompts")
        return

    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["md"] = lambda s: markdown.markdown(s or "")
    ctx = {
        "site": site,
        "strands": site["strands"],
        "standards": standards,
        "catalog": catalog,
        "events": events,
        "current": events[0] if events else None,
        "built": date.today().isoformat(),
        "today": date.today(),
        **derived,
    }

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    def write(rel: str, template: str, **extra):
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        html = env.get_template(template).render(**ctx, **extra)
        dest.write_text(html, encoding="utf-8")

    write("index.html", "home.html")
    for s in site["strands"]:
        write(f"strands/{s['slug']}/index.html", "strand.html", strand=s)
    for r in catalog:
        write(f"resources/{r['slug']}/index.html", "resource.html", r=r)
    write("prompts/index.html", "prompts.html")
    write("standards/index.html", "standards.html")
    write("attribution/index.html", "attribution.html")
    write("workshops/index.html", "workshops.html")
    for ev in events:
        write(f"workshops/{ev['slug']}/index.html", "event.html", ev=ev)
    write("facilitators/index.html", "facilitators.html")
    for s in site["strands"]:
        write(f"facilitators/{s['slug']}/index.html", "facilitator_strand.html", strand=s)
    write("facilitators/how-to/index.html", "page.html", title="Adding content", body=render_markdown_file(ROOT / "HOW-TO.md"))
    write("facilitators/changelog/index.html", "page.html", title="Changelog", body=render_markdown_file(ROOT / "CHANGELOG.md"))
    write("404.html", "404.html")

    shutil.copytree(ROOT / "static", out / "static")
    if (ROOT / "files").exists():
        shutil.copytree(ROOT / "files", out / "files")
    (out / ".nojekyll").write_text("")
    print(f"Built {len(catalog)} cards, {len(events)} events into {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    ap.add_argument("--check", action="store_true", help="validate inputs without writing output")
    args = ap.parse_args()
    try:
        build(ROOT / args.out, check_only=args.check)
    except BuildError as e:
        print("Build refused:\n" + str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
