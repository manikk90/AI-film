"""CLI for persistent manual production workflows."""

import argparse
import json
import subprocess
import sys

from .core import ProductionError, add_asset, audit, init_project, read_json, review_breakdown, set_plan
from .portable import export_shot, import_take, review_take


def parser():
    root = argparse.ArgumentParser(prog="aifilm", description="Portable screenplay-to-video production records")
    commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Preserve a UTF-8 screenplay and register every nonblank source line")
    init.add_argument("screenplay")
    init.add_argument("project")
    asset = commands.add_parser("add-asset", help="Copy and register an immutable image reference")
    asset.add_argument("project")
    asset.add_argument("id")
    asset.add_argument("kind", choices=["character", "costume", "location", "prop", "keyframe"])
    asset.add_argument("file")
    asset.add_argument("--description", required=True)
    asset.add_argument("--derived-from", nargs="*", default=[])
    plan = commands.add_parser("set-plan", help="Validate and version an assistant-authored production plan")
    plan.add_argument("project")
    plan.add_argument("file")
    breakdown = commands.add_parser("review-breakdown", help="Record an independent original-screenplay coverage review")
    breakdown.add_argument("project")
    breakdown.add_argument("--reviewer", required=True)
    breakdown.add_argument("--evidence", required=True)
    export = commands.add_parser("export-shot", help="Export a manual input bundle; does not call providers")
    export.add_argument("project")
    export.add_argument("shot")
    export.add_argument("destination")
    export.add_argument("--profile", required=True)
    take = commands.add_parser("import-take", help="Validate and attach an externally generated video")
    take.add_argument("project")
    take.add_argument("shot")
    take.add_argument("file")
    take.add_argument("--bundle", required=True)
    take.add_argument("--tool", required=True)
    take.add_argument("--model", required=True)
    review = commands.add_parser("review-take", help="Record evidence for every beat and acceptance criterion")
    review.add_argument("project")
    review.add_argument("take")
    review.add_argument("file")
    check = commands.add_parser("audit", help="Report missing/stale/unreviewed work; exit 1 until complete")
    check.add_argument("project")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            result = init_project(args.screenplay, args.project)
        elif args.command == "add-asset":
            result = add_asset(args.project, args.id, args.kind, args.file, args.description, args.derived_from)
        elif args.command == "set-plan":
            result = set_plan(args.project, read_json(args.file))
        elif args.command == "review-breakdown":
            result = review_breakdown(args.project, args.reviewer, args.evidence)
        elif args.command == "export-shot":
            result = export_shot(args.project, args.shot, args.destination, read_json(args.profile))
        elif args.command == "import-take":
            result = import_take(args.project, args.shot, args.file, args.bundle, args.tool, args.model)
        elif args.command == "review-take":
            result = review_take(args.project, args.take, read_json(args.file))
        else:
            result = audit(args.project)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if args.command == "audit" and not result["complete"] else 0
    except (ProductionError, OSError, KeyError, TypeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
