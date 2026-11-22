#!/usr/bin/env python3
"""Real recorded sounds with a clean licence, from Openverse (openverse.org, WordPress; API: api.openverse.org).

    python3 studio/openverse_audio.py search "temple bell" [--n 10] [--license cc0] [--max-s 20]
    python3 studio/openverse_audio.py get "temple bell" projects/<slug>/sfx/ [--n 3] [--license cc0] [--max-s 20]
    python3 studio/openverse_audio.py get --id <openverse id> projects/<slug>/sfx/
    python3 studio/openverse_audio.py verify projects/<slug>/sfx/      # before publishing: check each licence

Licences: cc0 and pdm (public domain) by default: free for any use, no credit needed (the studio keeps one anyway).
--license by also allows CC BY: the credit line is then REQUIRED wherever the film is posted (description) and the
CREDITS file says so. NC and ND licences are never fetched: the owner's videos are published, often monetised, and
edited. Mature results are skipped.

get writes, into the folder:
  <title-slug>_<id8>.<ext>   the recording as served (usually an MP3 preview of the original)
  sources.json                one row per file: id, title, creator, licence, licence URL, landing page, file URL, date
  CREDITS.md                  one human-readable line per file (title, creator, licence, link)
It never overwrites a file that is already there (it says so and skips it). Openverse's licence data can be wrong, so
every file starts UNVERIFIED: `verify` reads each source page and marks it verified, mismatch or unverified, and only
verified files go into a published film (exit 1 while any is not). Then use the file as a cue:
{"t": 2.4, "file": "projects/<slug>/sfx/temple-bell_5ef8351e.mp3", "gain": -8} in studio/sfx.py place.
Anonymous API use is rate-limited; 403/429 answers are retried with a short backoff. Standard library only.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
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


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _credits(sources: list[dict]) -> str:
    """CREDITS.md rebuilt from the manifest, so a credit can never go missing for a listed file."""
    head = ("# Sound credits\n\nFetched from Openverse. A licence marked UNVERIFIED comes only from Openverse's metadata, "
            "which can be wrong: run `python3 studio/openverse_audio.py verify <this folder>` and check the source page "
            "before the film is published.\n\n")
    lines = []
    for s in sources:
        r = {"title": s.get("title"), "creator": s.get("creator"), "license": s["license"],
             "license_version": s.get("license_version"), "foreign_landing_url": s.get("landing"), "url": s["url"]}
        state = {"verified": "verified on the source page", "mismatch": "LICENCE MISMATCH: do not use"}.get(
            s.get("verified"), "UNVERIFIED")
        lines.append(f"{credit_line(r)} [{s['file']}; {state}]")
    return head + "\n".join(lines) + ("\n" if lines else "")


@contextmanager
def _locked(out: Path):
    """One writer per folder: two `get` runs into the same project cannot overwrite each other's manifest."""
    out.mkdir(parents=True, exist_ok=True)
    with open(out / ".openverse.lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def _is_audio(path: Path) -> bool:
    if not shutil.which("ffprobe"):
        return path.stat().st_size > 1024  # no ffprobe here: at least refuse an empty or tiny error body
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return r.returncode == 0 and "audio" in r.stdout


def save(rows: list[dict], out: Path, want: int | None = None) -> list[Path]:
    """Download rows in order until `want` files are written (default: all rows). A file the host keeps refusing,
    or a body that is not audio, is skipped with a note and the next candidate is tried. Each file is downloaded to a
    temporary name, checked, and only then moved in and listed, under a folder lock, with the manifest and
    CREDITS.md replaced atomically."""
    written = []
    want = want or len(rows)
    with _locked(out):
        src_path = out / "sources.json"
        sources = json.loads(src_path.read_text(encoding="utf-8")) if src_path.exists() else []
        listed = {s["file"] for s in sources}
        for r in rows:
            if len(written) >= want:
                break
            # the served file is often a preview in another format than the original (filetype), so trust the URL
            ext = (Path(urllib.parse.urlparse(r["url"]).path).suffix.lstrip(".") or r.get("filetype") or "mp3").lower()
            f = out / f"{slug(r.get('title') or '')}_{r['id'][:8]}.{ext}"
            if f.exists():
                print(f"skip {f.name}: already there" + ("" if f.name in listed else
                      " but NOT in sources.json (an interrupted run?): credit it or delete it; it was not overwritten"))
                continue
            try:
                data = _get(r["url"])
            except urllib.error.HTTPError as e:
                print(f"skip {r['id'][:8]} ({r.get('title')}): the file host answered {e.code} after retries")
                continue
            tmp = out / (f.name + ".part")
            tmp.write_bytes(data)
            if not _is_audio(tmp):
                tmp.unlink()
                print(f"skip {r['id'][:8]} ({r.get('title')}): the download is not audio (an error page?)")
                continue
            os.replace(tmp, f)
            sources.append({"file": f.name, "id": r["id"], "title": r.get("title"), "creator": r.get("creator"),
                            "license": r["license"], "license_version": r.get("license_version"),
                            "license_url": r.get("license_url"), "landing": r.get("foreign_landing_url"),
                            "url": r["url"], "provider": r.get("provider"), "fetched": date.today().isoformat(),
                            "verified": None})
            _atomic_write(src_path, json.dumps(sources, ensure_ascii=False, indent=1) + "\n")
            _atomic_write(out / "CREDITS.md", _credits(sources))
            written.append(f)
    return written


CC_LINK = re.compile(r"creativecommons\.org/(licenses|publicdomain)/([a-z-]+)")


def licence_verdict(page: str, lic: str) -> str | None:
    """'verified', 'mismatch' or None, from the licence LINKS on a work's source page.

    Any link to a different Creative Commons licence, or the word "noncommercial", is a mismatch, even when the
    expected licence also appears somewhere (a page can show a filter or a footer link for CC0 while the work itself
    is BY-NC). With no licence link, plain text is not trusted: the result is None (unverified)."""
    page = (page or "").lower()
    if not page:
        return None
    want = {"cc0": {("publicdomain", "zero")}, "pdm": {("publicdomain", "mark")}, "by": {("licenses", "by")}}[lic]
    links = {(kind, code) for kind, code in CC_LINK.findall(page)}
    if links - want or "noncommercial" in page or "non-commercial" in page:
        return "mismatch"
    return "verified" if links & want else None


def verify(out: Path) -> list[dict]:
    """Check each listed file's licence on its source page and record the result in the manifest: verified,
    mismatch (the page shows another licence) or unverified (the page could not be read or shows no licence).
    The page text is evidence, not a legal opinion: the owner still decides."""
    with _locked(out):
        src_path = out / "sources.json"
        sources = json.loads(src_path.read_text(encoding="utf-8")) if src_path.exists() else []
        for s in sources:
            if s.get("verified") == "verified":
                continue
            try:
                page = _get(s["landing"]).decode("utf-8", "ignore").lower() if s.get("landing") else ""
            except (urllib.error.URLError, ValueError):
                page = ""
            s["verified"] = licence_verdict(page, s["license"])
            s["verified_on"] = date.today().isoformat()
        _atomic_write(src_path, json.dumps(sources, ensure_ascii=False, indent=1) + "\n")
        _atomic_write(out / "CREDITS.md", _credits(sources))
    return sources


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("q")
    g = sub.add_parser("get")
    g.add_argument("q", nargs="?")
    g.add_argument("out")
    g.add_argument("--id")
    v = sub.add_parser("verify")
    v.add_argument("out")
    for p in (s, g):
        p.add_argument("--n", type=int, default=3 if p is g else 10)
        p.add_argument("--license", default="cc0,pdm")
        p.add_argument("--max-s", type=float)
    a = ap.parse_args(argv)
    if a.cmd == "verify":
        rows = verify(Path(a.out))
        for r in rows:
            print(f"{r['file']}: {r['license']} {r.get('verified') or 'UNVERIFIED'}")
        bad = [r for r in rows if r.get("verified") != "verified"]
        return 1 if bad else 0
    if a.cmd == "search":
        for r in search(a.q, a.n, a.license, a.max_s):
            print(f"{r['id'][:8]}  {(r.get('duration') or 0) / 1000:6.1f}s  {r['license']:4s}  {(r.get('title') or '')[:50]}  ({r.get('creator')})")
        return 0
    if a.id:
        r = json.loads(_get(API + urllib.parse.quote(a.id) + "/"))
        rows = pick([r], 1, allowed(a.license), a.max_s)
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
