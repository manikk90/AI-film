"""Assemble the approved EDL with FFmpeg, master the loudness, and QC the result against
`editor/rules.json` (the rules Mann has learned from the owner's corrections)."""

import shutil
from pathlib import Path

from ..core import ProductionError, inside, now, project_lock, read_json, require, write_json
from . import edl as E
from . import media

REPO = Path(__file__).resolve().parents[2]
RULES = REPO / "editor" / "rules.json"
STYLES = REPO / "editor" / "styles"


def atempo(speed):
    """atempo accepts 0.5-2.0 per stage; chain stages for other speeds."""
    parts, s = [], float(speed)
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    if abs(s - 1.0) > 1e-6:
        parts.append("atempo={:.5f}".format(s))
    return parts


CACHE_VERSION = 1


def clip_audio_chain(edl, clip, probes):
    """Audio filters for one clip, or None when the clip is silent (filled with anullsrc)."""
    keep = edl.get("audio", {}).get("keep_source", True)
    if not (keep and clip.get("audio", True) and probes[clip["source"]]["has_audio"]):
        return None
    return ",".join(["asetpts=PTS-STARTPTS"] + atempo(clip.get("speed", 1.0)) + [
        "aresample=48000", "aformat=sample_fmts=fltp:channel_layouts=stereo", "apad", "atrim=0:{:.4f}".format(E.clip_duration(clip))])


def clip_cache_key(root, edl, clip, probes):
    """Everything that shapes a clip's own pixels and sound. Text, inserts, transitions and
    overlays are applied at assembly, so changing them never re-renders the clip."""
    from ..core import fingerprint
    from . import reframe
    own = {k: v for k, v in clip.items() if k not in ("id", "text", "inserts", "transition_in", "beat")}
    files = {"src": E.hashed(root, edl["sources"][clip["source"]])}
    if edl.get("grade", {}).get("lut"):
        files["lut"] = E.hashed(root, edl["grade"]["lut"])
    return fingerprint({"v": CACHE_VERSION, "clip": own, "files": files, "format": edl["format"], "grade": edl.get("grade", {}),
                        "audio": clip_audio_chain(edl, clip, probes) is not None, "reframe": reframe.VERSION})


def cache_dir(root):
    return Path(root) / "renders" / "cache"


def render_clip(root, edl, clip, probes, target):
    src = inside(root, edl["sources"][clip["source"]])
    span = clip["out"] - clip["in"]
    dur = E.clip_duration(clip)
    textfiles = []
    vchain = E.clip_video_chain(root, edl, clip, textfiles)
    achain = clip_audio_chain(edl, clip, probes)
    graph = "[0:v]{}[v];".format(vchain) + ("[0:a]{}[a]".format(achain) if achain else
                                           "anullsrc=r=48000:cl=stereo,atrim=0:{:.4f},aformat=sample_fmts=fltp[a]".format(dur))
    tmp = target.with_name(".tmp-" + target.name)
    media.run(["ffmpeg", "-hide_banner", "-y", "-ss", "{:.3f}".format(clip["in"]), "-t", "{:.3f}".format(span), "-i", str(src),
               "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
               "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-t", "{:.3f}".format(dur), str(tmp)])
    tmp.replace(target)


def cached_clips(root, edl, probes, build=False, workers=None):
    """Map clip id -> cached render. With build=True, render missing clips (in parallel)."""
    import os
    from concurrent.futures import ThreadPoolExecutor
    folder = cache_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    want = {c["id"]: (c, folder / (clip_cache_key(root, edl, c, probes)[:24] + ".mkv")) for c in edl["clips"]}
    have = {cid: path for cid, (c, path) in want.items() if path.exists()}
    missing = [(c, path) for cid, (c, path) in want.items() if cid not in have]
    stats = {"cached": len(have), "rendered": 0}
    if build and missing:
        with ThreadPoolExecutor(max_workers=workers or min(4, os.cpu_count() or 2)) as pool:
            list(pool.map(lambda cp: render_clip(root, edl, cp[0], probes, cp[1]), missing))
        for c, path in missing:
            have[c["id"]] = path
        stats["rendered"] = len(missing)
    return have, stats


def prune_cache(root, keep):
    keep = {Path(p).name for p in keep}
    for f in cache_dir(root).glob("*.mkv"):
        if f.name not in keep:
            f.unlink()


def build_graph(root, edl, probes, textfiles, sub_shift=0.0, cache=None):
    """Return (ffmpeg input args, filter_complex, video label, audio label, total seconds).
    Clips found in `cache` (id -> processed file) are used as-is instead of re-processing."""
    inputs, graph = [], []
    rows, total = E.timeline(edl)
    audio_cfg = edl.get("audio", {})
    keep = audio_cfg.get("keep_source", True)
    cache = cache or {}
    for i, clip in enumerate(edl["clips"]):
        dur = E.clip_duration(clip)
        if clip["id"] in cache:
            inputs += ["-i", str(cache[clip["id"]])]
            # Matroska cache streams can expose an unknown filter frame rate on
            # FFmpeg 7. xfade requires CFR inputs, even when cached pixels already
            # have the requested cadence. Restore the EDL rate explicitly.
            graph.append("[{}:v]setpts=PTS-STARTPTS,fps={},settb=AVTB[v{}]".format(i, edl["format"].get("fps", 30), i))
            graph.append("[{}:a]asetpts=PTS-STARTPTS,atrim=0:{:.4f}[a{}]".format(i, dur, i))
            continue
        src = inside(root, edl["sources"][clip["source"]])
        span = clip["out"] - clip["in"]
        inputs += ["-ss", "{:.3f}".format(clip["in"]), "-t", "{:.3f}".format(span), "-i", str(src)]
        graph.append("[{}:v]{}[v{}]".format(i, E.clip_video_chain(root, edl, clip, textfiles), i))
        achain = clip_audio_chain(edl, clip, probes)
        if achain:
            graph.append("[{}:a]{}[a{}]".format(i, achain, i))
        else:
            graph.append("anullsrc=r=48000:cl=stereo,atrim=0:{:.4f},aformat=sample_fmts=fltp[a{}]".format(dur, i))
    v, a, length = "v0", "a0", E.clip_duration(edl["clips"][0])
    for i in range(1, len(edl["clips"])):
        kind, tdur = E.transition(edl["clips"][i])
        nv, na = "vj{}".format(i), "aj{}".format(i)
        if kind == "cut":
            graph.append("[{}][{}][v{}][a{}]concat=n=2:v=1:a=1[{}][{}]".format(v, a, i, i, nv, na))
        else:
            xf = "fade" if kind == "dissolve" else kind
            graph.append("[{}][v{}]xfade=transition={}:duration={:.3f}:offset={:.3f}[{}]".format(v, i, xf, tdur, length - tdur, nv))
            graph.append("[{}][a{}]acrossfade=d={:.3f}[{}]".format(a, i, tdur, na))
        length += E.clip_duration(edl["clips"][i]) - tdur
        v, a = nv, na
    n_inputs = len(edl["clips"])
    fmt = edl["format"]
    for i, clip in enumerate(edl["clips"]):
        for k, ins in enumerate(clip.get("inserts", [])):
            span = ins["out"] - ins["in"]
            at = rows[i]["start"] + float(ins.get("at", 0))
            inputs += ["-ss", "{:.3f}".format(ins["in"]), "-t", "{:.3f}".format(span), "-i", str(inside(root, edl["sources"][ins["source"]]))]
            graph.append("[{}:v]{}[ins{}_{}]".format(n_inputs, E.insert_chain(root, edl, clip, ins, at), i, k))
            graph.append("[{}][ins{}_{}]overlay=eof_action=pass:enable='between(t,{:.3f},{:.3f})'[vi{}_{}]".format(v, i, k, at, at + span, i, k))
            v = "vi{}_{}".format(i, k)
            n_inputs += 1
    for k, ov in enumerate(edl.get("overlays", [])):
        inputs += ["-i", str(inside(root, ov["file"]))]
        at = float(ov.get("at", 0))
        graph.append("[{}:v]scale={}:{},setpts=PTS-STARTPTS+{:.3f}/TB[ov{}]".format(n_inputs, fmt["width"], fmt["height"], at, k))
        graph.append("[{}][ov{}]overlay=eof_action=pass:format=auto[vo{}]".format(v, k, k))
        v = "vo{}".format(k)
        n_inputs += 1
    script = E.ass_script(root, edl, sub_shift)
    if script:
        textfiles.append(str(script))
        from .fonts import font_dir
        fdir = ":fontsdir='{}'".format(E.esc(font_dir())) if font_dir().exists() else ""
        graph.append("[{}]ass=filename='{}'{}:shaping=complex[vs]".format(v, E.esc(script), fdir))
        v = "vs"
    graph.append("[{}]format=yuv420p[vout]".format(v))
    # Audio: dialogue/source bed, music (looped, ducked), SFX.
    gain = float(audio_cfg.get("source_gain_db", 0))
    music = audio_cfg.get("music")
    duck = bool(music and music.get("duck", True) and keep)
    graph.append("[{}]volume={}dB,atrim=0:{:.4f}{}".format(a, gain, total, ",asplit=2[bed][key]" if duck else "[bed]"))
    mix = ["bed"]
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(inside(root, music["file"]))]
        start = float(music.get("start", 0))
        fade = float(music.get("fade_out", 1.5))
        chain = ["aresample=48000", "aformat=sample_fmts=fltp:channel_layouts=stereo", "atrim={:.3f}:{:.3f}".format(start, start + total),
                 "asetpts=PTS-STARTPTS", "volume={}dB".format(float(music.get("gain_db", -16)))]
        if fade:
            chain.append("afade=t=out:st={:.3f}:d={:.3f}".format(max(total - fade, 0), fade))
        graph.append("[{}:a]{}[mus]".format(n_inputs, ",".join(chain)))
        n_inputs += 1
        if duck:
            graph.append("[mus][key]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350:makeup=1[musd]")
            mix.append("musd")
        else:
            mix.append("mus")
    for k, sfx in enumerate(audio_cfg.get("sfx", [])):
        inputs += ["-i", str(inside(root, sfx["file"]))]
        ms = int(round(float(sfx["at"]) * 1000))
        graph.append("[{}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={}dB,adelay={}|{}[sfx{}]".format(
            n_inputs, float(sfx.get("gain_db", 0)), ms, ms, k))
        mix.append("sfx{}".format(k))
        n_inputs += 1
    if len(mix) > 1:
        graph.append("{}amix=inputs={}:duration=first:normalize=0,atrim=0:{:.4f}[aout]".format("".join("[{}]".format(m) for m in mix), len(mix), total))
    else:
        graph.append("[bed]anull[aout]")
    return inputs, ";".join(graph), "vout", "aout", total


QUALITY = {"draft": ("veryfast", "20"), "standard": ("faster", "18"), "best": ("slow", "16")}


def render(root, preview=True, quality="standard"):
    root = Path(root)
    media.need("ffmpeg")
    require(quality in QUALITY, "quality must be one of {}".format(sorted(QUALITY)))
    with project_lock(root):
        edl = E.load(root)
        E.require_decisions(root, edl)
        E.require_approval(root, edl)
        probes = E.validate(root, edl)
        out = root / "renders"
        out.mkdir(parents=True, exist_ok=True)
        stage, master = out / ".stage.mkv", out / "master.mp4"
        cache, stats = cached_clips(root, edl, probes, build=True)
        textfiles = []
        try:
            inputs, graph, v, a, total = build_graph(root, edl, probes, textfiles, cache=cache)
            media.run(["ffmpeg", "-hide_banner", "-y"] + inputs + ["-filter_complex", graph, "-map", "[" + v + "]", "-map", "[" + a + "]",
                       "-c:v", "libx264", "-preset", QUALITY[quality][0], "-crf", QUALITY[quality][1], "-pix_fmt", "yuv420p",
                       "-r", str(edl["format"].get("fps", 30)),
                       "-c:a", "pcm_s16le", "-t", "{:.3f}".format(total), str(stage)])
        finally:
            for f in textfiles:
                Path(f).unlink(missing_ok=True)
        target = edl.get("master", {})
        lufs, tp = float(target.get("lufs", -14)), float(target.get("true_peak", -1))
        measured = media.loudness(stage)
        if measured["lufs"] is None:
            norm = "anull"
        else:
            norm = ("loudnorm=I={}:TP={}:LRA=11:measured_I={}:measured_TP={}:measured_LRA={}:linear=true,"
                    "aresample=48000").format(lufs, tp, measured["lufs"], measured["true_peak"], measured["lra"] or 7)
        media.run(["ffmpeg", "-hide_banner", "-y", "-i", str(stage), "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", norm,
                   "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(master)])
        # loudnorm misses on very short or very dynamic mixes; measure and correct with a gain + limiter pass.
        result = media.loudness(master) if measured["lufs"] is not None else {"lufs": None}
        for _ in range(2):
            if result["lufs"] is None or abs(result["lufs"] - lufs) <= 0.5:
                break
            fixed = out / ".fixed.mp4"
            limit = 10 ** ((tp - 0.3) / 20.0)
            media.run(["ffmpeg", "-hide_banner", "-y", "-i", str(stage), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                       "-af", "{},volume={:.2f}dB,alimiter=limit={:.4f}:level=disabled".format(norm, lufs - result["lufs"], limit),
                       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(fixed)])
            fixed.replace(master)
            norm = "{},volume={:.2f}dB".format(norm, lufs - result["lufs"])
            result = media.loudness(master)
        stage.unlink(missing_ok=True)
        if preview:
            media.run(["ffmpeg", "-hide_banner", "-y", "-i", str(master), "-vf", "scale='if(gt(iw,ih),-2,720)':'if(gt(iw,ih),720,-2)'",
                       "-c:v", "libx264", "-crf", "26", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k", str(out / "preview_720p.mp4")])
        prune_cache(root, cache.values())
        from . import footage
        credits_file = footage.credits(root, edl)
        write_json(out / "render.json", {"edl_fingerprint": E.edit_fingerprint(root, edl), "rendered": now(),
                                         "expected_seconds": total, "file": "renders/master.mp4", "clips": stats})
        return {"master": str(master), "expected_seconds": total, "clips_reused": stats["cached"], "clips_rendered": stats["rendered"],
                "credits": credits_file}


def preview_part(root, ids, context=1):
    """Render only the corrected part (plus one neighbour each side) as a quick 720p check copy
    for the owner. It is a preview, not the film: the full render still needs the approvals."""
    root = Path(root)
    media.need("ffmpeg")
    edl = E.load(root)
    part, offset, length = E.sub_edl(edl, ids, context)
    probes = E.validate(root, part)
    out = root / "renders" / "parts"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "part-{}.mp4".format("-".join(ids))
    textfiles = []
    try:
        cache, _ = cached_clips(root, part, probes)
        inputs, graph, v, a, total = build_graph(root, part, probes, textfiles, sub_shift=offset, cache=cache)
        scale = "scale='if(gt(iw,ih),-2,720)':'if(gt(iw,ih),720,-2)'"
        graph += ";[{}]{}[pv];[{}]loudnorm=I=-14:TP=-1.5[pa]".format(v, scale, a)
        media.run(["ffmpeg", "-hide_banner", "-y"] + inputs + ["-filter_complex", graph, "-map", "[pv]", "-map", "[pa]",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                   "-t", "{:.3f}".format(total), str(target)])
    finally:
        for f in textfiles:
            Path(f).unlink(missing_ok=True)
    return {"file": str(target), "covers": "{}-{} of the film".format(E.tc(offset), E.tc(offset + length)),
            "clips": [c["id"] for c in part["clips"]]}


def load_rules():
    return read_json(RULES)


def style_targets(name):
    if not name:
        return None
    path = STYLES / name / "style.json"
    return read_json(path) if path.exists() else None


def qc(root):
    """Measure the master and compare it with the EDL, the learned rules and the style target.
    Writes renders/qc.json and renders/QC.md. Returns the record; `passed` is False on any failure."""
    root = Path(root)
    edl = E.load(root)
    master = root / "renders" / "master.mp4"
    require(master.exists(), "No renders/master.mp4; render first")
    rules = load_rules()["rules"]
    info = media.probe(master)
    _, total = E.timeline(edl)
    fmt = edl["format"]
    checks = []

    def check(name, ok, detail, kind="fail"):
        checks.append({"check": name, "result": "pass" if ok else kind, "detail": detail})

    frame = 1.0 / float(fmt.get("fps", 30))
    check("duration", abs(info["duration"] - total) <= max(2 * frame, 0.08), "{:.3f}s vs planned {:.3f}s".format(info["duration"], total))
    check("resolution", (info.get("width"), info.get("height")) == (fmt["width"], fmt["height"]),
          "{}x{} vs {}x{}".format(info.get("width"), info.get("height"), fmt["width"], fmt["height"]))
    check("fps", abs(info.get("fps", 0) - float(fmt.get("fps", 30))) < 0.05, "{} fps".format(info.get("fps")))
    target = edl.get("master", {})
    lufs_target = float(target.get("lufs", rules["loudness_lufs"]))
    loud = media.loudness(master) if info["has_audio"] else {"lufs": None, "true_peak": None}
    if loud["lufs"] is None:
        check("loudness", False, "no measurable audio")
    else:
        check("loudness", abs(loud["lufs"] - lufs_target) <= rules["loudness_tolerance_lu"], "{} LUFS (target {})".format(loud["lufs"], lufs_target))
        check("true peak", loud["true_peak"] <= float(target.get("true_peak", rules["true_peak_max_db"])) + 0.2,
              "{} dBTP (max {})".format(loud["true_peak"], target.get("true_peak", rules["true_peak_max_db"])))
    blacks = [b for b in media.black_segments(master, rules["max_black_seconds"]) if not edl.get("allow_black")]
    check("black frames", not blacks, ", ".join("{}-{}".format(E.tc(b["start"]), E.tc(b["end"])) for b in blacks) or "none")
    dead = [s for s in media.silences(master, rules["dead_air_noise_db"], rules["max_dead_air_seconds"])
            if not any(abs((s["start"] or 0) - float(d)) < 0.5 for d in edl.get("deliberate_silences", []))]
    check("dead air", not dead, ", ".join("{}-{}".format(E.tc(s["start"]), E.tc(s["end"] if s["end"] is not None else total)) for s in dead) or "none")
    stats = E.pace(edl)
    short = fmt["height"] > fmt["width"] and total <= rules["short_form_max_seconds"]
    if short:
        check("shot length (short form)", stats["longest_shot_seconds"] <= rules["short_form_max_shot_seconds"],
              "longest {}s (max {}s)".format(stats["longest_shot_seconds"], rules["short_form_max_shot_seconds"]), "warn")
        first = E.timeline(edl)[0][0]["duration"]
        check("hook (first cut)", first <= rules["hook_first_cut_max_seconds"], "first shot {}s (max {}s)".format(first, rules["hook_first_cut_max_seconds"]), "warn")
        check("subtitles", bool(edl.get("subtitles")) or not rules["short_form_requires_subtitles"], "burned subtitles required for short form", "fail")
    check("shortest shot", stats["shortest_shot_seconds"] >= rules["min_shot_seconds"],
          "{}s (min {}s)".format(stats["shortest_shot_seconds"], rules["min_shot_seconds"]), "warn")
    style = style_targets(edl.get("style"))
    if style and style.get("targets", {}).get("average_shot_seconds"):
        want = style["targets"]["average_shot_seconds"]
        tol = rules["style_pace_tolerance"]
        check("style pace ({})".format(edl["style"]), abs(stats["average_shot_seconds"] - want) <= want * tol,
              "average shot {}s vs style {}s (±{:.0%})".format(stats["average_shot_seconds"], want, tol), "warn")
    from . import craft
    for f in craft.check(root, edl, sample_contrast=False):
        if f["result"] != "pass":
            checks.append({"check": "craft: " + f["check"], "result": f["result"], "detail": "{} (rule `{}`)".format(f["detail"], f["rule"])})
    failed = [c for c in checks if c["result"] == "fail"]
    record = {"edl_fingerprint": E.edit_fingerprint(root, edl), "checked": now(), "passed": not failed, "checks": checks,
              "measured": {"probe": info, "loudness": loud, "pace": stats},
              "not_checked": ["picture quality and continuity by eye", "lip sync", "audio quality by ear",
                              "spoken words vs the approved script (run `transcribe` on the master when Whisper is available)"]}
    write_json(root / "renders" / "qc.json", record)
    lines = ["# QC: {}".format(edl.get("title", "untitled")), "", "Result: **{}**".format("PASS" if record["passed"] else "FAIL"), "",
             "| Check | Result | Detail |", "|---|---|---|"]
    lines += ["| {} | {} | {} |".format(c["check"], c["result"].upper(), c["detail"]) for c in checks]
    lines += ["", "Not checked by this tool (Mann reviews the contact frames and says so plainly):", ""]
    lines += ["- " + x for x in record["not_checked"]]
    (root / "renders" / "QC.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return record


def contact_frames(root, every=1.5):
    """Individual numbered QC frames from the master, every `every` seconds."""
    root = Path(root)
    master = root / "renders" / "master.mp4"
    require(master.exists(), "No renders/master.mp4; render first")
    dur = media.probe(master)["duration"]
    out = root / "renders" / "qc-frames"
    if out.exists():
        shutil.rmtree(out)
    files, t, n = [], 0.0, 0
    while t < dur:
        n += 1
        files.append(str(media.save_frame(master, t, out / "Q{:03d}_{}.jpg".format(n, E.tc(t).replace(":", "m") + "s"), width=540)))
        t += every
    return files


__all__ = ["render", "qc", "contact_frames", "ProductionError"]
