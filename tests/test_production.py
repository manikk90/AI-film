"""Workflow tests use synthetic media, never real or paid film generation."""

import copy
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from aifilm.cli import main
from aifilm.core import (
    ProductionError, add_asset, audit, file_hash, init_project, inside, load_project,
    project_lock, read_json, review_breakdown, set_plan, shot_fingerprint, write_json,
)
from aifilm.portable import export_shot, import_take, read_bundle, review_take


REPO = Path(__file__).resolve().parents[1]


class ProjectCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        init_project(REPO / "examples/screenplay.txt", self.root)
        self.plan = read_json(REPO / "examples/plan.json")
        for shot in self.plan["shots"]:
            shot["duration_seconds"] = 1
        self.text_profile = read_json(REPO / "profiles/portable-text.json")

    def prepare(self):
        set_plan(self.root, self.plan)
        review_breakdown(self.root, "synthetic-test", "Fixture only: compare all six source lines and seven semantic beats")


class RecordTests(ProjectCase):
    def test_original_bytes_and_all_lines_preserved(self):
        state = load_project(self.root)
        self.assertEqual((self.root / "screenplay.txt").read_bytes(), (REPO / "examples/screenplay.txt").read_bytes())
        self.assertEqual(len(state["scenes"]), 2)
        self.assertEqual(len(state["units"]), 6)
        self.assertEqual(state["units"][-1]["id"], "U00006")

    def test_missing_scene_and_compound_beats_reported(self):
        self.plan["shots"] = self.plan["shots"][:1]
        result = set_plan(self.root, self.plan)
        self.assertEqual(result["unplanned_scenes"], ["SC002"])
        self.assertIn("B03", result["unplanned_beats"])
        self.assertFalse(result["complete"])
        with self.assertRaisesRegex(ProductionError, "missing coverage"):
            review_breakdown(self.root, "reviewer", "Cannot approve incomplete coverage")

    def test_missing_source_unit_is_not_hidden_by_shot_count(self):
        self.plan["beats"] = [b for b in self.plan["beats"] if b["id"] != "B07"]
        self.plan["shots"][-1]["beat_ids"] = ["B06"]
        result = set_plan(self.root, self.plan)
        self.assertEqual(result["unmapped_source_units"], ["U00006"])

    def test_breakdown_review_and_real_takes_required(self):
        result = set_plan(self.root, self.plan)
        self.assertFalse(result["breakdown_review_current"])
        self.assertTrue(all(s["status"] == "missing" for s in result["shots"]))
        review_breakdown(self.root, "synthetic-test", "Fixture source reviewed")
        self.assertFalse(audit(self.root)["complete"])

    def test_cross_scene_and_duplicate_ids_rejected_without_mutation(self):
        before = file_hash(self.root / "project.json")
        broken = copy.deepcopy(self.plan)
        broken["shots"][0]["beat_ids"] = ["B06"]
        with self.assertRaisesRegex(ProductionError, "cross-scene"):
            set_plan(self.root, broken)
        broken = copy.deepcopy(self.plan)
        broken["beats"].append(broken["beats"][0])
        with self.assertRaisesRegex(ProductionError, "Duplicate"):
            set_plan(self.root, broken)
        self.assertEqual(before, file_hash(self.root / "project.json"))

    def test_unknown_fields_and_wrong_types_rejected(self):
        cases = []
        wrong = copy.deepcopy(self.plan)
        wrong["shots"][0]["duration_seconds"] = True
        cases.append(wrong)
        wrong = copy.deepcopy(self.plan)
        wrong["shots"][0]["asset_ids"] = "CHAR_1"
        cases.append(wrong)
        wrong = copy.deepcopy(self.plan)
        wrong["beats"][0]["optional"] = True
        cases.append(wrong)
        for wrong in cases:
            with self.assertRaises(ProductionError):
                set_plan(self.root, wrong)

    def test_changed_source_and_register_are_detected(self):
        (self.root / "screenplay.txt").write_text("INT. NEW ROOM - DAY\nChanged.\n")
        with self.assertRaisesRegex(ProductionError, "screenplay changed"):
            audit(self.root)

    def test_preamble_does_not_allow_hiding_scene_content(self):
        self.plan["preamble_unit_ids"] = ["U00003"]
        with self.assertRaisesRegex(ProductionError, "pre-heading"):
            set_plan(self.root, self.plan)

    def test_no_scene_headings_is_a_clear_error(self):
        source = self.base / "unstructured.txt"
        source.write_text("Someone enters a room.\n")
        with self.assertRaisesRegex(ProductionError, "No scene headings"):
            init_project(source, self.base / "other")

    def test_no_overwrite_and_project_lock(self):
        with self.assertRaisesRegex(ProductionError, "already exists"):
            init_project(REPO / "examples/screenplay.txt", self.root)
        with project_lock(self.root):
            with self.assertRaisesRegex(ProductionError, "busy"):
                set_plan(self.root, self.plan)
        set_plan(self.root, self.plan)

    def test_unresolved_creative_decision_blocks_export(self):
        self.plan["decisions"][0]["status"] = "needs_creative_decision"
        set_plan(self.root, self.plan)
        with self.assertRaisesRegex(ProductionError, "Resolve creative"):
            export_shot(self.root, "SH001", self.base / "bundle", self.text_profile)
        self.assertFalse((self.base / "bundle").exists())

    def test_declared_provider_limits_are_enforced(self):
        self.prepare()
        profile = copy.deepcopy(self.text_profile)
        profile["durations"] = [5, 10]
        with self.assertRaisesRegex(ProductionError, "Unsupported duration"):
            export_shot(self.root, "SH001", self.base / "bundle", profile)

    def test_bundle_detects_changed_prompt(self):
        self.prepare()
        target = self.base / "bundle"
        result = export_shot(self.root, "SH001", target, self.text_profile)
        self.assertEqual(result["status"], "exported_not_generated")
        self.assertEqual(result["compatibility"], "requires_target_tool_check")
        (target / "prompt.txt").write_text("Changed prompt")
        with self.assertRaisesRegex(ProductionError, "prompt changed"):
            read_bundle(target)

    def test_path_escape_and_symlink_escape_rejected(self):
        with self.assertRaisesRegex(ProductionError, "escapes"):
            inside(self.root, "../private.txt")
        (self.root / "outside").symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ProductionError, "escapes"):
            inside(self.root, "outside/private.txt")

    def test_shot_local_change_preserves_unrelated_fingerprint(self):
        self.prepare()
        old = load_project(self.root)
        old_hashes = [shot_fingerprint(old, s) for s in old["plan"]["shots"]]
        self.plan["shots"][0]["camera"] = "Gentle camera push instead of locked frame"
        set_plan(self.root, self.plan)
        new = load_project(self.root)
        new_hashes = [shot_fingerprint(new, s) for s in new["plan"]["shots"]]
        self.assertNotEqual(old_hashes[0], new_hashes[0])
        self.assertEqual(old_hashes[1:], new_hashes[1:])
        self.assertFalse(audit(self.root)["breakdown_review_current"])

    def test_changed_boundary_invalidates_adjacent_shot(self):
        self.prepare()
        old = load_project(self.root)
        old_hash = shot_fingerprint(old, old["plan"]["shots"][1])
        self.plan["shots"][0]["end_state"] = "Meera now stands on the other side of the table"
        set_plan(self.root, self.plan)
        new = load_project(self.root)
        self.assertNotEqual(old_hash, shot_fingerprint(new, new["plan"]["shots"][1]))

    def test_cli_reports_incomplete_and_errors_with_exit_codes(self):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["audit", str(self.root)]), 1)
        self.assertFalse(json.loads(output.getvalue())["complete"])
        with redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(["set-plan", str(self.root), str(self.base / "missing.json")]), 2)
        self.assertIn("Cannot read JSON", error.getvalue())


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is required for media workflow tests")
class MediaTests(ProjectCase):
    @classmethod
    def setUpClass(cls):
        cls.media_temp = tempfile.TemporaryDirectory()
        cls.media_root = Path(cls.media_temp.name)
        cls.video = cls.media_root / "synthetic.mp4"
        cls.image = cls.media_root / "synthetic.png"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=96x54:r=24:d=1",
                        "-c:v", "mpeg4", "-y", str(cls.video)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(cls.video), "-frames:v", "1", "-threads", "1", "-y", str(cls.image)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.media_temp.cleanup()

    def imported(self, shot_id="SH001", name="bundle"):
        target = self.base / name
        export_shot(self.root, shot_id, target, self.text_profile)
        return import_take(self.root, shot_id, self.video, target, "synthetic-test-tool", "fixture-v1")

    def evidence(self, take, verdict="pass"):
        shot = next(s for s in self.plan["shots"] if s["id"] == take["shot_id"])
        check = {"verdict": verdict, "evidence": "Synthetic test attestation only; 0.0-1.0 seconds. Not a real film review."}
        return {"reviewer": "synthetic-test", "take_sha256": take["sha256"],
                "beat_checks": {b: dict(check) for b in shot["beat_ids"]},
                "criterion_checks": {c: dict(check) for c in shot["acceptance_criteria"]},
                "continuity": dict(check), "technical": dict(check)}

    def test_real_container_import_is_not_acceptance_and_duplicate_is_idempotent(self):
        self.prepare()
        take = self.imported()
        self.assertEqual(audit(self.root)["shots"][0]["status"], "review_required")
        duplicate = import_take(self.root, "SH001", self.video, self.base / "bundle", "synthetic-test-tool", "fixture-v1")
        self.assertEqual(take["id"], duplicate["id"])
        self.assertEqual(len(load_project(self.root)["takes"]), 1)
        with self.assertRaisesRegex(ProductionError, "conflicting tool/model"):
            import_take(self.root, "SH001", self.video, self.base / "bundle", "different-tool", "fixture-v1")

    def test_healthy_alternative_take_can_replace_corrupted_accepted_take(self):
        self.prepare()
        take = self.imported()
        review_take(self.root, take["id"], self.evidence(take))
        alternative = self.base / "alternative.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(self.video), "-c", "copy", "-metadata", "comment=alternative synthetic take", str(alternative)], check=True)
        replacement = import_take(self.root, "SH001", alternative, self.base / "bundle", "synthetic-test-tool", "fixture-v1")
        review_take(self.root, replacement["id"], self.evidence(replacement))
        (self.root / take["path"]).write_bytes(b"corrupted earlier take")
        self.assertEqual(audit(self.root)["shots"][0]["status"], "accepted")

    def test_wrong_aspect_ratio_and_reference_count_rejected(self):
        self.prepare()
        self.plan["shots"][0]["aspect_ratio"] = "9:16"
        set_plan(self.root, self.plan)
        export_shot(self.root, "SH001", self.base / "portrait", self.text_profile)
        with self.assertRaisesRegex(ProductionError, "aspect ratio"):
            import_take(self.root, "SH001", self.video, self.base / "portrait", "test", "v1")
        for asset_id in ("CHAR_V1", "ROOM_V1"):
            add_asset(self.root, asset_id, "character", self.image, "Synthetic reference")
        self.plan["shots"][0]["asset_ids"] = ["CHAR_V1", "ROOM_V1"]
        self.plan["shots"][0]["input_asset_ids"] = ["CHAR_V1", "ROOM_V1"]
        set_plan(self.root, self.plan)
        profile = read_json(REPO / "profiles/portable-multi-reference.json")
        profile["max_references"] = 1
        with self.assertRaisesRegex(ProductionError, "Too many references"):
            export_shot(self.root, "SH001", self.base / "limited", profile)

    def test_all_takes_and_reviews_can_complete_then_changed_media_revokes(self):
        self.prepare()
        takes = []
        for shot in self.plan["shots"]:
            take = self.imported(shot["id"], shot["id"])
            takes.append(take)
            review_take(self.root, take["id"], self.evidence(take))
        self.assertTrue(audit(self.root)["complete"])
        (self.root / takes[0]["path"]).write_bytes(b"changed")
        result = audit(self.root)
        self.assertFalse(result["complete"])
        self.assertEqual(result["shots"][0]["status"], "invalid_media")

    def test_missing_beat_and_uncertain_review_cannot_accept(self):
        self.prepare()
        take = self.imported()
        review = self.evidence(take)
        review["beat_checks"].pop("B02")
        with self.assertRaisesRegex(ProductionError, "every planned item"):
            review_take(self.root, take["id"], review)
        result = review_take(self.root, take["id"], self.evidence(take, "uncertain"))
        self.assertFalse(result["accepted"])
        self.assertEqual(audit(self.root)["shots"][0]["status"], "review_required")

    def test_later_failed_review_revokes_acceptance(self):
        self.prepare()
        take = self.imported()
        review_take(self.root, take["id"], self.evidence(take))
        self.assertEqual(audit(self.root)["shots"][0]["status"], "accepted")
        review_take(self.root, take["id"], self.evidence(take, "fail"))
        self.assertNotEqual(audit(self.root)["shots"][0]["status"], "accepted")

    def test_stale_take_and_stale_bundle_are_rejected_after_change(self):
        self.prepare()
        take = self.imported()
        self.plan["shots"][0]["action"] = "A revised action"
        set_plan(self.root, self.plan)
        self.assertEqual(audit(self.root)["shots"][0]["status"], "stale")
        with self.assertRaisesRegex(ProductionError, "stale"):
            review_take(self.root, take["id"], self.evidence(take))
        with self.assertRaisesRegex(ProductionError, "stale shot"):
            import_take(self.root, "SH001", self.video, self.base / "bundle", "test", "v1")

    def test_wrong_duration_and_wrong_shot_bundle_rejected(self):
        self.prepare()
        export_shot(self.root, "SH001", self.base / "bundle", self.text_profile)
        with self.assertRaisesRegex(ProductionError, "different or stale"):
            import_take(self.root, "SH002", self.video, self.base / "bundle", "test", "v1")
        self.plan["shots"][0]["duration_seconds"] = 5
        set_plan(self.root, self.plan)
        export_shot(self.root, "SH001", self.base / "long", self.text_profile)
        with self.assertRaisesRegex(ProductionError, "duration differs"):
            import_take(self.root, "SH001", self.video, self.base / "long", "test", "v1")

    def test_invalid_video_bytes_and_wrong_review_hash_rejected(self):
        self.prepare()
        take = self.imported()
        review = self.evidence(take)
        review["take_sha256"] = "incorrect"
        with self.assertRaisesRegex(ProductionError, "hash mismatch"):
            review_take(self.root, take["id"], review)
        invalid = self.base / "fake.mp4"
        invalid.write_bytes(b"not a video")
        with self.assertRaisesRegex(ProductionError, "decoded"):
            import_take(self.root, "SH001", invalid, self.base / "bundle", "test", "v1")

    def test_single_frame_requires_complete_provenance_and_immutable_assets(self):
        add_asset(self.root, "CHAR_V1", "character", self.image, "Synthetic identity")
        add_asset(self.root, "FRAME_BAD", "keyframe", self.image, "Synthetic frame without provenance")
        shot = self.plan["shots"][0]
        shot["asset_ids"] = ["CHAR_V1", "FRAME_BAD"]
        shot["input_asset_ids"] = ["FRAME_BAD"]
        set_plan(self.root, self.plan)
        profile = read_json(REPO / "profiles/portable-single-image.json")
        with self.assertRaisesRegex(ProductionError, "References would be dropped"):
            export_shot(self.root, "SH001", self.base / "bad", profile)
        add_asset(self.root, "FRAME_GOOD", "keyframe", self.image, "Synthetic frame", ["CHAR_V1"])
        shot["asset_ids"] = ["CHAR_V1", "FRAME_GOOD"]
        shot["input_asset_ids"] = ["FRAME_GOOD"]
        set_plan(self.root, self.plan)
        manifest = export_shot(self.root, "SH001", self.base / "good", profile)
        self.assertEqual(manifest["reference_order"], ["FRAME_GOOD"])
        self.assertEqual(len(manifest["assets"]), 2)
        with self.assertRaisesRegex(ProductionError, "immutable"):
            add_asset(self.root, "CHAR_V1", "character", self.image, "Replacement")

    def test_changed_asset_and_bundle_reference_detected(self):
        asset = add_asset(self.root, "CHAR_V1", "character", self.image, "Synthetic identity")
        self.plan["shots"][0]["asset_ids"] = ["CHAR_V1"]
        self.plan["shots"][0]["input_asset_ids"] = ["CHAR_V1"]
        set_plan(self.root, self.plan)
        profile = read_json(REPO / "profiles/portable-multi-reference.json")
        export_shot(self.root, "SH001", self.base / "bundle", profile)
        (self.base / "bundle" / asset["path"]).write_bytes(b"wrong image")
        with self.assertRaisesRegex(ProductionError, "reference changed"):
            read_bundle(self.base / "bundle")
        (self.root / asset["path"]).write_bytes(b"wrong image")
        with self.assertRaisesRegex(ProductionError, "Asset modified"):
            export_shot(self.root, "SH001", self.base / "other", profile)


if __name__ == "__main__":
    unittest.main()
