#!/usr/bin/env python3
"""Check that every external URL in the catalog and events still resolves.

Run by hand (python linkcheck.py) or on a schedule in GitHub Actions. Exits non-zero
if any link fails so the workflow run shows red and emails the repository watchers.
Google/SharePoint links often answer 3xx or 401 to anonymous requests; those count as
alive. Only connection errors, 404 and 410 count as dead.
"""

import sys
import urllib.request
import urllib.error
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
DEAD = {404, 410}


def urls():
    seen = set()
    for path in sorted((ROOT / "catalog").glob("*.yaml")):
        for row in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            u = row.get("url")
            if u and u not in seen:
                seen.add(u)
                yield f"{path.name} / {row.get('slug')}", u
    for path in sorted((ROOT / "events").glob("*.yaml")):
        ev = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for key in ("evaluation_url", "short_link"):
            u = ev.get(key)
            if u and u not in seen:
                seen.add(u)
                yield f"{path.name} / {key}", u


def check(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "teaching-with-ai-va linkcheck"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return True, str(resp.status)
    except urllib.error.HTTPError as e:
        if e.code in DEAD:
            return False, str(e.code)
        return True, str(e.code)
    except Exception as e:  # noqa: BLE001
        return False, type(e).__name__


def main():
    bad = []
    for where, u in urls():
        ok, status = check(u)
        print(("ok  " if ok else "DEAD") + f"  {status:>6}  {where}\n            {u}")
        if not ok:
            bad.append((where, u, status))
    if bad:
        print(f"\n{len(bad)} dead link(s)", file=sys.stderr)
        sys.exit(1)
    print("\nAll links alive.")


if __name__ == "__main__":
    main()
