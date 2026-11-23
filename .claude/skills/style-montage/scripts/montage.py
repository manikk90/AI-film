#!/usr/bin/env python3
"""One scene, many styles, one reel: plan the style pages, check every loop, and cut them into a montage.

    python3 .claude/skills/style-montage/scripts/montage.py plan <slug> --styles pop_art,voxel_3d,madhubani,...
                    (--preset golden_hour | --scene "..." --action "...") [--dur 6] [--force]
    python3 .claude/skills/style-montage/scripts/montage.py check <slug>
    python3 .claude/skills/style-montage/scripts/montage.py assemble <slug> [--seg 0.9 | --beats beats.json --every 2]
                    [--audio song.mp3] [--hook "1 PROMPT\\N10 STYLES"] [--hook-dur 1.2] [--grid-dur 1.6]
                    [--size 1080x1920] [--fps 30] [--out montage.mp4]

plan      writes projects/<slug>/motion.js (the one shared subject path and camera, a pure function of t) and one
          living-painting page per style in projects/<slug>/styles/NN-<style>/painting.html, each loading motion.js,
          so the subject is in the same place at the same t in every style.
check     runs living-painting's loop_check on every styles/*/loop.mp4. assemble refuses a montage with a failing loop.
assemble  cuts the loops on one continuous clock: segment k shows style k at the same moment of the motion the cut
          left (source time = global time mod the loop length), so the subject keeps moving across every style change.
          A hook card opens it, a numbered label chip names each style, a grid of all styles closes it. Text is set
          with libass (shaping=complex) from the vendored studio fonts, so Hindi is shaped correctly.
          Writes the video and montage.json (segments, sources, loop checks).
Needs FFmpeg with libass, numpy and Pillow.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LP = REPO / ".claude" / "skills" / "living-painting"
FONTS = REPO / "studio" / "fonts"
sys.path.insert(0, str(LP / "scripts"))
import loop_check  # noqa: E402
import new_painting  # noqa: E402

MOTION_JS = """// Shared motion for the style montage '{slug}' (studio /style-montage). Every style page loads this file, so the
// subject is in the same place at the same t in every style and a cut between styles never jumps.
// Edit the paths here, once, for the scene; never inside one style's page. Whole cycles of DUR only (seamless loops).
// Scene: {scene}
// Action: {action}
window.MOTION = {{
  DUR: {dur},
  SEED: {seed},
  // the subject: x, y in 0..1 of the frame, angle in radians, phase 0..1 of its main action cycle (stride, wingbeat)
  subject(t) {{
    const u = (t % this.DUR) / this.DUR, TAU = Math.PI * 2;
    return {{ x: 0.5 + 0.18 * Math.sin(u * TAU), y: 0.55 + 0.04 * Math.sin(u * TAU * 2), angle: u * TAU,
             phase: (u * 4) % 1 }};
  }},
  // the camera: zoom 1 = full frame; pan in frame fractions. A gentle whole-cycle breath, the same in every style.
  camera(t) {{
    const u = (t % this.DUR) / this.DUR, TAU = Math.PI * 2;
    return {{ zoom: 1.12 + 0.06 * Math.sin(u * TAU), panX: 0.02 * Math.sin(u * TAU), panY: 0 }};
  }},
}};
"""


def projects() -> Path:
    return REPO / "projects"


def style_dirs(slug: str) -> list[Path]:
    d = projects() / slug / "styles"
    return sorted(p for p in d.iterdir() if p.is_dir() and re.match(r"\d\d-", p.name)) if d.is_dir() else []


# ---------------------------------------------------------------------------------------------------- plan

def plan(slug, styles, preset=None, scene=None, action=None, dur=6, force=False) -> dict:
    allst = new_painting.all_styles()
    unknown = [s for s in styles if s not in allst]
    if unknown:
        raise SystemExit(f"unknown style(s) {', '.join(unknown)}; living-painting new_painting.py --list-styles")
    if len(styles) < 2:
        raise SystemExit("a montage needs at least 2 styles")
    presets = new_painting.load(LP / "presets.json")
    if preset:
        if preset not in presets:
            raise SystemExit(f"unknown preset {preset!r}")
        scene, action = presets[preset]["scene"], presets[preset]["action"]
    if not scene:
        raise SystemExit("give --preset, or --scene (and --action)")
    root = projects() / slug
    motion = root / "motion.js"
    if motion.exists() and not force:
        raise SystemExit(f"{motion} exists; ask the owner, then pass --force")
    root.mkdir(parents=True, exist_ok=True)
    motion.write_text(MOTION_JS.format(slug=slug, scene=scene, action=action or "", dur=dur, seed=11), encoding="utf-8")
    entries = []
    for i, key in enumerate(styles, 1):
        name = f"{i:02d}-{key}"
        argv = [name, "custom", "--scene", scene, "--style", key, "--root", str(root / "styles")]
        if action:
            argv += ["--action", action]
        if force:
            argv.append("--force")
        if new_painting.main(argv) != 0:
            raise SystemExit(f"could not make the page for {key}")
        page = root / "styles" / name / "painting.html"
        html = page.read_text(encoding="utf-8")
        tag = '<script src="../../motion.js"></script>\n'
        if tag not in html:
            html = re.sub(r'(<script src="[^"]*canvas_kit\.js"></script>\n)', lambda m: m.group(1) + tag, html, count=1)
        page.write_text(html, encoding="utf-8")
        st = allst[key]
        entries.append({"n": i, "style": key, "name": st["name"], "engine": st.get("engine", "canvas"),
                        "dir": f"styles/{name}", "page": f"styles/{name}/painting.html", "loop": f"styles/{name}/loop.mp4"})
    out = {"slug": slug, "scene": scene, "action": action or "", "dur": dur, "styles": entries}
    (root / "plan.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


# ---------------------------------------------------------------------------------------------------- check

def check(slug) -> list[dict]:
    p = load_plan(slug)
    rows = []
    for e in p["styles"]:
        f = projects() / slug / e["loop"]
        if not f.exists():
            rows.append({"style": e["style"], "loop": e["loop"], "fails": ["missing"]})
            continue
        r = loop_check.check(loop_check.frames(str(f)))
        rows.append({"style": e["style"], "loop": e["loop"], **r})
    return rows


def load_plan(slug) -> dict:
    f = projects() / slug / "plan.json"
    if not f.exists():
        raise SystemExit(f"no {f}; run plan first")
    return json.loads(f.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------------- assemble

def probe_dur(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def cut_points(n, start, seg=None, beats=None, every=1, min_seg=0.4):
    """Segment boundaries after the hook: fixed length, or every Nth beat at or after `start` (gaps under min_seg merge)."""
    if beats is None:
        return [round(start + i * seg, 4) for i in range(n + 1)]
    bs = [b for b in beats if b >= start - 1e-6][::max(1, every)]
    pts = [start]
    for b in bs:
        if b - pts[-1] >= min_seg:
            pts.append(round(b, 4))
        if len(pts) == n + 1:
            return pts
    raise SystemExit(f"the beat grid has only {len(pts) - 1} usable cuts after {start:.2f} s for {n} styles; "
                     "lower --every or use --seg")


def ass_time(s):
    cs = int(round(s * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def has_deva(s):
    return bool(re.search(r"[ऀ-ॿ]", s))


def ass_file(w, h, hook, hook_dur, segs, grid_t0, grid_dur, grid_cells) -> str:
    latin, deva = "Saira Extra Condensed", "Noto Sans Devanagari"
    chip = max(28, h // 34)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chip,{latin},{chip},&H00FFFFFF,&H00FFFFFF,&H00111111,&H96000000,1,0,0,0,100,100,2,0,3,{chip // 4},0,7,{w // 18},{w // 18},{h // 16},1
Style: Hook,{latin},{min(h // 9, w // 5)},&H00FFFFFF,&H00FFFFFF,&H00111111,&H64000000,1,0,0,0,100,100,1,0,1,{h // 160},{h // 240},5,{w // 12},{w // 12},0,1
Style: HookDeva,{deva},{min(h // 7, w // 4)},&H00FFFFFF,&H00FFFFFF,&H00111111,&H64000000,1,0,0,0,100,100,0,0,1,{h // 160},{h // 240},5,{w // 12},{w // 12},0,1
Style: Cell,{latin},{max(20, h // 52)},&H00FFFFFF,&H00FFFFFF,&H00111111,&H96000000,1,0,0,0,100,100,1,0,3,{h // 240},0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    if hook:
        st = "HookDeva" if has_deva(hook) else "Hook"
        ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(hook_dur)},{st},,0,0,0,,{{\\fad(120,160)}}{hook}")
    for s in segs:
        label = f"{s['n']:02d}  {s['name'].upper()}"
        ev.append(f"Dialogue: 1,{ass_time(s['start'])},{ass_time(s['start'] + s['dur'])},Chip,,0,0,0,,{label}")
    for (x, y, label) in grid_cells:
        ev.append(f"Dialogue: 1,{ass_time(grid_t0)},{ass_time(grid_t0 + grid_dur)},Cell,,0,0,0,,{{\\pos({x},{y})}}{label}")
    return head + "\n".join(ev) + "\n"


def grid_image(stills: list[Path], w, h, out: Path, gap=12, bg=(14, 14, 16)):
    """All styles side by side at one moment: 2 columns up to 10 styles, 3 above; each cell keeps the frame's aspect."""
    from PIL import Image
    n = len(stills)
    cols = 2 if n <= 10 else 3
    rows = math.ceil(n / cols)
    cw = (w - gap * (cols + 1)) // cols
    ch = (h - gap * (rows + 1)) // rows
    im0 = Image.open(stills[0])
    ar = im0.width / im0.height
    cw2, ch2 = (cw, int(cw / ar)) if cw / ar <= ch else (int(ch * ar), ch)
    ox = (w - (cols * cw2 + gap * (cols - 1))) // 2
    oy = (h - (rows * ch2 + gap * (rows - 1))) // 2
    canvas = Image.new("RGB", (w, h), bg)
    cells = []
    for i, p in enumerate(stills):
        r, c = divmod(i, cols)
        x, y = ox + c * (cw2 + gap), oy + r * (ch2 + gap)
        canvas.paste(Image.open(p).convert("RGB").resize((cw2, ch2), Image.LANCZOS), (x, y))
        cells.append((x + 8, y + 8))
    canvas.save(out)
    return cells


def assemble(slug, seg=0.9, beats=None, every=1, audio=None, hook=None, hook_dur=1.2, grid_dur=1.6,
             size="1080x1920", fps=30, out=None, crf=18) -> dict:
    p = load_plan(slug)
    root = projects() / slug
    rows = check(slug)
    bad = [r for r in rows if r["fails"]]
    if bad:
        raise SystemExit("loop_check fails, fix these loops first: " +
                         "; ".join(f"{r['style']}: {', '.join(r['fails'])}" for r in bad))
    w, h = map(int, size.split("x"))
    styles = p["styles"]
    n = len(styles)
    hook = f"1 PROMPT\\N{n} STYLES" if hook is None else hook  # \N is a line break in ASS
    hd = hook_dur if hook else 0.0
    beat_list = None
    if beats:
        beat_list = json.loads(Path(beats).read_text(encoding="utf-8"))["beats"]
        if hd:  # stretch the hook to the first chosen beat, so the hook-to-style cut lands on the music too
            chosen = [b for b in beat_list if b >= hd - 1e-6][::max(1, every)]
            if not chosen:
                raise SystemExit("the beat grid ends before the hook does")
            hd = round(chosen[0], 4)
    pts = cut_points(n, hd, seg=seg, beats=beat_list, every=every)
    loops = [root / e["loop"] for e in styles]
    durs = [probe_dur(f) for f in loops]
    segs = []
    for k, e in enumerate(styles):
        t0, t1 = pts[k], pts[k + 1]
        segs.append({"n": e["n"], "style": e["style"], "name": e["name"], "start": t0, "dur": round(t1 - t0, 4),
                     "source": e["loop"], "source_offset": round(t0 % durs[k], 4)})
    grid_t0 = pts[-1]
    total = round(grid_t0 + grid_dur, 4)
    out = Path(out) if out else root / "montage.mp4"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stills = []
        for k, f in enumerate(loops):  # every style at the same moment of the motion: the grid is one instant
            s = tmp / f"g{k}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{grid_t0 % durs[k]:.3f}", "-i", str(f), "-frames:v", "1",
                            str(s)], check=True)
            stills.append(s)
        cells = grid_image(stills, w, h, tmp / "grid.png")
        labels = [(x, y, f"{e['n']:02d} {e['name'].upper()}") for (x, y), e in zip(cells, styles)]
        (tmp / "t.ass").write_text(ass_file(w, h, hook, hd, segs, grid_t0, grid_dur, labels), encoding="utf-8")
        cmd = ["ffmpeg", "-v", "error", "-y"]
        parts = []
        if hd:  # the hook plays style 1 from t = 0
            cmd += ["-stream_loop", "-1", "-t", f"{hd:.4f}", "-i", str(loops[0])]
            parts.append(len(parts))
        for k, s in enumerate(segs):
            cmd += ["-stream_loop", "-1", "-ss", f"{s['source_offset']:.4f}", "-t", f"{s['dur']:.4f}", "-i", str(loops[k])]
            parts.append(len(parts))
        cmd += ["-loop", "1", "-t", f"{grid_dur:.4f}", "-framerate", str(fps), "-i", str(tmp / "grid.png")]
        parts.append(len(parts))
        fit = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setsar=1,format=yuv420p"
        chains = [f"[{i}:v]{fit},setpts=PTS-STARTPTS[v{i}]" for i in parts]
        fonts = str(FONTS).replace(":", "\\:")
        assf = str(tmp / "t.ass").replace(":", "\\:")
        chains.append("".join(f"[v{i}]" for i in parts) + f"concat=n={len(parts)}:v=1:a=0[cat]")
        chains.append(f"[cat]ass=filename='{assf}':fontsdir='{fonts}':shaping=complex[vout]")
        cmd += ["-filter_complex", ";".join(chains), "-map", "[vout]"]
        if audio:
            ai = len(parts)
            cmd += ["-i", str(audio)]
            cmd += ["-map", f"{ai}:a", "-af", f"afade=t=out:st={max(0, total - 0.6):.3f}:d=0.6", "-c:a", "aac", "-b:a", "256k"]
        cmd += ["-t", f"{total:.4f}", "-r", str(fps), "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
                "-crf", str(crf), "-movflags", "+faststart", str(out)]
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("ffmpeg failed:\n" + r.stderr[-2000:])
    report = {"slug": slug, "video": str(out.relative_to(REPO) if out.is_relative_to(REPO) else out), "size": size,
              "fps": fps, "total": total, "hook": hook, "hook_dur": hd, "grid_dur": grid_dur,
              "cuts": "beats" if beats else f"every {seg} s", "segments": segs,
              "loop_checks": [{"style": r["style"], "fails": r["fails"], "seam_ratio": r.get("seam_ratio")} for r in rows],
              "audio": str(audio) if audio else None}
    (root / "montage.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("plan")
    a.add_argument("slug")
    a.add_argument("--styles", required=True)
    a.add_argument("--preset")
    a.add_argument("--scene")
    a.add_argument("--action")
    a.add_argument("--dur", type=float, default=6)
    a.add_argument("--force", action="store_true")
    a = sub.add_parser("check")
    a.add_argument("slug")
    a = sub.add_parser("assemble")
    a.add_argument("slug")
    a.add_argument("--seg", type=float, default=0.9)
    a.add_argument("--beats")
    a.add_argument("--every", type=int, default=1)
    a.add_argument("--audio")
    a.add_argument("--hook")
    a.add_argument("--hook-dur", type=float, default=1.2)
    a.add_argument("--grid-dur", type=float, default=1.6)
    a.add_argument("--size", default="1080x1920")
    a.add_argument("--fps", type=int, default=30)
    a.add_argument("--out")
    x = ap.parse_args(argv)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", x.slug):
        raise SystemExit(f"bad slug {x.slug!r}")
    if x.cmd == "plan":
        p = plan(x.slug, [s.strip() for s in x.styles.split(",") if s.strip()], x.preset, x.scene, x.action, x.dur, x.force)
        for e in p["styles"]:
            print(f"{e['n']:02d} {e['name']:28s} {e['page']}")
        return 0
    if x.cmd == "check":
        rows = check(x.slug)
        for r in rows:
            print(f"{'OK  ' if not r['fails'] else 'FAIL'} {r['style']:18s} {', '.join(r['fails'])}")
        return 1 if any(r["fails"] for r in rows) else 0
    if shutil.which("ffmpeg") is None:
        raise SystemExit("needs FFmpeg")
    rep = assemble(x.slug, x.seg, x.beats, x.every, x.audio, x.hook, x.hook_dur, x.grid_dur, x.size, x.fps, x.out)
    print(f"{rep['video']}: {rep['total']} s, {len(rep['segments'])} styles, cuts {rep['cuts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
