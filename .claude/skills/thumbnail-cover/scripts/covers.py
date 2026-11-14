#!/usr/bin/env python3
"""Pick the strongest frames of a finished video and turn them into a Reel cover and a YouTube thumbnail, in three
layouts each, with the studio fonts.

    python3 .claude/skills/thumbnail-cover/scripts/covers.py pick final.mp4 out/ [--n 6] [--skip 0.5]
    python3 .claude/skills/thumbnail-cover/scripts/covers.py make out/cand_02.png "मौत से डर?" out/ \
        [--sub "Honey Singh ne kya kaha"] [--accent "#ffd400"] [--font "Rozha One"] [--force]

pick: samples the video every 0.25 s, scores each frame for sharpness (Laplacian variance), contrast, and colour, skips
      the first --skip seconds and frames within 0.2 s of a cut (blurry mid-transition), keeps the best --n that are
      at least 1 s apart, and writes cand_01.png ... plus candidates.json and a candidates sheet (sheet.png).
make: writes cover_reel_<A|B|C>.png (1080x1920, text inside the Instagram grid crop and safe zone) and
      thumb_yt_<A|B|C>.png (1280x720), rendered through a canvas page in headless Chromium so Devanagari shapes right.
      A: big text top on a dark gradient. B: text bottom-left on a colour band. C: split, text panel beside the frame.
Needs numpy, Pillow, FFmpeg, Node with Playwright (studio/render_canvas.cjs). Never overwrites without --force.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
STUDIO = REPO / "studio"


def _frames(video: str, step: float, w: int = 320):
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                           "-of", "csv=p=0", video], capture_output=True, text=True, check=True).stdout
    vw, vh = map(int, info.strip().split(",")[:2])
    h = int(round(vh * w / vw / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={1 / step},scale={w}:{h}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)


def score(rgb: np.ndarray) -> float:
    g = rgb.mean(axis=2)
    lap = (-4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
    sharp = float(lap.var())
    contrast = float(g.std())
    sat = float((rgb.max(axis=2) - rgb.min(axis=2)).mean())
    dark = max(0.0, 40 - g.mean()) * 3  # near-black frames lose
    return np.log1p(sharp) * 10 + contrast * 0.6 + sat * 0.3 - dark


def pick(video: str, out: Path, n: int = 6, skip: float = 0.5, step: float = 0.25) -> list[dict]:
    f = _frames(video, step)
    diffs = np.r_[0, np.abs(np.diff(f.mean(axis=3), axis=0)).mean(axis=(1, 2))]
    cut = diffs > max(25.0, 6 * float(np.median(diffs) + 1e-6))
    near_cut = cut | np.r_[cut[1:], False] | np.r_[False, cut[:-1]]
    scored = [(score(fr), i * step) for i, fr in enumerate(f) if i * step >= skip and not near_cut[i]]
    scored.sort(reverse=True)
    chosen: list[tuple[float, float]] = []
    for s, t in scored:
        if all(abs(t - c[1]) >= 1.0 for c in chosen):
            chosen.append((s, t))
        if len(chosen) == n:
            break
    out.mkdir(parents=True, exist_ok=True)
    res = []
    for k, (s, t) in enumerate(sorted(chosen, key=lambda x: x[1]), 1):
        p = out / f"cand_{k:02d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", str(p)], check=True)
        res.append({"file": p.name, "t": round(t, 2), "score": round(float(s), 1)})
    (out / "candidates.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    from PIL import Image
    if res:
        ims = [Image.open(out / r["file"]).convert("RGB") for r in res]
        th = 360
        ims = [im.resize((int(im.width * th / im.height), th)) for im in ims]
        sheet = Image.new("RGB", (sum(i.width for i in ims) + 10 * (len(ims) - 1), th), "black")
        x = 0
        for im in ims:
            sheet.paste(im, (x, 0))
            x += im.width + 10
        sheet.save(out / "sheet.png")
    return res


PAGE = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="{fonts}">
<canvas width="{W}" height="{H}"></canvas>
<script src="{kit}"></script>
<script>
const K = STUDIO, W = {W}, H = {H}, TITLE = {title}, SUB = {sub}, ACC = {acc}, FONT = {font}, LAYOUT = {layout};
let img;
K.whenReady(async () => {{ img = await K.loadImage({img}); }});
function cover(ctx, x, y, w, h) {{                       // cover-crop the frame into a rect, never stretched
  const s = Math.max(w / img.width, h / img.height), iw = img.width * s, ih = img.height * s;
  ctx.drawImage(img, x + (w - iw) / 2, y + (h - ih) / 2, iw, ih);
}}
function fit(ctx, text, maxW, size, weight) {{
  let s = size; ctx.font = `${{weight}} ${{s}}px "${{FONT}}", "Noto Sans Devanagari", "Inter"`;
  while (ctx.measureText(text).width > maxW && s > 30) {{ s *= 0.94; ctx.font = `${{weight}} ${{s}}px "${{FONT}}", "Noto Sans Devanagari", "Inter"`; }}
  return s;
}}
function measure(ctx, maxW, size, subSize) {{            // lay out the title (max 2 lines) and the subtitle before drawing
  const ws = TITLE.split(' '), lines = [];
  if (ws.length > 2) {{ const m = Math.ceil(ws.length / 2); lines.push(ws.slice(0, m).join(' '), ws.slice(m).join(' ')); }} else lines.push(TITLE);
  const s = Math.min(...lines.map(l => fit(ctx, l, maxW, size, 900)));
  const ss = SUB ? fit(ctx, SUB, maxW, subSize, 600) : 0;
  return {{ lines, s, ss, h: lines.length * s * 1.08 + (SUB ? ss * 1.5 : 0) }};
}}
function draw(ctx, B, x, top, align) {{                   // top = top of the block; last word of the title in the accent
  ctx.textAlign = align; ctx.textBaseline = 'alphabetic'; ctx.lineJoin = 'round';
  B.lines.forEach((l, i) => {{
    ctx.font = `900 ${{B.s}}px "${{FONT}}", "Noto Sans Devanagari", "Inter"`;
    const yy = top + B.s * 0.9 + i * B.s * 1.08;
    ctx.lineWidth = B.s * 0.16; ctx.strokeStyle = '#000'; ctx.strokeText(l, x, yy);
    const last = i === B.lines.length - 1 && TITLE.includes(' ') ? l.split(' ').pop() : '';
    const head = l.slice(0, l.length - last.length), full = ctx.measureText(l).width, hw = ctx.measureText(head).width;
    const x0 = align === 'center' ? x - full / 2 : x;
    ctx.textAlign = 'left'; ctx.fillStyle = '#fff'; ctx.fillText(head, x0, yy);
    if (last) {{ ctx.fillStyle = ACC; ctx.fillText(last, x0 + hw, yy); }}
    ctx.textAlign = align;
  }});
  if (SUB) {{
    ctx.font = `600 ${{B.ss}}px "Inter", "Noto Sans Devanagari"`; ctx.fillStyle = ACC;
    ctx.fillText(SUB, x, top + B.lines.length * B.s * 1.08 + B.ss * 1.2);
  }}
}}
window.FILM = {{ DUR: 1, init() {{}}, render(ctx) {{
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  const tall = H > W, pad = tall ? 90 : 56;
  // reel text stays in the safe zone (top 250, bottom 420) and inside the 3:4 profile-grid crop (y 240..1680)
  const safeTop = tall ? 300 : 40, safeBottom = tall ? H - 460 : H - 40;
  if (LAYOUT === 'C') {{
    const pw = tall ? W : Math.round(W * 0.42), ph = tall ? Math.round(H * 0.4) : H;
    cover(ctx, tall ? 0 : pw, tall ? ph : 0, tall ? W : W - pw, tall ? H - ph : H);
    ctx.fillStyle = ACC; ctx.fillRect(0, 0, pw, ph);
    ctx.fillStyle = 'rgba(0,0,0,0.88)'; ctx.fillRect(10, 10, pw - 20, ph - 20);
    const B = measure(ctx, pw - 2 * pad, tall ? 150 : 110, tall ? 50 : 38);
    const lo = tall ? Math.max(safeTop, 40) : 40, hi = ph - 40;
    draw(ctx, B, pw / 2, Math.max(lo, (lo + hi - B.h) / 2), 'center');
  }} else {{
    cover(ctx, 0, 0, W, H);
    const top = LAYOUT === 'A';
    const g = ctx.createLinearGradient(0, top ? 0 : H, 0, top ? H * 0.55 : H * 0.45);
    g.addColorStop(0, 'rgba(0,0,0,0.85)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const B = measure(ctx, W - 2 * pad - (top ? 0 : 24), tall ? 160 : 118, tall ? 54 : 40);
    const y = top ? safeTop : safeBottom - B.h;
    if (!top) {{ ctx.fillStyle = ACC; ctx.fillRect(pad - 26, y, 12, B.h); }}
    draw(ctx, B, top ? W / 2 : pad, y, top ? 'center' : 'left');
    window.__box = {{ y, h: B.h }};
  }}
}} }};
</script>"""


def make(frame: str, title: str, out: Path, sub: str = "", accent: str = "#ffd400", font: str = "Rozha One",
         force: bool = False) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    targets = [(f"cover_reel_{L}.png", 1080, 1920, L) for L in "ABC"] + [(f"thumb_yt_{L}.png", 1280, 720, L) for L in "ABC"]
    if not force:
        clash = [n for n, *_ in targets if (out / n).exists()]
        if clash:
            sys.exit(f"{', '.join(clash)} exist in {out}; ask the owner, then pass --force")
    written = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, W, H, L in targets:
            page = Path(tmp) / f"{name}.html"
            page.write_text(PAGE.format(fonts=(STUDIO / "fonts" / "fonts.css").as_uri(), kit=(STUDIO / "canvas_kit.js").as_uri(),
                                        W=W, H=H, title=json.dumps(title, ensure_ascii=False), sub=json.dumps(sub, ensure_ascii=False),
                                        acc=json.dumps(accent), font=json.dumps(font), layout=json.dumps(L),
                                        img=json.dumps(Path(frame).resolve().as_uri())), encoding="utf-8")
            prefix = Path(tmp) / name[:-4]
            r = subprocess.run(["node", str(STUDIO / "render_canvas.cjs"), str(page), str(prefix), "--size", f"{W}x{H}",
                                "--stills", "0"], capture_output=True, text=True, timeout=120)
            if r.returncode:
                sys.exit(r.stderr or r.stdout)
            os.replace(f"{prefix}_1.png", out / name)
            written.append(out / name)
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pick")
    p.add_argument("video")
    p.add_argument("out")
    p.add_argument("--n", type=int, default=6)
    p.add_argument("--skip", type=float, default=0.5)
    m = sub.add_parser("make")
    m.add_argument("frame")
    m.add_argument("title")
    m.add_argument("out")
    m.add_argument("--sub", default="")
    m.add_argument("--accent", default="#ffd400")
    m.add_argument("--font", default="Rozha One")
    m.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "pick":
        res = pick(a.video, Path(a.out), a.n, a.skip)
        print(json.dumps(res, ensure_ascii=False))
    else:
        for f in make(a.frame, a.title, Path(a.out), a.sub, a.accent, a.font, a.force):
            print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
