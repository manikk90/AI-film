#!/usr/bin/env python3
"""Crayon carousel slides: crayon drawing on top ("One day"), real photo below ("Day one").

    python3 make_slides.py photos_dir out_dir [--font Caveat-Bold.ttf] [--first-only] [--force]

For every photo in photos_dir (jpg/jpeg/png/webp, sorted by name) that has a matching `<stem>_drawing.<ext>`,
it writes out_dir/01.png, 02.png ... (1080×1350, 4:5) and out_dir/contact_sheet.png.
- Each half (1080×672) is cover-cropped: scaled up to fill, never stretched.
- The crop is centred on the person: MediaPipe face detection when it is installed, otherwise a skin-tone and
  detail centroid. The crop window is clamped to the image, so it never shows empty borders.
- Labels in white with a soft shadow, top-left of each half. Pass --font with Caveat; without it, the best TTF found.
- Refuses to overwrite existing slides unless --force. --first-only makes just slide 1 (the preview).
Needs Pillow and numpy.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, GAP = 1080, 1350, 6
HALF = (H - GAP) // 2          # 672
EXTS = {".jpg", ".jpeg", ".png", ".webp"}
FONT_GUESSES = ["Caveat-Bold.ttf", "Caveat-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]


def load(path: Path) -> Image.Image:
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def find_font(path: str | None, size: int) -> ImageFont.ImageFont:
    for cand in ([path] if path else []) + FONT_GUESSES:
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            continue
    try:
        import glob
        for cand in sorted(glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)):
            return ImageFont.truetype(cand, size)
    except OSError:
        pass
    return ImageFont.load_default()


def subject_centre(img: Image.Image) -> tuple[float, float]:
    """Normalised (x, y) of the person: face if MediaPipe finds one, else a skin + detail centroid."""
    try:
        import mediapipe as mp  # optional
        with mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as fd:
            res = fd.process(np.asarray(img))
        if res.detections:
            boxes = [d.location_data.relative_bounding_box for d in res.detections]
            x = float(np.mean([b.xmin + b.width / 2 for b in boxes]))
            y = float(np.mean([b.ymin + b.height / 2 for b in boxes]))
            ymin = min(b.ymin for b in boxes)
            return x, min(y + 0.15, max(ymin + 0.25, y))  # bias down a bit so the body shows too
    except Exception:  # noqa: BLE001 - mediapipe missing or failing: fall back
        pass
    small = img.copy()
    small.thumbnail((256, 256))
    a = np.asarray(small).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    skin = (r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) & ((r - np.minimum(g, b)) > 15) & (abs(r - g) > 15)
    grey = a.mean(axis=2)
    edges = np.abs(np.diff(grey, axis=0, prepend=grey[:1])) + np.abs(np.diff(grey, axis=1, prepend=grey[:, :1]))
    weight = skin * 3.0 + edges / (edges.max() + 1e-6)
    hh, ww = weight.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    yy_w = weight * (1.2 - yy / hh * 0.4)  # people tend to sit in the upper-middle
    s = yy_w.sum()
    if s <= 0:
        return 0.5, 0.45
    return float((xx * yy_w).sum() / s / ww), float((yy * yy_w).sum() / s / hh)


def cover(img: Image.Image, tw: int, th: int) -> Image.Image:
    cx, cy = subject_centre(img)
    scale = max(tw / img.width, th / img.height)
    nw, nh = max(tw, round(img.width * scale)), max(th, round(img.height * scale))
    big = img.resize((nw, nh), Image.LANCZOS)  # same scale on both axes: never stretched
    left = int(round(min(max(cx * nw - tw / 2, 0), nw - tw)))
    top = int(round(min(max(cy * nh - th / 2, 0), nh - th)))
    return big.crop((left, top, left + tw, top + th))


def label(canvas: Image.Image, text: str, x: int, y: int, font) -> None:
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((x + 3, y + 4), text, font=font, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    canvas.alpha_composite(shadow)
    ImageDraw.Draw(canvas).text((x, y), text, font=font, fill=(255, 255, 255, 255))


def slide(photo: Path, drawing: Path, font) -> Image.Image:
    out = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    out.paste(cover(load(drawing), W, HALF), (0, 0))
    out.paste(cover(load(photo), W, H - HALF - GAP), (0, HALF + GAP))
    label(out, "One day", 48, 36, font)
    label(out, "Day one", 48, HALF + GAP + 36, font)
    return out.convert("RGB")


def pairs(folder: Path) -> list[tuple[Path, Path]]:
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in EXTS)
    drawings = {p.stem[: -len("_drawing")]: p for p in files if p.stem.endswith("_drawing")}
    out, missing = [], []
    for p in files:
        if p.stem.endswith("_drawing"):
            continue
        (out.append((p, drawings[p.stem])) if p.stem in drawings else missing.append(p.name))
    if missing:
        print("no _drawing for: " + ", ".join(missing), file=sys.stderr)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("photos_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--font", help="path to Caveat (Bold) TTF")
    ap.add_argument("--first-only", action="store_true", help="make only slide 1, for the preview")
    ap.add_argument("--force", action="store_true", help="overwrite existing slides")
    a = ap.parse_args(argv)
    todo = pairs(a.photos_dir)
    if not todo:
        print("no photo/_drawing pairs found", file=sys.stderr)
        return 1
    if a.first_only:
        todo = todo[:1]
    a.out_dir.mkdir(parents=True, exist_ok=True)
    targets = [a.out_dir / f"{i:02d}.png" for i in range(1, len(todo) + 1)]
    if not a.first_only:
        targets.append(a.out_dir / "contact_sheet.png")
    clash = [t.name for t in targets if t.exists()]
    if clash and not a.force:
        print("would overwrite " + ", ".join(clash) + "; ask the owner, then re-run with --force", file=sys.stderr)
        return 1
    font = find_font(a.font, 78)
    slides = []
    for (photo, drawing), target in zip(todo, targets):
        s = slide(photo, drawing, font)
        s.save(target)
        slides.append(s)
        print(target)
    if not a.first_only:
        cols = min(5, len(slides))
        rows = -(-len(slides) // cols)
        tw, th, pad = 270, 338, 12
        sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad) + pad), (30, 30, 30))
        for i, s in enumerate(slides):
            sheet.paste(s.resize((tw, th), Image.LANCZOS), (pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + pad)))
        sheet.save(targets[-1])
        print(targets[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
