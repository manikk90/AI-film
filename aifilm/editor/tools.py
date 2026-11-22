"""External open-source tools Mann drives: FFmpeg, Whisper (faster-whisper or openai-whisper),
yt-dlp and Hyperframes. Each wrapper fails with a plain reason instead of faking output."""

import importlib.util
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

from ..core import ProductionError, now, require, write_json
from .edl import tc

HYPERFRAMES = "hyperframes@0.8.230"
GSAP_CDN = re.compile(r"https://cdn\.jsdelivr\.net/npm/gsap@([0-9.]+)/dist/gsap\.min\.js")


def version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        text = (out.stdout or out.stderr).strip().splitlines()
        return text[0][:80] if out.returncode == 0 and text else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def doctor():
    has = lambda m: importlib.util.find_spec(m) is not None
    report = {
        "ffmpeg": version(["ffmpeg", "-version"]),
        "ffprobe": version(["ffprobe", "-version"]),
        "yt-dlp": version(["yt-dlp", "--version"]),
        "whisper": "faster-whisper" if has("faster_whisper") else ("openai-whisper" if has("whisper") else None),
        "node": version(["node", "--version"]),
        "hyperframes": version(["hyperframes", "--version"]) or (version(["npx", "--no-install", "hyperframes", "--version"]) if shutil.which("npx") else None),
        "fc-match": bool(shutil.which("fc-match")),
        "fonttools": has("fontTools"),
        "opencv_faces": __import__("aifilm.editor.reframe", fromlist=["available"]).available(),
    }
    node = report["node"] or ""
    m = re.match(r"v(\d+)", node)
    report["node_ok_for_hyperframes"] = bool(m and int(m.group(1)) >= 22)
    report["ready_core"] = bool(report["ffmpeg"] and report["ffprobe"])
    report["missing"] = [k for k in ("ffmpeg", "ffprobe", "yt-dlp", "whisper", "node", "hyperframes") if not report[k]]
    return report


def fetch(url, dest, max_height=1080):
    """Download a reference video with yt-dlp for style study (owner's responsibility: rights to use it)."""
    require(shutil.which("yt-dlp") is not None, "yt-dlp is not installed; run editor/install.sh")
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    cmd = ["yt-dlp", "--no-playlist", "-f", "bv*[height<={0}]+ba/b[height<={0}]/b".format(max_height),
           "--merge-output-format", "mp4", "--write-info-json", "--restrict-filenames",
           "-o", str(dest / "%(extractor)s-%(id)s.%(ext)s"), "--print", "after_move:filepath", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        tail = "\n".join(result.stderr.strip().splitlines()[-4:])
        raise ProductionError("yt-dlp could not download {}:\n{}\n(If this is a cloud session, the site may be blocked by the network policy.)".format(url, tail))
    path = result.stdout.strip().splitlines()[-1]
    write_json(Path(path).with_suffix(".source.json"), {"url": url, "fetched": now(), "file": Path(path).name,
                                                        "use": "reference study only; not for re-upload"})
    return path


def srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "{:02d}:{:02d}:{:02d},{:03d}".format(h, m, s, ms)


def write_srt(segments, path, max_words=None):
    """segments: [{start, end, text, words?}]. With max_words, split into short phone captions using word timings."""
    cues = []
    for seg in segments:
        words = seg.get("words") or []
        if max_words and words:
            for i in range(0, len(words), max_words):
                chunk = words[i:i + max_words]
                cues.append((chunk[0]["start"], chunk[-1]["end"], " ".join(w["word"].strip() for w in chunk)))
        else:
            cues.append((seg["start"], seg["end"], seg["text"].strip()))
    body = "\n".join("{}\n{} --> {}\n{}\n".format(i, srt_time(a), srt_time(b), t) for i, (a, b, t) in enumerate(cues, 1))
    Path(path).write_text(body, encoding="utf-8")
    return len(cues)


def transcribe(media_path, out_dir, model="small", language=None, max_words=4):
    """Transcribe with faster-whisper (preferred) or openai-whisper. Writes <stem>.json, <stem>.srt
    (full lines) and <stem>.captions.srt (max_words per cue, for burned-in phone captions)."""
    media_path, out_dir = Path(media_path), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    segments = []
    try:
        if importlib.util.find_spec("faster_whisper"):
            from faster_whisper import WhisperModel
            engine = "faster-whisper"
            wm = WhisperModel(model, device="auto", compute_type="int8")
            segs, info = wm.transcribe(str(media_path), language=language, word_timestamps=True, vad_filter=True)
            for s in segs:
                segments.append({"start": s.start, "end": s.end, "text": s.text,
                                 "words": [{"start": w.start, "end": w.end, "word": w.word} for w in (s.words or [])]})
            lang = info.language
        elif importlib.util.find_spec("whisper"):
            import whisper
            engine = "openai-whisper"
            result = whisper.load_model(model).transcribe(str(media_path), language=language, word_timestamps=True)
            segments = [{"start": s["start"], "end": s["end"], "text": s["text"], "words": s.get("words", [])} for s in result["segments"]]
            lang = result.get("language")
        else:
            raise ProductionError("No Whisper engine installed; run editor/install.sh")
    except ProductionError:
        raise
    except Exception as exc:  # model download blocked, bad file, out of memory
        raise ProductionError("Whisper could not run ({}: {}). If the model download was refused, allow huggingface.co "
                              "(faster-whisper) or openaipublic.azureedge.net (openai-whisper) in the network settings, or run "
                              "on a machine that has the model cached.".format(type(exc).__name__, str(exc)[:200])) from exc
    stem = media_path.stem
    write_json(out_dir / (stem + ".json"), {"engine": engine, "model": model, "language": lang, "segments": segments, "created": now()})
    write_srt(segments, out_dir / (stem + ".srt"))
    n = write_srt(segments, out_dir / (stem + ".captions.srt"), max_words=max_words)
    return {"engine": engine, "language": lang, "segments": len(segments), "caption_cues": n,
            "files": [str(out_dir / (stem + x)) for x in (".json", ".srt", ".captions.srt")]}


def vendor_gsap(project):
    """Hyperframes' blank template loads GSAP from a CDN that some networks block. Copy the same
    GSAP version from the npm registry into vendor/ and point the composition at it."""
    project = Path(project)
    for html in project.rglob("*.html"):
        text = html.read_text(encoding="utf-8")
        m = GSAP_CDN.search(text)
        if not m:
            continue
        target = project / "vendor" / "gsap.min.js"
        if not target.exists():
            with tempfile.TemporaryDirectory() as tmp:
                packed = subprocess.run(["npm", "pack", "gsap@" + m.group(1), "--silent"], cwd=tmp, capture_output=True, text=True, timeout=300)
                require(packed.returncode == 0, "npm pack gsap failed; leaving the CDN link in place")
                with tarfile.open(Path(tmp) / packed.stdout.strip().splitlines()[-1]) as tar:
                    member = tar.getmember("package/dist/gsap.min.js")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(member).read())
        rel = Path("vendor/gsap.min.js") if html.parent == project else Path("../" * len(html.parent.relative_to(project).parts)) / "vendor/gsap.min.js"
        html.write_text(GSAP_CDN.sub(rel.as_posix(), text), encoding="utf-8")


def hyperframes_cmd():
    return ["hyperframes"] if shutil.which("hyperframes") else ["npx", "--yes", HYPERFRAMES]


def mg_new(edit_root, name, resolution="portrait"):
    """Scaffold a Hyperframes motion-graphics composition at <edit>/mg/<name>/."""
    dest = Path(edit_root) / "mg"
    dest.mkdir(parents=True, exist_ok=True)
    require(not (dest / name).exists(), "mg/{} already exists".format(name))
    env = dict(__import__("os").environ, HYPERFRAMES_SKIP_SKILLS="1")
    result = subprocess.run(hyperframes_cmd() + ["init", name, "--example", "blank", "--non-interactive", "--resolution", resolution],
                            cwd=dest, capture_output=True, text=True, timeout=600, env=env)
    require(result.returncode == 0, "hyperframes init failed: " + (result.stderr or result.stdout)[-400:])
    vendor_gsap(dest / name)
    apply_design(edit_root, dest / name)
    return str(dest / name)


def apply_design(edit_root, project):
    """Put the EDL's colour theme and font pairing into the composition's :root tokens."""
    edl_path = Path(edit_root) / "edl.json"
    if not edl_path.exists():
        return
    from ..core import read_json
    from . import craft
    typo = (read_json(edl_path).get("typography") or {})
    html = Path(project) / "index.html"
    text = html.read_text(encoding="utf-8")
    if typo.get("theme"):
        colours = craft.theme(typo["theme"])["colours"]
        text = text.replace("--ground: #000;", "--ground: {};".format(colours[0])).replace("--ink: #ffffff;", "--ink: {};".format(colours[3]))
        text = text.replace(":root {", ":root {\n        --accent: " + colours[-1] + ";", 1)
    if typo.get("pairing"):
        p = craft.pairing(typo["pairing"])
        text = text.replace("--font-display: sans-serif;", "--font-display: '{}', sans-serif;\n        --font-text: '{}', sans-serif;".format(p["display"], p["text"]))
    html.write_text(text, encoding="utf-8")


def mg_render(edit_root, name, alpha=True):
    """Render mg/<name> to mg/<name>.mov (ProRes 4444 with alpha) or .mp4, ready for an EDL overlay."""
    project = Path(edit_root) / "mg" / name
    require((project / "index.html").exists(), "No Hyperframes composition at " + str(project))
    vendor_gsap(project)
    out = project.parent / (name + (".mov" if alpha else ".mp4"))
    cmd = hyperframes_cmd() + ["render", "-o", str(out.resolve()), "--quiet"] + (["--format", "mov"] if alpha else [])
    result = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=3600)
    require(result.returncode == 0 and out.exists(), "hyperframes render failed: " + (result.stderr or result.stdout)[-600:])
    return str(out)


NOT_MEDIA = (".txt", ".md", ".json", ".pdf", ".docx", ".csv")  # notes and documents: no ffprobe


def ingest(edit_root, files, link=False):
    """Copy (or symlink) the owner's raw files into raw/ and record probe + sha256 in media.json."""
    from ..core import file_hash, project_lock, read_json
    from . import media
    root = Path(edit_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "raw").mkdir(exist_ok=True)
    with project_lock(root):
        path = root / "media.json"
        log = read_json(path) if path.exists() else {"files": {}}
        added = []
        for f in files:
            f = Path(f)
            require(f.is_file(), "Missing file " + str(f))
            target = root / "raw" / f.name
            if target.exists() or target.is_symlink():
                # Same name, different bytes: refuse rather than silently keep the old take.
                require(target.exists() and file_hash(target) == file_hash(f),
                        "raw/{} already holds a different file; rename the source and ingest again".format(f.name))
            else:
                if link:
                    target.symlink_to(f.resolve())
                else:
                    shutil.copy2(f, target)
            rel = "raw/" + f.name
            info = media.probe(target) if target.suffix.lower() not in (".srt", ".vtt", ".cube") + NOT_MEDIA else {}
            log["files"][rel] = {"sha256": file_hash(target), "probe": info, "ingested": now(), "original": str(f)}
            added.append({"file": rel, "duration": tc(info.get("duration", 0)) if info else "-",
                          "video": "{}x{}".format(info.get("width"), info.get("height")) if info.get("has_video") else "-",
                          "audio": info.get("has_audio", False)})
        write_json(path, log)
        return added


__all__ = ["doctor", "fetch", "transcribe", "mg_new", "mg_render", "ingest"]
