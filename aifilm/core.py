"""Persistent production records and conservative completion gates.

This module does not call a generative model or infer visual correctness.
An assistant authors plans; a reviewer supplies evidence after watching takes.
"""

import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class ProductionError(ValueError):
    pass


ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")
HEADING = re.compile(r"^(?:\.?\s*(?:INT\.?/EXT\.?|EXT\.?/INT\.?|INT\.|EXT\.|I/E\.)\s|SCENE\s+\d+\b)", re.I)
ASSET_KINDS = {"character", "costume", "location", "prop", "keyframe"}
SHOT_FIELDS = {
    "id", "scene_id", "beat_ids", "asset_ids", "input_asset_ids", "duration_seconds",
    "aspect_ratio", "visual_description", "action", "camera", "lighting", "audio",
    "start_state", "end_state", "acceptance_criteria",
}


def require(condition, message):
    if not condition:
        raise ProductionError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProductionError("Cannot read JSON {}: {}".format(path, exc)) from exc


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".write-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def identifier(value):
    require(isinstance(value, str) and ID.fullmatch(value), "Invalid ID: {!r}".format(value))
    return value


def nonempty(value, name):
    require(isinstance(value, str) and bool(value.strip()), name + " must be a nonempty string")


def string_list(value, name, allow_empty=False):
    require(isinstance(value, list) and (allow_empty or bool(value)), name + " must be a list")
    require(all(isinstance(v, str) and v.strip() for v in value), name + " needs nonempty strings")
    require(len(set(value)) == len(value), name + " contains duplicates")


def inside(root, relative):
    require(isinstance(relative, str) and not Path(relative).is_absolute(), "Expected relative project path")
    root = Path(root).resolve()
    target = (root / relative).resolve()
    require(root in target.parents, "Path escapes project: " + relative)
    return target


def source_units(text):
    scenes, units = [], []
    scene_id = None
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        heading = bool(HEADING.match(line.strip()))
        if heading:
            scene_id = "SC{:03d}".format(len(scenes) + 1)
            scenes.append({"id": scene_id, "heading": line, "line": number})
        # Preamble remains accounted for; it must not quietly become a scene.
        units.append({"id": "U{:05d}".format(number), "line": number, "text": line,
                      "scene_id": scene_id, "kind": "heading" if heading else "content"})
    require(bool(scenes), "No scene headings found. Use INT., EXT., I/E., or SCENE 1 headings.")
    return scenes, units


def init_project(screenplay, root):
    root = Path(root)
    require(not root.exists(), "Project destination already exists")
    data = Path(screenplay).read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProductionError("Screenplay must be UTF-8 plain text; convert PDF/DOCX first") from exc
    scenes, units = source_units(text)
    root.mkdir(parents=True)
    (root / "screenplay.txt").write_bytes(data)
    state = {"schema_version": 1, "created_at": now(),
             "source": {"path": "screenplay.txt", "sha256": digest(data)},
             "scenes": scenes, "units": units, "assets": {},
             "plan": {"treatment": "", "decisions": [], "beats": [], "shots": [], "preamble_unit_ids": []},
             "plan_history": [], "breakdown_review": None, "takes": [], "reviews": []}
    write_json(root / "project.json", state)
    return state


def load_project(root):
    state = read_json(Path(root) / "project.json")
    require(isinstance(state, dict) and state.get("schema_version") == 1, "Unsupported project schema")
    source = inside(root, state["source"]["path"])
    require(file_hash(source) == state["source"]["sha256"], "Original screenplay changed; create a new project revision")
    scenes, units = source_units(source.read_bytes().decode("utf-8-sig"))
    require(scenes == state["scenes"] and units == state["units"], "Source register differs from original screenplay")
    return state


@contextlib.contextmanager
def project_lock(root):
    lock = Path(root) / ".production.lock"
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ProductionError("Project is busy. Recover a stale .production.lock only after checking its process") from exc
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def save(root, state):
    write_json(Path(root) / "project.json", state)


def probe_media(path):
    require(shutil.which("ffprobe") is not None, "ffprobe is required for media validation; install FFmpeg")
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(Path(path).resolve())],
                            capture_output=True, text=True, timeout=60)
    require(result.returncode == 0, "Media could not be decoded by ffprobe")
    info = json.loads(result.stdout)
    streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    require(bool(streams), "No video/image stream found")
    stream = streams[0]
    return {"width": int(stream.get("width", 0)), "height": int(stream.get("height", 0)),
            "duration_seconds": float(info.get("format", {}).get("duration", stream.get("duration", 0))),
            "codec": stream.get("codec_name", "unknown")}


def add_asset(root, asset_id, kind, source, description, derived_from=None):
    identifier(asset_id)
    require(kind in ASSET_KINDS, "Unknown asset kind")
    nonempty(description, "description")
    derived_from = derived_from or []
    string_list(derived_from, "derived_from", allow_empty=True)
    source = Path(source)
    require(source.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}, "Assets must be PNG, JPEG, or WebP")
    with project_lock(root):
        state = load_project(root)
        require(asset_id not in state["assets"], "Asset ID is immutable; use a new versioned ID")
        require(set(derived_from) <= set(state["assets"]), "Unknown derived_from asset")
        metadata = probe_media(source)
        require(metadata["width"] > 0 and metadata["height"] > 0, "Invalid image dimensions")
        relative = "assets/{}{}".format(asset_id, source.suffix.lower())
        target = inside(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        asset = {"id": asset_id, "kind": kind, "path": relative, "sha256": file_hash(target),
                 "description": description, "derived_from": derived_from, "media": metadata}
        state["assets"][asset_id] = asset
        save(root, state)
        return asset


def keyed(items, name):
    require(isinstance(items, list), name + " must be a list")
    result = {}
    for item in items:
        require(isinstance(item, dict), name + " entries must be objects")
        item_id = identifier(item.get("id"))
        require(item_id not in result, "Duplicate " + name + " ID: " + item_id)
        result[item_id] = item
    return result


def validate_plan(state, plan):
    require(isinstance(plan, dict), "Plan must be an object")
    require(set(plan) == {"treatment", "decisions", "beats", "shots", "preamble_unit_ids"}, "Unexpected/missing plan fields")
    nonempty(plan["treatment"], "treatment")
    require(isinstance(plan["decisions"], list), "decisions must be a list")
    for decision in plan["decisions"]:
        require(isinstance(decision, dict) and set(decision) == {"description", "basis", "status"}, "Invalid decision record")
        nonempty(decision["description"], "decision description")
        require(decision["basis"] in {"screenplay", "inferred", "human"}, "Invalid decision basis")
        require(decision["status"] in {"resolved", "needs_creative_decision"}, "Invalid decision status")
    scenes = {s["id"] for s in state["scenes"]}
    units = {u["id"]: u for u in state["units"]}
    string_list(plan["preamble_unit_ids"], "preamble_unit_ids", allow_empty=True)
    require(set(plan["preamble_unit_ids"]) <= {u["id"] for u in state["units"] if u["scene_id"] is None},
            "Only pre-heading source units can be classified as preamble")
    beats = keyed(plan["beats"], "beat")
    for beat in beats.values():
        require(set(beat) == {"id", "scene_id", "source_unit_ids", "description", "kind"}, "Unexpected/missing beat fields")
        require(beat["scene_id"] in scenes, "Unknown beat scene")
        require(beat["kind"] in {"action", "dialogue", "context"}, "Invalid beat kind")
        nonempty(beat["description"], "beat description")
        string_list(beat["source_unit_ids"], "source_unit_ids")
        for unit_id in beat["source_unit_ids"]:
            require(unit_id in units and units[unit_id]["kind"] == "content", "Unknown/non-content source unit: " + unit_id)
            require(units[unit_id]["scene_id"] == beat["scene_id"], "Beat source crosses scenes")
    shots = keyed(plan["shots"], "shot")
    for shot in shots.values():
        require(set(shot) == SHOT_FIELDS, "Unexpected/missing shot fields: " + shot["id"])
        require(shot["scene_id"] in scenes, "Unknown shot scene")
        string_list(shot["beat_ids"], "beat_ids")
        for beat_id in shot["beat_ids"]:
            require(beat_id in beats and beats[beat_id]["scene_id"] == shot["scene_id"], "Unknown or cross-scene shot beat")
        for name in ("asset_ids", "input_asset_ids"):
            string_list(shot[name], name, allow_empty=True)
            require(set(shot[name]) <= set(state["assets"]), "Unknown shot asset")
        require(set(shot["input_asset_ids"]) <= set(shot["asset_ids"]), "Input assets must also be shot dependencies")
        duration = shot["duration_seconds"]
        require(isinstance(duration, (int, float)) and not isinstance(duration, bool) and 0 < duration <= 3600,
                "duration_seconds must be positive and at most 3600")
        require(isinstance(shot["aspect_ratio"], str) and re.fullmatch(r"[1-9]\d*:[1-9]\d*", shot["aspect_ratio"]), "Invalid aspect ratio")
        for field in ("visual_description", "action", "camera", "lighting", "audio", "start_state", "end_state"):
            nonempty(shot[field], field)
        string_list(shot["acceptance_criteria"], "acceptance_criteria")
    return plan


def set_plan(root, plan):
    with project_lock(root):
        state = load_project(root)
        validate_plan(state, plan)
        if state["plan"] != plan:
            state["plan_history"].append({"saved_at": now(), "plan": state["plan"]})
            state["plan"] = plan
            state["breakdown_review"] = None
            save(root, state)
        return audit(root, state)


def asset_closure(state, ids):
    found, visiting = set(), set()

    def visit(asset_id):
        require(asset_id in state["assets"], "Unknown asset: " + asset_id)
        require(asset_id not in visiting, "Cyclic asset provenance")
        if asset_id in found:
            return
        visiting.add(asset_id)
        for parent in state["assets"][asset_id]["derived_from"]:
            visit(parent)
        visiting.remove(asset_id)
        found.add(asset_id)
    for asset_id in ids:
        visit(asset_id)
    return found


def shot_by_id(state, shot_id):
    shot = next((s for s in state["plan"]["shots"] if s["id"] == shot_id), None)
    require(shot is not None, "Unknown shot: " + shot_id)
    return shot


def shot_fingerprint(state, shot):
    beat_map = {b["id"]: b for b in state["plan"]["beats"]}
    ordered = state["plan"]["shots"]
    index = next(i for i, value in enumerate(ordered) if value["id"] == shot["id"])
    neighbors = []
    for adjacent in (index - 1, index + 1):
        if 0 <= adjacent < len(ordered):
            neighbor = ordered[adjacent]
            neighbors.append({"id": neighbor["id"], "start_state": neighbor["start_state"],
                              "end_state": neighbor["end_state"]})
    return fingerprint({"source": state["source"]["sha256"], "shot": shot,
                        "treatment": state["plan"]["treatment"], "decisions": state["plan"]["decisions"],
                        "adjacent_boundaries": neighbors,
                        "beats": [beat_map[b] for b in shot["beat_ids"]],
                        "assets": [state["assets"][a] for a in sorted(asset_closure(state, shot["asset_ids"]))]})


def verify_assets(root, state, ids):
    for asset_id in asset_closure(state, ids):
        asset = state["assets"][asset_id]
        require(file_hash(inside(root, asset["path"])) == asset["sha256"], "Asset modified: " + asset_id)


def coverage(state):
    plan = state["plan"]
    mapped = {u for b in plan["beats"] for u in b["source_unit_ids"]} | set(plan["preamble_unit_ids"])
    missing_units = [u["id"] for u in state["units"] if u["kind"] == "content" and u["id"] not in mapped]
    shot_beats = {b for s in plan["shots"] for b in s["beat_ids"]}
    missing_beats = [b["id"] for b in plan["beats"] if b["id"] not in shot_beats]
    shot_scenes = {s["scene_id"] for s in plan["shots"]}
    missing_scenes = [s["id"] for s in state["scenes"] if s["id"] not in shot_scenes]
    return {"unmapped_source_units": missing_units, "unplanned_beats": missing_beats, "unplanned_scenes": missing_scenes}


def review_breakdown(root, reviewer, evidence):
    nonempty(reviewer, "reviewer")
    nonempty(evidence, "evidence")
    with project_lock(root):
        state = load_project(root)
        validate_plan(state, state["plan"])
        require(not any(coverage(state).values()), "Cannot accept breakdown with missing coverage")
        state["breakdown_review"] = {"plan_sha256": fingerprint(state["plan"]), "reviewer": reviewer,
                                     "evidence": evidence, "reviewed_at": now()}
        save(root, state)
        return state["breakdown_review"]


def audit(root, state=None):
    state = state or load_project(root)
    plan = state["plan"]
    if plan["treatment"]:
        validate_plan(state, plan)
    result = coverage(state)
    result["unresolved_decisions"] = [d["description"] for d in plan["decisions"] if d["status"] != "resolved"]
    review = state["breakdown_review"]
    result["breakdown_review_current"] = bool(review and review["plan_sha256"] == fingerprint(plan))
    result["shots"] = []
    accepted_beats = set()
    for shot in plan["shots"]:
        status, problems = "missing", []
        try:
            verify_assets(root, state, shot["asset_ids"])
        except (ProductionError, OSError) as exc:
            problems.append(str(exc))
        current = shot_fingerprint(state, shot)
        takes = [t for t in state["takes"] if t["shot_id"] == shot["id"]]
        valid_takes = [t for t in takes if t["shot_sha256"] == current]
        if takes:
            status = "stale" if not valid_takes else "review_required"
        take_problems = []
        for take in valid_takes:
            reviews = [r for r in state["reviews"] if r["take_id"] == take["id"]]
            if not reviews or not reviews[-1]["accepted"]:
                continue
            try:
                require(file_hash(inside(root, take["path"])) == take["sha256"], "Accepted take modified: " + take["id"])
                if not problems:
                    status = "accepted"
                    accepted_beats.update(shot["beat_ids"])
                    break
            except (ProductionError, OSError) as exc:
                take_problems.append(str(exc))
        if status != "accepted":
            problems.extend(take_problems)
        if problems:
            status = "invalid_media"
        result["shots"].append({"id": shot["id"], "status": status, "problems": problems})
    result["unverified_beats"] = [b["id"] for b in plan["beats"] if b["id"] not in accepted_beats]
    result["complete"] = bool(plan["shots"]) and result["breakdown_review_current"] and not any([
        result["unmapped_source_units"], result["unplanned_beats"], result["unplanned_scenes"],
        result["unresolved_decisions"], result["unverified_beats"],
        [s for s in result["shots"] if s["status"] != "accepted"],
    ])
    result["scope"] = "Recorded coverage and reviewer attestations; not a guarantee of visual correctness"
    return result
