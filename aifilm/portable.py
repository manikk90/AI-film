"""Manual tool adapters: compile portable inputs and reconcile reviewed outputs."""

import os
import shutil
import tempfile
from pathlib import Path

from .core import (
    ProductionError, asset_closure, file_hash, fingerprint, identifier, inside,
    load_project, nonempty, now, probe_media, project_lock, read_json, require,
    save, shot_by_id, shot_fingerprint, string_list, validate_plan, verify_assets, write_json,
)


def validate_profile(profile):
    fields = {"name", "input_mode", "max_references", "durations", "aspect_ratios", "verification"}
    require(isinstance(profile, dict) and set(profile) == fields, "Unexpected/missing profile fields")
    nonempty(profile["name"], "profile name")
    require(profile["input_mode"] in {"single-image", "multi-reference", "text"}, "Unknown input mode")
    limit = profile["max_references"]
    require(limit is None or (isinstance(limit, int) and not isinstance(limit, bool) and limit >= 0), "Invalid reference limit")
    require(isinstance(profile["durations"], list) and all(isinstance(d, (int, float)) and not isinstance(d, bool) and d > 0 for d in profile["durations"]), "Invalid durations")
    string_list(profile["aspect_ratios"], "profile aspect_ratios", allow_empty=True)
    verification = profile["verification"]
    require(isinstance(verification, dict), "Profile verification must be an object")
    require(verification.get("status") in {"portable-template", "verified"}, "Invalid profile verification status")
    if verification["status"] == "verified":
        for field in ("tool", "model", "checked_on", "evidence"):
            nonempty(verification.get(field), "verification " + field)
        require(limit is not None and profile["durations"] and profile["aspect_ratios"], "Verified profiles need explicit supported limits")
    return profile


def compile_prompt(shot, profile, assets):
    lines = []
    if profile["input_mode"] != "single-image":
        lines.append("Visual: " + shot["visual_description"])
        lines.extend("Reference {}: {} ({}) — {}".format(i, asset["id"], asset["kind"], asset["description"])
                     for i, asset in enumerate(assets, 1))
    lines.extend(["Action/performance: " + shot["action"], "Camera: " + shot["camera"],
                  "Lighting: " + shot["lighting"], "Audio intent: " + shot["audio"],
                  "Starting state: " + shot["start_state"], "Ending state: " + shot["end_state"]])
    return "\n".join(lines) + "\n"


def export_shot(root, shot_id, destination, profile):
    validate_profile(profile)
    destination = Path(destination).resolve()
    require(not destination.exists(), "Export destination already exists; use a new versioned directory")
    with project_lock(root):
        state = load_project(root)
        validate_plan(state, state["plan"])
        require(not any(d["status"] != "resolved" for d in state["plan"]["decisions"]), "Resolve creative decisions before exporting")
        shot = shot_by_id(state, shot_id)
        inputs = shot["input_asset_ids"]
        mode = profile["input_mode"]
        require(mode != "single-image" or (len(inputs) == 1 and state["assets"][inputs[0]]["kind"] == "keyframe"),
                "Single-image mode needs exactly one composed keyframe")
        require(mode != "text" or not inputs, "Text mode cannot receive images")
        require(mode != "multi-reference" or bool(inputs), "Multi-reference mode needs input assets")
        require(profile["max_references"] is None or len(inputs) <= profile["max_references"], "Too many references for profile")
        require(not profile["durations"] or shot["duration_seconds"] in profile["durations"], "Unsupported duration")
        require(not profile["aspect_ratios"] or shot["aspect_ratio"] in profile["aspect_ratios"], "Unsupported aspect ratio")
        covered = asset_closure(state, inputs)
        require(set(shot["asset_ids"]) <= covered, "References would be dropped. Compose a keyframe with derived_from provenance or change the profile")
        verify_assets(root, state, shot["asset_ids"])
        all_ids = sorted(asset_closure(state, shot["asset_ids"]))
        input_assets = [state["assets"][a] for a in inputs]
        prompt = compile_prompt(shot, profile, input_assets)
        source_ids = {u for beat in state["plan"]["beats"] if beat["id"] in shot["beat_ids"] for u in beat["source_unit_ids"]}
        manifest = {
            "schema_version": 1, "created_at": now(), "source_sha256": state["source"]["sha256"],
            "shot": shot, "shot_sha256": shot_fingerprint(state, shot), "profile": profile,
            "prompt_path": "prompt.txt", "prompt_sha256": fingerprint(prompt),
            "source_units": [u for u in state["units"] if u["id"] in source_ids],
            "reference_order": inputs, "assets": [state["assets"][a] for a in all_ids],
            "status": "exported_not_generated",
            "compatibility": "requires_target_tool_check" if profile["verification"]["status"] == "portable-template" else "profile_validated_requires_output_review",
        }
        manifest["bundle_sha256"] = fingerprint(manifest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".bundle-", dir=str(destination.parent)))
        try:
            (temporary / "assets").mkdir()
            for asset in manifest["assets"]:
                target = inside(temporary, asset["path"])
                shutil.copyfile(inside(root, asset["path"]), target)
                require(file_hash(target) == asset["sha256"], "Reference changed while copying")
            (temporary / "prompt.txt").write_text(prompt, encoding="utf-8")
            write_json(temporary / "manifest.json", manifest)
            (temporary / "RUN_IN_TOOL.md").write_text(
                "# Run this shot\n\n"
                "This is an export, not a generated or accepted video.\n\n"
                "1. Check the exact tool/model supports this profile, image roles, duration, aspect ratio, and audio intent.\n"
                "2. Upload only manifest.reference_order assets, in that order. Other assets are provenance, not extra inputs.\n"
                "3. Copy prompt.txt; set duration/aspect ratio from manifest.shot. Generic reference labels may need the tool's own binding syntax.\n"
                "4. If adapting the prompt or settings, update the shot plan/profile and re-export; keep this bundle immutable.\n"
                "5. Download the clip. Import with this bundle and the actual tool/model names.\n"
                "6. Inspect the full clip and submit timestamped per-beat/per-criterion review evidence.\n\n"
                "No API call, paid generation, or visual approval has occurred.\n", encoding="utf-8")
            require(not destination.exists(), "Export destination appeared during export")
            os.rename(temporary, destination)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        return manifest


def read_bundle(bundle):
    manifest = read_json(Path(bundle) / "manifest.json")
    require(isinstance(manifest, dict) and manifest.get("schema_version") == 1, "Unsupported bundle schema")
    original_hash = manifest.get("bundle_sha256")
    body = {k: v for k, v in manifest.items() if k != "bundle_sha256"}
    require(fingerprint(body) == original_hash, "Bundle manifest changed")
    prompt = inside(bundle, manifest["prompt_path"]).read_text(encoding="utf-8")
    require(fingerprint(prompt) == manifest["prompt_sha256"], "Exported prompt changed; update plan and re-export")
    for asset in manifest["assets"]:
        require(file_hash(inside(bundle, asset["path"])) == asset["sha256"], "Bundle reference changed: " + asset["id"])
    return manifest


def import_take(root, shot_id, source, bundle, tool, model):
    nonempty(tool, "tool")
    nonempty(model, "model")
    source = Path(source)
    require(source.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}, "Unsupported video container")
    manifest = read_bundle(bundle)
    with project_lock(root):
        state = load_project(root)
        shot = shot_by_id(state, shot_id)
        require(manifest["shot"]["id"] == shot_id and manifest["shot_sha256"] == shot_fingerprint(state, shot), "Bundle belongs to a different or stale shot")
        require(manifest["source_sha256"] == state["source"]["sha256"], "Bundle belongs to a different screenplay")
        verification = manifest["profile"]["verification"]
        if verification["status"] == "verified":
            require(tool == verification["tool"] and model == verification["model"], "Actual tool/model differs from verified profile; re-export")
        verify_assets(root, state, shot["asset_ids"])
        media = probe_media(source)
        require(media["duration_seconds"] > 0, "Video duration is missing or zero")
        require(abs(media["duration_seconds"] - shot["duration_seconds"]) <= 0.25, "Video duration differs from shot plan by more than 0.25 seconds")
        width, height = (int(v) for v in shot["aspect_ratio"].split(":"))
        require(media["height"] > 0 and abs(media["width"] / media["height"] - width / height) <= 0.03, "Video aspect ratio differs from shot plan")
        video_hash = file_hash(source)
        existing = next((t for t in state["takes"] if t["shot_id"] == shot_id and t["sha256"] == video_hash and t["bundle_sha256"] == manifest["bundle_sha256"]), None)
        if existing:
            require(existing["tool"] == tool and existing["model"] == model, "Duplicate take has conflicting tool/model metadata")
            require(file_hash(inside(root, existing["path"])) == video_hash, "Existing take file is missing or modified; restore the original file or import a new take")
            return existing
        take_id = "T{:05d}".format(len(state["takes"]) + 1)
        relative = "takes/{}{}".format(take_id, source.suffix.lower())
        target = inside(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(file_hash(target) == video_hash, "Video changed while importing")
        record = {"id": take_id, "shot_id": shot_id, "shot_sha256": manifest["shot_sha256"],
                  "bundle_sha256": manifest["bundle_sha256"], "path": relative, "sha256": video_hash,
                  "tool": tool, "model": model, "media": media, "imported_at": now()}
        state["takes"].append(record)
        write_json(Path(root) / "bundles" / (manifest["bundle_sha256"] + ".json"), manifest)
        save(root, state)
        return record


def review_take(root, take_id, review):
    identifier(take_id)
    require(isinstance(review, dict) and set(review) == {"reviewer", "take_sha256", "beat_checks", "criterion_checks", "continuity", "technical"}, "Unexpected/missing review fields")
    nonempty(review["reviewer"], "reviewer")
    with project_lock(root):
        state = load_project(root)
        take = next((t for t in state["takes"] if t["id"] == take_id), None)
        require(take is not None, "Unknown take")
        shot = shot_by_id(state, take["shot_id"])
        require(take["shot_sha256"] == shot_fingerprint(state, shot), "Take is stale after plan changes")
        require(review["take_sha256"] == take["sha256"] == file_hash(inside(root, take["path"])), "Review/take hash mismatch")
        verify_assets(root, state, shot["asset_ids"])
        groups = [(review["beat_checks"], set(shot["beat_ids"]), "beat_checks"),
                  (review["criterion_checks"], set(shot["acceptance_criteria"]), "criterion_checks")]
        checks = []
        for supplied, expected, label in groups:
            require(isinstance(supplied, dict) and set(supplied) == expected, label + " must account for every planned item")
            checks.extend(supplied.values())
        checks.extend([review["continuity"], review["technical"]])
        for check in checks:
            require(isinstance(check, dict) and set(check) == {"verdict", "evidence"}, "Each check needs verdict and evidence")
            require(check["verdict"] in {"pass", "fail", "uncertain"}, "Unknown review verdict")
            nonempty(check["evidence"], "review evidence")
        accepted = all(c["verdict"] == "pass" for c in checks)
        record = dict(review, take_id=take_id, reviewed_at=now(), accepted=accepted)
        state["reviews"].append(record)
        save(root, state)
        return record
