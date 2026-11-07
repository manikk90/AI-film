#!/usr/bin/env python3
"""Caveman mode: the studio's token diet. See studio/CAVEMAN.md.

  python3 studio/caveman.py rules <role>               Global + the role's rules from studio/LEARNINGS.md
  python3 studio/caveman.py index FILE...              headings with line numbers and section sizes
  python3 studio/caveman.py section FILE HEADING...    print only the named sections
  python3 studio/caveman.py check projects/<slug> [--scale N] [--all]
                                                       size budgets; exit 1 when a file is over
  python3 studio/caveman.py usage [TRANSCRIPT.jsonl] [--top N]
                                                       tokens per agent run, from Claude Code transcripts

Output is terse on purpose: every printed line lands in an agent's context.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEARNINGS = REPO / "studio" / "LEARNINGS.md"
KB = 1024
# LEARNINGS.md sections each role reads besides Global.
ROLES = {
    "social": ["Social"],
    "researcher": ["Research"],
    "writer": ["Writer"],
    "director": ["Director", "Production"],
    "mann": ["Editor", "Production"],
}
# Budgets in KB of UTF-8 for a short (up to 60 s); long form uses --scale 4.
# Devanagari takes 3 bytes a letter, so a byte budget also keeps Hindi to the exact words.
BUDGETS = [
    ("00-brief.md", 3),
    ("01-trend-board.md", 10),
    ("02-research.md", 10),
    ("FACTS.md", 8),
    ("03-format.md", 10),
    ("04-script/SCRIPT*.md", 14),
    ("04-script/dialogue-lock.md", 3),
    ("05-critique-*.md", 5),
    ("DIGEST.md", 4),
    ("STATUS.md", 8),
    ("06-qc.md", 8),
    ("07-publish-kit.md", 8),
]
HEAD = re.compile(r"^(#{1,6}) (.+?)\s*$")
USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def sections(text):
    """Return the lines and [(level, title, first line, end line)] per heading; fenced code is skipped."""
    lines = text.splitlines()
    heads, fence = [], False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else HEAD.match(line)
        if m:
            heads.append((len(m.group(1)), m.group(2), i))
    out = []
    for k, (level, title, start) in enumerate(heads):
        end = next((s for lv, _, s in heads[k + 1:] if lv <= level), len(lines))
        out.append((level, title, start, end))
    return lines, out


def pick(text, wanted):
    """The named sections (with their subsections). A name matches a heading's start, else any part of it."""
    lines, secs = sections(text)
    parts = []
    for name in wanted:
        key = name.lower().lstrip("# ").strip()
        hit = [s for s in secs if s[1].lower().startswith(key)] or [s for s in secs if key in s[1].lower()]
        if not hit:
            raise SystemExit(f"no heading matches {name!r}")
        _, _, a, b = hit[0]
        parts.append("\n".join(lines[a:b]).rstrip())
    return "\n\n".join(parts)


def size_kb(lines):
    return len("\n".join(lines).encode("utf-8")) / KB


def cmd_rules(role):
    text = LEARNINGS.read_text(encoding="utf-8")
    if role == "all":
        return text.rstrip()
    if role not in ROLES:
        raise SystemExit(f"unknown role {role!r}; use one of: {', '.join(ROLES)}, all")
    return pick(text, ["Global"] + ROLES[role])


def cmd_index(files):
    out = []
    for f in files:
        lines, secs = sections(Path(f).read_text(encoding="utf-8"))
        out.append(f"{f} {size_kb(lines):.1f}KB {len(lines)} lines")
        out += [f"  L{a + 1} {size_kb(lines[a:b]):.1f}KB {'#' * lv} {t}" for lv, t, a, b in secs]
    return "\n".join(out)


def check(project, scale=1.0, show_all=False):
    """Lines to print and the number of files over budget."""
    root = Path(project)
    if not root.is_dir():
        raise SystemExit(f"no project folder: {project}")
    out, over, total = [], 0, 0
    for pattern, kb in BUDGETS:
        for p in sorted(root.glob(pattern)):
            size, limit = p.stat().st_size, kb * scale
            total += size
            bad = size > limit * KB
            over += bad
            if bad or show_all:
                out.append(f"{'OVER' if bad else 'ok':4} {size / KB:5.1f}/{limit:g}KB {p.relative_to(root).as_posix()}")
    out.append(f"{over} over budget; {total / KB:.0f}KB in budgeted files")
    return out, over


def human(n):
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.0f}k" if n >= 1e3 else str(n)


def short(path):
    return str(path).replace(str(REPO) + "/", "")


def read_run(path, main=False):
    """Token use of one transcript: requests, context sent, peak context, output, effort, biggest tool results."""
    reqs, effort, uses, results, images = {}, Counter(), {}, [], 0
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(d, dict) or (main and d.get("isSidechain")):
                continue
            msg = d.get("message") if isinstance(d.get("message"), dict) else {}
            if d.get("type") == "assistant":
                u = msg.get("usage") or {}
                key = msg.get("id") or d.get("requestId") or d.get("uuid")
                if key not in reqs:  # one API request can span several transcript lines
                    reqs[key] = [0, 0]
                    effort[str(d.get("effort") or "-")] += 1
                r = reqs[key]
                r[0] = max(r[0], sum(u.get(k) or 0 for k in USAGE_KEYS))
                r[1] = max(r[1], u.get("output_tokens") or 0)
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        i = b.get("input") or {}
                        target = next((i[k] for k in ("file_path", "command", "pattern", "query", "url", "description")
                                       if i.get(k)), "")
                        uses[b.get("id")] = (b.get("name", "?"), " ".join(short(target).split())[:64])
            elif d.get("type") == "user" and isinstance(msg.get("content"), list):
                for b in msg["content"]:
                    if not (isinstance(b, dict) and b.get("type") == "tool_result"):
                        continue
                    c, n = b.get("content"), 0
                    for x in c if isinstance(c, list) else [{"text": c or ""}]:
                        if isinstance(x, dict) and x.get("type") == "image":
                            images += 1
                        elif isinstance(x, dict):
                            n += len(str(x.get("text", "")).encode("utf-8"))
                    results.append((n,) + uses.get(b.get("tool_use_id"), ("?", "")))
    sent = [r[0] for r in reqs.values()]
    return {"requests": len(reqs), "sent": sum(sent), "peak": max(sent, default=0),
            "output": sum(r[1] for r in reqs.values()), "effort": effort.most_common(1)[0][0] if effort else "-",
            "images": images, "results": results}


def runs(transcript):
    """The main session and its subagents, as (label, path, is_main)."""
    out = [("main session", transcript, True)]
    for p in sorted(glob.glob(str(Path(transcript).with_suffix("")) + "/subagents/*.jsonl"), key=os.path.getmtime):
        meta = Path(p[:-len(".jsonl")] + ".meta.json")
        info = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
        label = " · ".join(x for x in (info.get("agentType"), info.get("description")) if x) or Path(p).stem
        out.append((label, p, False))
    return out


def usage(transcript, top=8):
    rows, biggest = [], []
    for label, path, main in runs(transcript):
        r = read_run(path, main)
        rows.append((label, r))
        biggest += [(n, label.split(" · ")[0], tool, target) for n, tool, target in r["results"]]
    w = min(44, max(len(label) for label, _ in rows))
    out = [f"{'run':{w}} {'req':>4} {'sent':>6} {'peak':>5} {'out':>5} effort img"]
    for label, r in rows:
        out.append(f"{label[:w]:{w}} {r['requests']:>4} {human(r['sent']):>6} {human(r['peak']):>5} "
                   f"{human(r['output']):>5} {r['effort']:6} {r['images']:>3}")
    tot = [sum(r[k] for _, r in rows) for k in ("requests", "sent", "output")]
    out.append(f"{'total':{w}} {tot[0]:>4} {human(tot[1]):>6} {'':>5} {human(tot[2]):>5}")
    out.append("sent = context tokens per request, summed (cache reads included); out includes thinking.")
    if top:
        out.append("biggest tool results:")
        out += [f"  {n / KB:6.1f}KB {who} {tool} {target}" for n, who, tool, target in sorted(biggest, reverse=True)[:top]]
    return "\n".join(out)


def newest_transcript():
    files = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
    if not files:
        raise SystemExit("no Claude Code transcript under ~/.claude/projects")
    return max(files, key=os.path.getmtime)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rules").add_argument("role")
    sub.add_parser("index").add_argument("files", nargs="+")
    s = sub.add_parser("section")
    s.add_argument("file")
    s.add_argument("headings", nargs="+")
    c = sub.add_parser("check")
    c.add_argument("project")
    c.add_argument("--scale", type=float, default=1.0, help="multiply every budget (long form: 4)")
    c.add_argument("--all", action="store_true", help="list files inside budget too")
    u = sub.add_parser("usage")
    u.add_argument("transcript", nargs="?")
    u.add_argument("--top", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "rules":
        print(cmd_rules(a.role))
    elif a.cmd == "index":
        print(cmd_index(a.files))
    elif a.cmd == "section":
        print(pick(Path(a.file).read_text(encoding="utf-8"), a.headings))
    elif a.cmd == "check":
        lines, over = check(a.project, a.scale, a.all)
        print("\n".join(lines))
        return 1 if over else 0
    else:
        print(usage(a.transcript or newest_transcript(), a.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
