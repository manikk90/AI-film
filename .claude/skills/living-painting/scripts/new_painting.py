#!/usr/bin/env python3
"""Start a living-painting project from the template, with the preset's brief at the top of the page.

    python3 .claude/skills/living-painting/scripts/new_painting.py <slug> <preset|custom> [--scene "..."] [--medium "..."]
    python3 .claude/skills/living-painting/scripts/new_painting.py --list

Writes projects/<slug>/painting.html (the template, its studio paths fixed for that folder) and projects/<slug>/brief.json
(scene, medium, action, motion). Refuses to overwrite an existing painting.html unless --force.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parents[2]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slug", nargs="?")
    ap.add_argument("preset", nargs="?")
    ap.add_argument("--scene")
    ap.add_argument("--medium")
    ap.add_argument("--action")
    ap.add_argument("--motion")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--root", default=str(REPO / "projects"))
    a = ap.parse_args(argv)
    presets = {k: v for k, v in json.loads((HERE / "presets.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
    if a.list or not a.slug:
        for k, v in presets.items():
            print(f"{k:18s} {v['name']}: {v['scene']}")
        return 0
    if a.preset == "custom":
        brief = {"name": "custom", "scene": a.scene or "", "medium": a.medium or "", "action": a.action or "", "motion": a.motion or ""}
        if not (brief["scene"] and brief["medium"]):
            sys.exit("custom needs --scene and --medium")
    elif a.preset in presets:
        brief = dict(presets[a.preset])
        for k in ("scene", "medium", "action", "motion"):
            if getattr(a, k):
                brief[k] = getattr(a, k)
    else:
        sys.exit(f"unknown preset {a.preset!r}; --list shows them")
    out = Path(a.root) / a.slug
    page = out / "painting.html"
    if page.exists() and not a.force:
        sys.exit(f"{page} exists; ask the owner, then pass --force")
    out.mkdir(parents=True, exist_ok=True)
    studio = os.path.relpath(REPO / "studio", out).replace(os.sep, "/")
    html = (HERE / "template.html").read_text(encoding="utf-8").replace("__STUDIO__", studio)
    head = "<!--\n  BRIEF (" + brief["name"] + ")\n" + "".join(f"  {k}: {brief[k]}\n" for k in ("scene", "medium", "action", "motion")) + "-->\n"
    page.write_text(html.replace("<!doctype html>\n", "<!doctype html>\n" + head, 1), encoding="utf-8")
    (out / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
