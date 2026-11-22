#!/usr/bin/env python3
"""Real recorded sounds with a clean licence, from Openverse (openverse.org, WordPress; API: api.openverse.org).

    python3 studio/openverse_audio.py search "temple bell" [--n 10] [--license cc0] [--max-s 20]
    python3 studio/openverse_audio.py get "temple bell" projects/<slug>/sfx/ [--n 3] [--license cc0] [--max-s 20]
    python3 studio/openverse_audio.py get --id <openverse id> projects/<slug>/sfx/

Licences: cc0 and pdm (public domain) by default: free for any use, no credit needed (the studio keeps one anyway).
--license by also allows CC BY: the credit line is then REQUIRED wherever the film is posted (description) and the
CREDITS file says so. NC and ND licences are never fetched: the owner's videos are published, often monetised, and
edited. Mature results are skipped.

get writes, into the folder:
  <title-slug>_<id8>.<ext>   the recording as served (usually an MP3 preview of the original)
  sources.json                one row per file: id, title, creator, licence, licence URL, landing page, file URL, date
  CREDITS.md                  one human-readable line per file (title, creator, licence, link)
It never overwrites a file that is already there (it says so and skips it). Then use the file as a cue:
{"t": 2.4, "file": "projects/<slug>/sfx/temple-bell_5ef8351e.mp3", "gain": -8} in studio/sfx.py place.
Anonymous API use is rate-limited; 403/429 answers are retried with a short backoff. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = "https://api.openverse.org/v1/audio/"
UA = "aifilm-studio/1.0 (https://github.com/manikk90/AI-film)"
SAFE = {"cc0", "pdm"}
WITH_CREDIT = {"by"}


def _get(url: str, tries: int = 6) -> bytes:
    delay = 2.0
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 502, 503) and k < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def allowed(licenses: str) -> set[str]:
    want = {x.strip().lower() for x in licenses.split(",") if x.strip()}
    bad = want - SAFE - WITH_CREDIT
    if bad:
        raise SystemExit(f"licence {', '.join(sorted(bad))} is not allowed here: only cc0, pdm and by "
                         "(NC/ND forbid monetised or edited use)")
    return want


def search(q: str, n: int = 10, licenses: str = "cc0,pdm", max_s: float | None = None) -> list[dict]:
    lic = allowed(licenses)
    params = {"q": q, "license": ",".join(sorted(lic)), "page_size": str(min(50, max(n * 3, 10))), "mature": "false"}
    data = json.loads(_get(API + "?" + urllib.parse.urlencode(params)))
    return pick(data.get("results", []), n, lic, max_s)


def pick(results: list[dict], n: int, lic: set[str], max_s: float | None = None) -> list[dict]:
    """Keep only rows we may use: allowed licence, not mature, has a file URL, within the length cap."""
    out = []
    for r in results:
        if r.get("license") not in lic or r.get("mature") or not r.get("url"):
            continue
        dur = (r.get("duration") or 0) / 1000
        if max_s and dur and dur > max_s:
            continue
        out.append(r)
        if len(out) == n:
            break
    return out


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "sound"


def credit_line(r: dict) -> str:
    lic = f"{r['license'].upper()} {r.get('license_version') or ''}".strip()
    need = " (credit REQUIRED where the film is posted)" if r["license"] in WITH_CREDIT else ""
    return f"- \"{r.get('title') or 'untitled'}\" by {r.get('creator') or 'unknown'}, {lic}{need}: {r.get('foreign_landing_url') or r['url']}"


def save(rows: list[dict], out: Path, want: int | None = None) -> list[Path]:
    """Download rows in order until `want` files are written (default: all rows). A file the CDN keeps refusing
    is skipped with a note, and the next candidate is tried."""
    out.mkdir(parents=True, exist_ok=True)
    src_path, cred_path = out / "sources.json", out / "CREDITS.md"
    sources = json.loads(src_path.read_text(encoding="utf-8")) if src_path.exists() else []
    written = []
    want = want or len(rows)
    for r in rows:
        if len(written) >= want:
            break
        # the served file is often a preview in another format than the original (filetype), so trust the URL
        ext = (Path(urllib.parse.urlparse(r["url"]).path).suffix.lstrip(".") or r.get("filetype") or "mp3").lower()
        f = out / f"{slug(r.get('title') or '')}_{r['id'][:8]}.{ext}"
        if f.exists():
            print(f"skip {f.name}: already there")
            continue
        try:
            data = _get(r["url"])
        except urllib.error.HTTPError as e:
            print(f"skip {r['id'][:8]} ({r.get('title')}): the file host answered {e.code} after retries")
            continue
        f.write_bytes(data)
        sources.append({"file": f.name, "id": r["id"], "title": r.get("title"), "creator": r.get("creator"),
                        "license": r["license"], "license_version": r.get("license_version"),
                        "license_url": r.get("license_url"), "landing": r.get("foreign_landing_url"),
                        "url": r["url"], "provider": r.get("provider"), "fetched": date.today().isoformat()})
        with open(cred_path, "a", encoding="utf-8") as c:
            c.write(credit_line(r) + "\n")
        written.append(f)
    src_path.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("q")
    g = sub.add_parser("get")
    g.add_argument("q", nargs="?")
    g.add_argument("out")
    g.add_argument("--id")
    for p in (s, g):
        p.add_argument("--n", type=int, default=3 if p is g else 10)
        p.add_argument("--license", default="cc0,pdm")
        p.add_argument("--max-s", type=float)
    a = ap.parse_args(argv)
    if a.cmd == "search":
        for r in search(a.q, a.n, a.license, a.max_s):
            print(f"{r['id'][:8]}  {(r.get('duration') or 0) / 1000:6.1f}s  {r['license']:4s}  {(r.get('title') or '')[:50]}  ({r.get('creator')})")
        return 0
    if a.id:
        r = json.loads(_get(API + urllib.parse.quote(a.id) + "/"))
        rows = pick([r], 1, allowed(a.license))
        if not rows:
            raise SystemExit(f"{a.id}: licence {r.get('license')} is not allowed (use --license by for CC BY)")
    elif a.q:
        rows = search(a.q, a.n * 3, a.license, a.max_s)  # spare candidates in case a file is refused
    else:
        raise SystemExit("get needs a query or --id")
    files = save(rows, Path(a.out), a.n)
    for f in files:
        print(f)
    if not files:
        raise SystemExit("no file could be fetched; try again in a minute, or another query")
    print(f"credits: {Path(a.out) / 'CREDITS.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
