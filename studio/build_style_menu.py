"""Rebuild studio/STYLE_MENU.md from the Lemo-Opuscar library, this repo's draft styles and the imported ready formats.

Run: python3 studio/build_style_menu.py --lemo /path/to/lemo-opuscar
(clone it first: GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/lemomo-ai/lemo-opuscar)
"""
import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ORDER = ["Indian Traditions", "World Folk", "Animation Techniques", "Art Movements", "Internet & Digital", "Cinema Eras"]
GROUPS = ["Animated videos (with engine)", "Animated videos", "Lyric videos", "Trend edits", "Reel formats", "Edit styles", "Motion effects", "Looks"]


def look(md):
    m = re.search(r"^> (.+)$", md.read_text(encoding="utf-8"), re.M)
    s = re.sub(r"\s+", " ", m.group(1).strip()) if m else ""
    return (s[:157] + "…") if len(s) > 160 else s


def cell(s):
    return s.replace("|", "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lemo", required=True, help="path to a lemo-opuscar clone")
    lib_dir = Path(ap.parse_args().lemo) / "styles"
    lib, draft = [], []
    for p in sorted(lib_dir.glob("*/style.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d["slug"] == "my-style" or p.parent.name.startswith("_"):
            continue
        lib.append((d["category_en"], d["en"], d["slug"], look(p.parent / "STYLE.md"), ", ".join(d.get("uses", [])[:3])))
    for p in sorted((REPO / "styles").glob("*/style.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        draft.append((d["category_en"], d["en"], d["slug"], look(p.parent / "STYLE.md"), ", ".join(d.get("uses", [])[:3]), d["hi"]))
    reg = REPO / "studio" / "IMPORTED_SKILLS.json"
    fmt = json.loads(reg.read_text(encoding="utf-8")) if reg.exists() else []
    fp = REPO / "studio" / "formats" / "claude-video-formats.json"
    prompts = json.loads(fp.read_text(encoding="utf-8"))["formats"] if fp.exists() else []
    out = ["# Style menu", "",
           "Every style the studio can pick from, in one place, for the social agent's style suggestions and the director's format brief.", "",
           f"- **Library styles ({len(lib)})**, from [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) `styles/<slug>/`. Each has a demo film and engine code, so these are the reliable, faster picks.",
           f"- **Draft styles ({len(draft)})**, from this repo's [`styles/`](../styles/README.md). Each has a written `STYLE.md` but no engine yet, so it needs more build time and an owner-approved preview.",
           f"- **Ready formats ({len(fmt)})**, the aansh.ai format skills: imported from the owner's Ai-Animation repo, plus the owner's 2026-11-08 specs in `studio/skill_sources/` (all in `studio/IMPORTED_SKILLS.json`). Each is a whole recipe, run as `/<name>` or picked as the format in a studio run, inside `studio/SKILL_HARNESS.md`. They have not been rendered in this repo yet.",
           f"- **Format prompts ({len(prompts)})**, from the \"12 Claude Video Formats\" guide (`studio/formats/`). Each is a one-line prompt (`Format: <name>.`) for `studio/templates/format-prompt.md`. They have a first-try result in the guide, not in this repo.", "",
           "Rebuild this file with `python3 studio/build_style_menu.py --lemo <lemo-opuscar clone>` when either library changes.", "",
           f"## Library styles ({len(lib)}, each with a demo film)", ""]
    cat = None
    for c, en, slug, lk, uses in sorted(lib, key=lambda r: (r[0], r[1])):
        if c != cat:
            cat = c
            out += ["", f"### {c}", "", "| Style | Slug | Look | Good for |", "|---|---|---|---|"]
        out.append(f"| {en} | `{slug}` | {cell(lk)} | {cell(uses)} |")
    out += ["", f"## Draft styles ({len(draft)}, no demo yet)", ""]
    cat = None
    for c, en, slug, lk, uses, hi in sorted(draft, key=lambda r: (ORDER.index(r[0]) if r[0] in ORDER else 99, r[1])):
        if c != cat:
            cat = c
            out += ["", f"### {c}", "", "| Style | हिंदी | Slug | Look | Good for |", "|---|---|---|---|---|"]
        out.append(f"| {en} | {hi} | `{slug}` | {cell(lk)} | {cell(uses)} |")
    out += ["", f"## Ready formats ({len(fmt)}, imported skills)", "",
            "Kind says where the words come from and which gate applies (see `studio/SKILL_HARNESS.md`).", ""]
    grp = None
    for e in sorted(fmt, key=lambda e: (GROUPS.index(e["group"]) if e["group"] in GROUPS else 99, e["title"])):
        if e["group"] != grp:
            grp = e["group"]
            out += ["", f"### {grp}", "", "| Format | Skill | Owner gives | Kind | Checks |", "|---|---|---|---|---|"]
        out.append(f"| {cell(e['title'])} | `/{e['name']}` | {cell(e['input'])} | {e['kind']} | {', '.join(e['flags']) or '-'} |")
    out += ["", f"## Format prompts ({len(prompts)}, from the 12 Claude Video Formats guide)", "",
            "Put `Format: <typed>.` as the last line of `studio/templates/format-prompt.md`. Prefer the nearest library style for a full film.", "",
            "| Format | हिंदी | Slug | Typed | Look | Good for | Nearest |", "|---|---|---|---|---|---|---|"]
    for e in prompts:
        name = e["name"] + ("" if e["in_reel"] else " (not in the guide's reel)")
        out.append(f"| {cell(name)} | {e['hi']} | `{e['slug']}` | {cell(e['typed'])} | {cell(e['look'])} | "
                   f"{cell(', '.join(e['good_for']))} | {', '.join('`' + n + '`' for n in e['nearest'])} |")
    (REPO / "studio" / "STYLE_MENU.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(lib)} library + {len(draft)} draft styles + {len(fmt)} ready formats + {len(prompts)} format prompts")


if __name__ == "__main__":
    main()
