#!/usr/bin/env python3
"""Person matte (and optional body-part mattes and face/pose landmarks) for every frame of a clip, with MediaPipe
Tasks, for skills that put graphics behind the owner, clip patterns to their clothes or hair, or stick doodles to
their face and hands.

    python3 studio/person_matte.py clip.mp4 mattes/ [--fps 30] [--smooth 3] [--parts] [--landmarks] [--video matte.mp4]

Writes:
- mattes/person/00001.png ...   8-bit alpha, 255 = person, at the clip's size, averaged over --smooth frames so the
                                edge does not boil
- with --parts: mattes/hair/, mattes/clothes/, mattes/skin/ (body + face skin), same format
- with --landmarks: mattes/landmarks.json: per frame, 478 face points and 33 pose points in 0..1 image coordinates
  (null when nobody is found). Smooth them over a few frames before drawing on them.
- with --video: a grey person-matte video
A canvas page loads the PNGs as images and composites: background, graphics, then the original frame masked by the
matte. The owner's face is never filtered; the matte only cuts.

Model: selfie_multiclass_256x256 (classes: background, hair, body skin, face skin, clothes, others), plus
face_landmarker and pose_landmarker_full for --landmarks. They download once from storage.googleapis.com into
~/.cache/aifilm/mediapipe/. Needs mediapipe >= 0.10 (Tasks API), numpy, Pillow and FFmpeg.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np

BASE = "https://storage.googleapis.com/mediapipe-models/"
MODELS = {
    "seg": BASE + "image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
    "face": BASE + "face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
    "pose": BASE + "pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
}
CACHE = Path.home() / ".cache" / "aifilm" / "mediapipe"
HAIR, BODY, FACE, CLOTHES = 1, 2, 3, 4


def model(key: str) -> str:
    path = CACHE / MODELS[key].rsplit("/", 1)[1]
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(MODELS[key], tmp)
        tmp.rename(path)
    return str(path)


def frames(path: str, fps: float):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout
    w, h = map(int, out.strip().split(",")[:2])
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps}", "-f", "rawvideo", "-pix_fmt",
                          "rgb24", "-"], stdout=subprocess.PIPE)
    size = w * h * 3
    while True:
        buf = p.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    p.wait()


def to_png(a: np.ndarray, path: Path) -> None:
    from PIL import Image
    Image.fromarray((np.clip((a - 0.35) / 0.3, 0, 1) * 255).astype(np.uint8)).save(path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("clip")
    ap.add_argument("outdir")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--smooth", type=int, default=3)
    ap.add_argument("--parts", action="store_true")
    ap.add_argument("--landmarks", action="store_true")
    ap.add_argument("--video")
    a = ap.parse_args(argv)
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
    except ImportError:
        sys.exit("mediapipe missing: pip install mediapipe pillow")
    out = Path(a.outdir)
    layers = ["person"] + (["hair", "clothes", "skin"] if a.parts else [])
    for layer in layers:
        (out / layer).mkdir(parents=True, exist_ok=True)
    Video = vision.RunningMode.VIDEO
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=model("seg")), running_mode=Video, output_confidence_masks=True))
    face = pose = None
    if a.landmarks:
        face = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model("face")), running_mode=Video, num_faces=1))
        pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model("pose")), running_mode=Video, num_poses=1))
    hist: dict[str, list] = {k: [] for k in layers}
    marks, n = [], 0
    for rgb in frames(a.clip, a.fps):
        ts = int(n * 1000 / a.fps)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        conf = [np.squeeze(m.numpy_view()) for m in seg.segment_for_video(img, ts).confidence_masks]
        cur = {"person": 1.0 - conf[0]}
        if a.parts:
            cur |= {"hair": conf[HAIR], "clothes": conf[CLOTHES], "skin": conf[BODY] + conf[FACE]}
        n += 1
        for k, v in cur.items():
            hist[k] = (hist[k] + [v.astype(np.float32)])[-max(1, a.smooth):]
            to_png(np.mean(hist[k], axis=0), out / k / f"{n:05d}.png")
        if a.landmarks:
            fr, pr = face.detect_for_video(img, ts), pose.detect_for_video(img, ts)
            marks.append({
                "face": [[round(p.x, 4), round(p.y, 4)] for p in fr.face_landmarks[0]] if fr.face_landmarks else None,
                "pose": [[round(p.x, 4), round(p.y, 4), round(p.visibility or 0, 2)] for p in pr.pose_landmarks[0]]
                if pr.pose_landmarks else None})
    for task in (seg, face, pose):  # close explicitly: MediaPipe errors if left to the interpreter's shutdown
        if task:
            task.close()
    if a.landmarks:
        json.dump({"fps": a.fps, "frames": marks}, open(out / "landmarks.json", "w"), separators=(",", ":"))
    if a.video:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", str(out / "person" / "%05d.png"),
                        "-pix_fmt", "yuv420p", a.video], check=True)
    print(f"{out}: {n} frames, layers {', '.join(layers)}" + (", landmarks.json" if a.landmarks else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
