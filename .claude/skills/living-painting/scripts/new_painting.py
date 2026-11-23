#!/usr/bin/env python3
"""Start a living-painting project from the template, with the preset's brief at the top of the page.

    python3 .claude/skills/living-painting/scripts/new_painting.py <slug> <preset|custom> [--scene "..."] [--medium "..."]
                                                              [--style <style or preset>]
    python3 .claude/skills/living-painting/scripts/new_painting.py --list          # presets (scene + look)
    python3 .claude/skills/living-painting/scripts/new_painting.py --list-styles   # looks only (styles.json + presets)

Style and scene are separate: the preset (or custom --scene/--action) gives what happens, --style gives how it looks
(medium, motion) and which engine draws it (canvas_kit painting, or voxel_kit 3D). Any preset is also a style.
Writes projects/<slug>/painting.html (the engine's template, its studio paths fixed for that folder) and
projects/<slug>/brief.json. Refuses to overwrite an existing painting.html unless --force.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parents[2]


def load(path: Path) -> dict:
    return {k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items() if not k.startswith("_")}


def all_styles() -> dict:
    """Looks a page can take: styles.json, then every preset's medium and motion (a preset is also a style)."""
    out = {k: dict(v, engine=v.get("engine", "canvas")) for k, v in load(HERE / "styles.json").items()}
    for k, v in load(HERE / "presets.json").items():
        out.setdefault(k, {"name": v["name"], "medium": v["medium"], "motion": v["motion"], "engine": "canvas"})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slug", nargs="?")
    ap.add_argument("preset", nargs="?")
    ap.add_argument("--scene")
    ap.add_argument("--medium")
    ap.add_argument("--action")
    ap.add_argument("--motion")
    ap.add_argument("--style", help="a style from styles.json or any preset: replaces the look, keeps the scene")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--list-styles", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--root", default=str(REPO / "projects"))
    a = ap.parse_args(argv)
    presets = load(HERE / "presets.json")
    styles = all_styles()
    if a.list_styles:
        for k, v in styles.items():
            print(f"{k:18s} {v['name']} [{v.get('engine', 'canvas')}]")
        return 0
    if a.list or not a.slug:
        for k, v in presets.items():
            print(f"{k:18s} {v['name']}: {v['scene']}")
        return 0
    if a.preset == "custom":
        brief = {"name": "custom", "scene": a.scene or "", "medium": a.medium or "", "action": a.action or "", "motion": a.motion or ""}
        if not (brief["scene"] and (brief["medium"] or a.style)):
            sys.exit("custom needs --scene and --medium (or --style)")
    elif a.preset in presets:
        brief = dict(presets[a.preset])
        for k in ("scene", "medium", "action", "motion"):
            if getattr(a, k):
                brief[k] = getattr(a, k)
    else:
        sys.exit(f"unknown preset {a.preset!r}; --list shows them")
    if a.style:
        if a.style not in styles:
            sys.exit(f"unknown style {a.style!r}; --list-styles shows them")
        st = styles[a.style]
        brief.update({"name": f"{brief['name']} as {st['name']}", "style": a.style, "medium": st["medium"],
                      "motion": st["motion"], "engine": st.get("engine", "canvas")})
        for k in ("medium", "motion"):  # an explicit flag still wins
            if getattr(a, k):
                brief[k] = getattr(a, k)
    brief.setdefault("engine", "canvas")
    out = Path(a.root) / a.slug
    page, brief_path = out / "painting.html", out / "brief.json"
    clash = [p for p in (page, brief_path) if p.exists()]
    if clash and not a.force:
        sys.exit(f"{', '.join(map(str, clash))} exists; ask the owner, then pass --force")
    out.mkdir(parents=True, exist_ok=True)
    studio = os.path.relpath(REPO / "studio", out).replace(os.sep, "/")
    template = HERE / ("template_voxel.html" if brief["engine"] == "voxel" else "template.html")
    html = template.read_text(encoding="utf-8").replace("__STUDIO__", studio)
    head = "<!--\n  BRIEF (" + brief["name"] + ")\n" + "".join(f"  {k}: {brief[k]}\n" for k in ("scene", "medium", "action", "motion")) + "-->\n"
    page.write_text(html.replace("<!doctype html>\n", "<!doctype html>\n" + head, 1), encoding="utf-8")
    brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
