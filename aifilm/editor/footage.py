"""Archive and stock footage for edits that need real shots the owner did not film.

Search adapters (written against each service's public API; they run wherever the host is
reachable: the owner's laptop, or this cloud session once the host is allowed):
  - internet-archive : archive.org films that carry a licence URL (public domain / Creative Commons)
  - wikimedia-commons: Commons videos with their licence metadata
  - nasa             : NASA Image and Video Library (free with NASA's media guidelines)
  - pexels           : Pexels videos (needs PEXELS_API_KEY; Pexels licence)
Any other site, such as movingimagearchive.com, goes through `add` (a file the owner downloaded or
licensed) or `fetch` with a direct link, with the licence stated by the owner.

Every external clip gets a provenance record in <edit>/footage.json. The render refuses clips
whose rights are unknown, no-derivatives, or non-commercial without the owner's say-so, and
writes renders/CREDITS.md with every attribution the licences require.
"""

import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from ..core import ProductionError, file_hash, now, project_lock, read_json, require, write_json

UA = "Mann-AI-film-editor/1.0 (footage search)"
MEDIA_EXT = (".mp4", ".mov", ".m4v", ".webm", ".ogv", ".mpg", ".mpeg", ".mkv")
RIGHTS = {
    "public-domain": "Public domain / CC0: free to edit and publish; credit is courtesy.",
    "cc-by": "Creative Commons Attribution: free to edit and publish with credit.",
    "cc-by-sa": "Attribution-ShareAlike: credit required; the edited film may have to carry the same licence.",
    "cc-by-nc": "NonCommercial: only for non-commercial videos (needs the owner's say-so).",
    "nd": "NoDerivatives: editing is not allowed. Refused.",
    "free-license": "Free licence with conditions (Pexels licence, NASA media guidelines): read the conditions in the record.",
    "owner-licensed": "The owner holds a licence (paid archive such as movingimagearchive.com): licence reference required.",
    "unknown": "Rights unknown: not usable until the owner confirms the licence.",
}


def classify(text):
    """Rights category from a licence name or URL."""
    t = (text or "").lower()
    if not t:
        return "unknown"
    if "-nd" in t or "noderiv" in t or "/nd/" in t or "by-nc-nd" in t or "by-nd" in t:
        return "nd"
    if "publicdomain" in t or "public domain" in t or "cc0" in t or "pdm" in t or "pd-" in t:
        return "public-domain"
    if "nc" in re.split(r"[^a-z]+", t) or "-nc" in t or "noncommercial" in t or "by-nc" in t:
        return "cc-by-nc"
    if "by-sa" in t or "sharealike" in t:
        return "cc-by-sa"
    if "creativecommons.org/licenses/by" in t or re.search(r"\bcc[ -]by\b", t):
        return "cc-by"
    return "unknown"


def http_json(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=dict({"User-Agent": UA}, **(headers or {})))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as exc:  # network policy, DNS, HTTP error
        host = urllib.parse.urlparse(url).netloc
        raise ProductionError("Could not reach {} ({}). In the cloud session this host may need to be allowed in the "
                              "network settings; on the laptop check the connection.".format(host, str(exc)[:120])) from exc


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


# ---- adapters -------------------------------------------------------------------

def search_internet_archive(query, limit):
    q = "({}) AND mediatype:movies AND licenseurl:*".format(query)
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        [("q", q), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "licenseurl"), ("fl[]", "year"), ("fl[]", "creator"),
         ("rows", str(limit)), ("output", "json")])
    out = []
    for d in http_json(url).get("response", {}).get("docs", []):
        lic = d.get("licenseurl", "")
        creator = d.get("creator")
        creator = ", ".join(creator) if isinstance(creator, list) else (creator or "Internet Archive")
        out.append({"source": "internet-archive", "id": d["identifier"], "title": d.get("title", d["identifier"]),
                    "page": "https://archive.org/details/" + d["identifier"], "download": None, "license": lic,
                    "rights": classify(lic), "credit": "{} ({}), via Internet Archive".format(creator, d.get("year", "n.d.")), "year": d.get("year")})
    return out


def internet_archive_file(identifier):
    """Best H.264 MP4 of an Internet Archive item (smallest MPEG4 derivative)."""
    meta = http_json("https://archive.org/metadata/" + urllib.parse.quote(identifier))
    files = [f for f in meta.get("files", []) if f.get("name", "").lower().endswith(".mp4")]
    require(files, "No MP4 file in archive.org item " + identifier)
    best = min(files, key=lambda f: int(f.get("size", 10 ** 12)))
    return "https://archive.org/download/{}/{}".format(identifier, urllib.parse.quote(best["name"]))


def search_wikimedia_commons(query, limit):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "generator": "search", "gsrsearch": "filetype:video " + query, "gsrnamespace": "6", "gsrlimit": str(limit),
         "prop": "imageinfo", "iiprop": "url|extmetadata|mime|size", "format": "json"})
    pages = (http_json(url).get("query") or {}).get("pages", {})
    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = (meta.get("LicenseShortName") or {}).get("value", "") + " " + (meta.get("LicenseUrl") or {}).get("value", "")
        artist = strip_html((meta.get("Artist") or {}).get("value", "")) or "Wikimedia Commons contributor"
        out.append({"source": "wikimedia-commons", "id": p.get("title", ""), "title": p.get("title", "").replace("File:", ""),
                    "page": info.get("descriptionurl"), "download": info.get("url"), "license": lic.strip(), "rights": classify(lic),
                    "credit": "{} / {}, via Wikimedia Commons".format(artist, (meta.get("LicenseShortName") or {}).get("value", "licence"))})
    return out


def search_nasa(query, limit):
    url = "https://images-api.nasa.gov/search?" + urllib.parse.urlencode({"q": query, "media_type": "video"})
    out = []
    for item in http_json(url).get("collection", {}).get("items", [])[:limit]:
        d = (item.get("data") or [{}])[0]
        out.append({"source": "nasa", "id": d.get("nasa_id"), "title": d.get("title", d.get("nasa_id")),
                    "page": "https://images.nasa.gov/details/" + urllib.parse.quote(d.get("nasa_id", "")), "download": None,
                    "assets": item.get("href"), "license": "NASA media usage guidelines", "rights": "free-license",
                    "conditions": "No NASA endorsement implied; NASA logos/insignia restricted; check the item for third-party rights.",
                    "credit": "NASA{}".format(" / " + d["center"] if d.get("center") else "")})
    return out


def nasa_file(assets_url):
    files = http_json(assets_url)
    mp4 = [f for f in files if isinstance(f, str) and f.lower().endswith(".mp4")]
    require(mp4, "No MP4 in the NASA asset list")
    for pref in ("~medium.mp4", "~orig.mp4", "~large.mp4"):
        for f in mp4:
            if f.endswith(pref):
                return f.replace("http://", "https://")
    return mp4[0].replace("http://", "https://")


def search_pexels(query, limit):
    key = os.environ.get("PEXELS_API_KEY")
    require(key, "Pexels needs PEXELS_API_KEY in the environment (never in chat or files)")
    url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode({"query": query, "per_page": str(limit)})
    out = []
    for v in http_json(url, {"Authorization": key}).get("videos", []):
        files = sorted([f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"],
                       key=lambda f: abs((f.get("height") or 0) - 1920))
        out.append({"source": "pexels", "id": str(v.get("id")), "title": v.get("url", "").rstrip("/").split("/")[-1],
                    "page": v.get("url"), "download": files[0]["link"] if files else None, "license": "Pexels License",
                    "rights": "free-license", "conditions": "Pexels licence: free to use and edit; do not sell unaltered copies; "
                    "identifiable people must not be shown in a bad light.", "credit": "{} via Pexels".format((v.get("user") or {}).get("name", "Pexels")),
                    "duration": v.get("duration")})
    return out


ADAPTERS = {"internet-archive": search_internet_archive, "wikimedia-commons": search_wikimedia_commons,
            "nasa": search_nasa, "pexels": search_pexels}


def search(query, sources=None, limit=8):
    """Search the free sources; each result carries its licence and rights category.
    A source that cannot be reached is reported, not fatal."""
    results, errors = [], {}
    for name in sources or ["internet-archive", "wikimedia-commons", "nasa"] + (["pexels"] if os.environ.get("PEXELS_API_KEY") else []):
        require(name in ADAPTERS, "Unknown footage source {!r}; choose from {}".format(name, sorted(ADAPTERS)))
        try:
            results += ADAPTERS[name](query, limit)
        except ProductionError as exc:
            errors[name] = str(exc)
    for r in results:
        r["usable"] = r["rights"] in ("public-domain", "cc-by", "cc-by-sa", "free-license")
        r["rights_note"] = RIGHTS[r["rights"]]
    return {"query": query, "results": results, "errors": errors}


# ---- provenance -----------------------------------------------------------------

def check_rights(rights, licence_ref=None, noncommercial_ok=False):
    require(rights in RIGHTS, "rights must be one of {}".format(sorted(RIGHTS)))
    require(rights != "nd", "No-derivatives licence: editing the clip is not allowed, so Mann cannot use it")
    require(rights != "unknown", "Rights unknown: confirm the licence with the owner and pass --rights/--license")
    require(rights != "cc-by-nc" or noncommercial_ok, "Non-commercial licence: only usable when the owner confirms this video is "
                                                      "non-commercial (pass --noncommercial-ok with their words)")
    require(rights != "owner-licensed" or (licence_ref or "").strip(), "Owner-licensed footage needs the licence reference "
                                                                        "(order/invoice/licence id) in --licence-ref")


def register(root, rel, entry):
    path = Path(root) / "footage.json"
    log = read_json(path) if path.exists() else {"clips": {}}
    log["clips"][rel] = entry
    write_json(path, log)
    return entry


def add(edit_root, file, source_url, license_text, credit, rights=None, licence_ref=None, noncommercial_ok=False, notes=None, link=False):
    """Bring in a clip the owner downloaded or licensed (any site, e.g. movingimagearchive.com)."""
    from . import media
    root = Path(edit_root)
    f = Path(file)
    require(f.is_file(), "Missing file " + str(f))
    rights = rights or classify(license_text)
    check_rights(rights, licence_ref, noncommercial_ok)
    require((credit or "").strip(), "Give the credit line (who made the footage, where it is from)")
    with project_lock(root):
        dest = root / "raw" / "archive"
        dest.mkdir(parents=True, exist_ok=True)
        target = dest / re.sub(r"[^A-Za-z0-9._-]+", "_", f.name)
        if not target.exists():
            target.symlink_to(f.resolve()) if link else shutil.copy2(f, target)
        info = media.probe(target)
        require(info["has_video"], "Not a video file: " + f.name)
        rel = str(target.relative_to(root))
        entry = {"file": rel, "source_url": source_url, "license": license_text, "rights": rights, "credit": credit.strip(),
                 "licence_ref": licence_ref, "noncommercial_ok": bool(noncommercial_ok), "notes": notes,
                 "sha256": file_hash(target), "duration": round(info["duration"], 2), "added": now()}
        return register(root, rel, entry)


def download(url, dest):
    """Direct media links are streamed; page links go through yt-dlp."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if urllib.parse.urlparse(url).path.lower().endswith(MEDIA_EXT):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as out:
                shutil.copyfileobj(r, out)
        except Exception as exc:
            dest.unlink(missing_ok=True)
            raise ProductionError("Download failed for {} ({}); the host may need to be allowed".format(
                urllib.parse.urlparse(url).netloc, str(exc)[:120])) from exc
        return dest
    require(shutil.which("yt-dlp") is not None, "yt-dlp is needed for page links; run editor/install.sh")
    result = subprocess.run(["yt-dlp", "--no-playlist", "-f", "bv*[height<=1080]+ba/b[height<=1080]/b", "--merge-output-format", "mp4",
                             "-o", str(dest.with_suffix(".%(ext)s")), "--print", "after_move:filepath", url],
                            capture_output=True, text=True, timeout=3600)
    require(result.returncode == 0, "yt-dlp could not download {}: {}".format(url, result.stderr.strip()[-300:]))
    return Path(result.stdout.strip().splitlines()[-1])


def fetch(edit_root, result=None, url=None, license_text=None, credit=None, rights=None, licence_ref=None, noncommercial_ok=False):
    """Download a search result (or a direct/page URL with an owner-stated licence) into the edit."""
    root = Path(edit_root)
    if result:
        rights = rights or result["rights"]
        license_text = license_text or result.get("license")
        credit = credit or result.get("credit")
        url = result.get("download")
        if not url and result["source"] == "internet-archive":
            url = internet_archive_file(result["id"])
        if not url and result["source"] == "nasa":
            url = nasa_file(result["assets"])
        page = result.get("page")
        notes = result.get("conditions")
        name = "{}-{}".format(result["source"], re.sub(r"[^A-Za-z0-9_-]+", "_", str(result["id"]))[:60])
    else:
        require(url, "Give a URL or a search result")
        page, notes = url, None
        name = "link-" + re.sub(r"[^A-Za-z0-9_-]+", "_", urllib.parse.urlparse(url).path.rsplit("/", 1)[-1] or "clip")[:60]
    rights = rights or classify(license_text)
    check_rights(rights, licence_ref, noncommercial_ok)
    tmp = root / ".footage-download" / (name + ".mp4")
    got = download(url, tmp)
    try:
        return add(root, got, page, license_text, credit, rights, licence_ref, noncommercial_ok, notes)
    finally:
        shutil.rmtree(root / ".footage-download", ignore_errors=True)


def used_files(edl):
    files = set(edl["sources"].values())
    files |= {o["file"] for o in edl.get("overlays", [])}
    if edl.get("audio", {}).get("music"):
        files.add(edl["audio"]["music"]["file"])
    return files


def gate(root, edl):
    """Refuse a render that uses archive footage without an accepted licence; return the records used."""
    root = Path(root)
    log = read_json(root / "footage.json")["clips"] if (root / "footage.json").exists() else {}
    used = []
    for rel in sorted(used_files(edl)):
        rec = log.get(rel)
        if rel.startswith("raw/archive/"):
            require(rec is not None, "{} is archive footage without a provenance record; add it with `footage add` "
                                     "(source, licence, credit)".format(rel))
        if rec:
            check_rights(rec["rights"], rec.get("licence_ref"), rec.get("noncommercial_ok"))
            require(file_hash(root / rel) == rec["sha256"], "{} changed after its licence was recorded; add it again".format(rel))
            used.append(rec)
    return used


def credits(root, edl, out=None):
    """CREDITS.md for the archive footage the edit uses (attribution lines and licence conditions)."""
    used = gate(root, edl)
    if not used:
        return None
    lines = ["# Footage credits", ""]
    for r in used:
        lines.append("- {} — {} ({}){}".format(r["credit"], r["license"] or r["rights"], r["source_url"] or "owner's file",
                                               "; licence ref {}".format(r["licence_ref"]) if r.get("licence_ref") else ""))
    notes = sorted({r["notes"] for r in used if r.get("notes")})
    sa = any(r["rights"] == "cc-by-sa" for r in used)
    if notes or sa:
        lines += ["", "## Conditions", ""] + ["- " + n for n in notes]
        if sa:
            lines.append("- ShareAlike footage is used: the published film may need to carry the same Creative Commons licence.")
    text = "\n".join(lines) + "\n"
    out = Path(out or (Path(root) / "renders" / "CREDITS.md"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return str(out)


__all__ = ["search", "fetch", "add", "gate", "credits", "classify", "RIGHTS"]
