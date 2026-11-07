"""`python3 -m aifilm.editor` (alias `mann`): Mann, the AI video editor's command line.

Flow: doctor -> ingest -> transcribe -> assets -> suggest -> [owner: approve-style, lock-script]
-> autocut (draft EDL) -> Mann refines -> storyboard -> [owner: approve] -> render -> qc -> deliver.
Corrections: status tells whole vs part; part -> storyboard --changed + preview-part -> approve --clips -> render.
Style lab: fetch -> analyze-style -> publish-style.
"""

import argparse
import json
import sys
from pathlib import Path

from ..core import ProductionError
from . import craft as C
from . import edl as E
from . import engine as G
from . import media as M
from . import render as R
from . import style as S
from . import tools as T


def parser():
    root = argparse.ArgumentParser(prog="mann", description="Mann: AI video editor (FFmpeg, Whisper, yt-dlp, Hyperframes)")
    c = root.add_subparsers(dest="command", required=True)
    c.add_parser("doctor", help="Check which editing tools are installed")
    p = c.add_parser("ingest", help="Copy the owner's raw files into <edit>/raw and record probe + sha256")
    p.add_argument("edit")
    p.add_argument("files", nargs="+")
    p.add_argument("--link", action="store_true", help="Symlink instead of copying (large footage)")
    p = c.add_parser("transcribe", help="Whisper transcript + word-timed phone captions")
    p.add_argument("media")
    p.add_argument("out_dir")
    p.add_argument("--model", default="small")
    p.add_argument("--language", help="e.g. hi, en; omit to auto-detect")
    p.add_argument("--max-words", type=int, default=4)
    p = c.add_parser("scenes", help="List detected cuts in a video")
    p.add_argument("video")
    p.add_argument("--threshold", type=float, default=0.3)
    p = c.add_parser("validate", help="Validate <edit>/edl.json and print the timeline")
    p.add_argument("edit")
    p = c.add_parser("assets", help="Analyse every ingested file (shots, motion, colour, audio, beats); cached by hash")
    p.add_argument("edit")
    p = c.add_parser("suggest", help="Smart engine: best styles, unique ideas, hooks and problems for this footage")
    p.add_argument("edit")
    p.add_argument("--aspect", choices=sorted(G.SIZES))
    p = c.add_parser("autocut", help="Draft edl.json from the footage in a catalog style")
    p.add_argument("edit")
    p.add_argument("--style", required=True)
    p.add_argument("--seconds", type=float)
    p.add_argument("--aspect", choices=sorted(G.SIZES))
    p = c.add_parser("beats", help="Tempo and beat times of a music file")
    p.add_argument("audio")
    p = c.add_parser("library-scan", help="Index a reusable music/SFX/LUT/overlay folder")
    p.add_argument("folder")
    p = c.add_parser("styles", help="List the 50 catalog styles")
    p.add_argument("--family")
    p = c.add_parser("craft", help="The craft rulebook: cuts, continuity, eyelines, composition, typography, colour, safe zones, sound...")
    p.add_argument("--domain")
    p = c.add_parser("craft-check", help="Automatic craft checks on <edit>/edl.json (also run by storyboard and qc)")
    p.add_argument("edit")
    p.add_argument("--no-contrast", action="store_true", help="Skip sampling frames for text contrast")
    c.add_parser("pairings", help="Font pairings (Devanagari support verified)")
    c.add_parser("themes", help="Colour themes")
    p = c.add_parser("fonts-install", help="Fetch open-licensed fonts from npm (@fontsource), merge Latin+Devanagari, install")
    p.add_argument("families", nargs="*")
    p.add_argument("--pairing")
    p.add_argument("--weights", default="400,700")
    p = c.add_parser("motion", help="Motion-graphics templates: list, render, still, add (canvas + Playwright; cloud and laptop)")
    p.add_argument("action", choices=["list", "render", "still", "add"])
    p.add_argument("template", nargs="?")
    p.add_argument("target", nargs="?", help="render/still: output path; add: the edit folder")
    p.add_argument("--size", default="1080x1920")
    p.add_argument("--duration", type=float)
    p.add_argument("--vars", default="{}", help="JSON of template variables, e.g. '{\"name\": \"Asha\"}'")
    p.add_argument("--theme")
    p.add_argument("--pairing")
    p.add_argument("--at", type=float, default=0.0, help="add: overlay start time in the edit (seconds)")
    p.add_argument("--times", default="0.5,1.5", help="still: comma-separated timecodes")
    p = c.add_parser("footage", help="Archive/stock footage with licences: search, fetch, add (any site incl. movingimagearchive.com), credits")
    p.add_argument("action", choices=["search", "fetch", "add", "credits", "list"])
    p.add_argument("arg1", nargs="?", help="search: query; fetch/add/credits/list: the edit folder")
    p.add_argument("arg2", nargs="?", help="fetch: result number from the last search or a URL; add: the file")
    p.add_argument("--source", action="append", help="search: internet-archive, wikimedia-commons, nasa, pexels (repeatable)")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--source-url", help="add: where the clip came from")
    p.add_argument("--license", help="licence name or URL (e.g. 'CC BY 4.0', 'Public domain', 'movingimagearchive.com licence')")
    p.add_argument("--credit", help="attribution line")
    p.add_argument("--rights", help="override the rights category: " + ", ".join(sorted(["public-domain", "cc-by", "cc-by-sa", "cc-by-nc", "free-license", "owner-licensed"])))
    p.add_argument("--licence-ref", help="owner-licensed: order / invoice / licence id")
    p.add_argument("--noncommercial-ok", action="store_true", help="the owner confirmed this video is non-commercial")
    p = c.add_parser("approve-style", help="Owner decision 1: record the finalised style")
    p.add_argument("edit")
    p.add_argument("slug")
    p.add_argument("--words", required=True)
    p = c.add_parser("lock-script", help="Owner decision 2: lock the script file (its hash is checked before storyboard)")
    p.add_argument("edit")
    p.add_argument("file", help="Path inside the edit folder, e.g. SCRIPT.md")
    p.add_argument("--words", required=True)
    p = c.add_parser("status", help="What still needs the owner: nothing, some parts, or the whole video")
    p.add_argument("edit")
    p = c.add_parser("storyboard", help="Numbered frames + STORYBOARD.md (owner decision 3); --changed/--only for one-part corrections")
    p.add_argument("edit")
    p.add_argument("--two", action="store_true", help="Two frames per clip (start and end)")
    p.add_argument("--only", help="Comma-separated clip ids: a part storyboard")
    p.add_argument("--changed", action="store_true", help="Whole storyboard if a global setting changed, else only the changed clips")
    p = c.add_parser("preview-part", help="Quick 720p video of the corrected part (plus neighbours) for the owner's check")
    p.add_argument("edit")
    p.add_argument("--clips", required=True)
    p = c.add_parser("approve", help="Record the owner's explicit approval (their exact words)")
    p.add_argument("edit")
    p.add_argument("--words", required=True)
    p.add_argument("--clips", help="Approve only these corrected clips (comma-separated)")
    p.add_argument("--final", action="store_true", help="Approve the final cut instead of the storyboard")
    p = c.add_parser("render", help="Render the approved EDL to renders/master.mp4 (+ 720p preview)")
    p.add_argument("edit")
    p.add_argument("--no-preview", action="store_true")
    p.add_argument("--quality", choices=["draft", "standard", "best"], default="standard",
                   help="Encoder speed/quality: draft (fastest), standard (default), best (slowest, smallest files)")
    p = c.add_parser("qc", help="Measure the master against the EDL, editor/rules.json and the style target")
    p.add_argument("edit")
    p.add_argument("--frames", type=float, default=1.5, help="Also export QC frames every N seconds (0 = none)")
    p = c.add_parser("fetch", help="Download a reference video with yt-dlp (for style study)")
    p.add_argument("url")
    p.add_argument("dest")
    p = c.add_parser("analyze-style", help="Break down a reference video's editing style")
    p.add_argument("video")
    p.add_argument("workdir")
    p.add_argument("--name", required=True)
    p.add_argument("--threshold", type=float, default=0.3)
    p.add_argument("--transcript", help="SRT of the reference, for speech rate")
    p = c.add_parser("publish-style", help="Save a finished STYLE_SHEET.md + targets to editor/styles/<slug>/")
    p.add_argument("workdir")
    p.add_argument("slug")
    p = c.add_parser("mg-new", help="Scaffold a Hyperframes motion-graphics composition in <edit>/mg/<name>")
    p.add_argument("edit")
    p.add_argument("name")
    p.add_argument("--resolution", default="portrait")
    p = c.add_parser("mg-render", help="Render <edit>/mg/<name> to a .mov with alpha for an overlay")
    p.add_argument("edit")
    p.add_argument("name")
    p.add_argument("--opaque", action="store_true", help="Render .mp4 without alpha")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        cmd = args.command
        if cmd == "doctor":
            result = T.doctor()
        elif cmd == "ingest":
            result = T.ingest(args.edit, args.files, args.link)
        elif cmd == "transcribe":
            result = T.transcribe(args.media, args.out_dir, args.model, args.language, args.max_words)
        elif cmd == "scenes":
            result = {"cuts": M.scene_cuts(args.video, args.threshold)}
        elif cmd == "validate":
            edl = E.load(args.edit)
            rows, total = E.timeline(edl)
            result = {"total": total, "pace": E.pace(edl), "timeline": rows, "storyboard_approved": E.approved(args.edit, edl)}
        elif cmd == "assets":
            result = G.assets(args.edit)
        elif cmd == "suggest":
            r = G.suggest(args.edit, args.aspect)
            result = {"suggestions": str(Path(args.edit) / "SUGGESTIONS.md"), "recommended": r["recommended"], "experiment": r["experiment"],
                      "problems": r["problems"]}
        elif cmd == "autocut":
            result = G.autocut(args.edit, args.style, args.seconds, args.aspect)
        elif cmd == "beats":
            result = G.beats(args.audio)
        elif cmd == "library-scan":
            result = {"indexed": len(G.library_scan(args.folder))}
        elif cmd == "styles":
            result = [{"slug": s["slug"], "name": s["name"], "family": s["family"], "best_for": s["best_for"]}
                      for s in G.catalog() if not args.family or s["family"] == args.family]
        elif cmd == "craft":
            result = [{"id": r["id"], "domain": r["domain"], "name": r["name"], "check": r["check"], "how": r["how"]} for r in C.rules(args.domain)]
        elif cmd == "craft-check":
            findings = C.check(args.edit, E.load(args.edit), sample_contrast=not args.no_contrast)
            print(json.dumps(findings, indent=2, ensure_ascii=False))
            return 1 if any(f["result"] == "fail" for f in findings) else 0
        elif cmd == "pairings":
            result = C.data()["font_pairings"]
        elif cmd == "themes":
            result = C.data()["colour_themes"]
        elif cmd == "fonts-install":
            from . import fonts as F
            if args.pairing:
                result = F.install_pairing(C.pairing(args.pairing))
            else:
                result = [f for fam in args.families for f in F.install(fam, [int(w) for w in args.weights.split(",")])]
        elif cmd == "motion":
            from . import motion as MO
            if args.action == "list":
                result = [{"name": m["name"], "description": m["description"], "duration": m["duration"], "vars": m["vars"]} for m in MO.templates()]
            else:
                require_args = args.template and args.target
                if not require_args:
                    raise ProductionError("motion {} needs a template and a target".format(args.action))
                variables = json.loads(args.vars)
                if args.action == "add":
                    result = MO.add(args.target, args.template, args.at, args.duration, variables)
                else:
                    size = tuple(int(x) for x in args.size.split("x"))
                    stills = [float(x) for x in args.times.split(",")] if args.action == "still" else None
                    result = MO.render(args.template, args.target, size, args.duration, variables, args.theme, args.pairing, stills=stills)
        elif cmd == "footage":
            from . import footage as FT
            last = Path.home() / ".cache" / "mann" / "last-footage-search.json"
            last.parent.mkdir(parents=True, exist_ok=True)
            if args.action == "search":
                require_q = args.arg1 or ""
                if not require_q:
                    raise ProductionError("footage search needs a query")
                result = FT.search(require_q, args.source, args.limit)
                last.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
                result = {"results": [dict(n=i + 1, **{k: r.get(k) for k in ("source", "title", "rights", "license", "credit", "page", "usable")})
                                      for i, r in enumerate(result["results"])], "errors": result["errors"]}
            elif args.action == "fetch":
                if args.arg2 and args.arg2.isdigit():
                    if not last.exists():
                        raise ProductionError("Run `footage search` first, or pass a URL")
                    picked = json.loads(last.read_text(encoding="utf-8"))["results"][int(args.arg2) - 1]
                    result = FT.fetch(args.arg1, picked, rights=args.rights, licence_ref=args.licence_ref, noncommercial_ok=args.noncommercial_ok)
                else:
                    result = FT.fetch(args.arg1, url=args.arg2, license_text=args.license, credit=args.credit, rights=args.rights,
                                      licence_ref=args.licence_ref, noncommercial_ok=args.noncommercial_ok)
            elif args.action == "add":
                result = FT.add(args.arg1, args.arg2, args.source_url, args.license, args.credit, args.rights, args.licence_ref, args.noncommercial_ok)
            elif args.action == "list":
                path = Path(args.arg1) / "footage.json"
                result = json.loads(path.read_text(encoding="utf-8"))["clips"] if path.exists() else {}
            else:
                result = {"credits": FT.credits(args.arg1, E.load(args.arg1))}
        elif cmd == "approve-style":
            G.style(args.slug)
            result = E.approve_style(args.edit, args.slug, args.words)
        elif cmd == "lock-script":
            result = E.lock_script(args.edit, args.file, args.words)
        elif cmd == "status":
            edl = E.load(args.edit)
            result = E.status(args.edit, edl)
        elif cmd == "storyboard":
            only = [x.strip() for x in args.only.split(",")] if args.only else None
            if args.changed and not only:
                st = E.status(args.edit, E.load(args.edit))
                if st["scope"] == "none":
                    print(json.dumps({"scope": "none", "message": "Nothing changed since the owner's approval"}, indent=2))
                    return 0
                only = st["changed_clips"] if st["scope"] == "part" else None
            rec = E.storyboard(args.edit, 2 if args.two else 1, only)
            name = "part/PART.md" if only else "STORYBOARD.md"
            result = {"scope": rec["scope"], "storyboard": str(Path(args.edit) / "storyboard" / name),
                      "frames": [f["file"] for f in rec["frames"]], "pace": rec["pace"], "changes": rec["changes_since_previous"]}
        elif cmd == "preview-part":
            result = R.preview_part(args.edit, [x.strip() for x in args.clips.split(",")])
        elif cmd == "approve":
            clips = [x.strip() for x in args.clips.split(",")] if args.clips else None
            result = E.approve(args.edit, args.words, kind="final" if args.final else "storyboard", clips=clips)
        elif cmd == "render":
            result = R.render(args.edit, preview=not args.no_preview, quality=args.quality)
        elif cmd == "qc":
            rec = R.qc(args.edit)
            frames = R.contact_frames(args.edit, args.frames) if args.frames else []
            result = {"passed": rec["passed"], "checks": rec["checks"], "qc_frames": len(frames), "report": str(Path(args.edit) / "renders" / "QC.md")}
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if rec["passed"] else 1
        elif cmd == "fetch":
            result = {"file": T.fetch(args.url, args.dest)}
        elif cmd == "analyze-style":
            a = S.analyze(args.video, args.workdir, args.name, args.threshold, args.transcript)
            result = {"draft": str(Path(args.workdir) / "STYLE_SHEET.draft.md"), "targets": S.targets(a), "frames": len(a["frames"])}
        elif cmd == "publish-style":
            result = {"saved": str(S.publish(args.workdir, R.STYLES, args.slug))}
        elif cmd == "mg-new":
            result = {"composition": T.mg_new(args.edit, args.name, args.resolution)}
        elif cmd == "mg-render":
            result = {"file": T.mg_render(args.edit, args.name, alpha=not args.opaque)}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except ProductionError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
