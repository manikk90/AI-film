"""Checks for studio/editor_package.py, the NLE editor package (Premiere Pro / DaVinci Resolve timeline).

The media test builds a SYNTHETIC FIXTURE (an FFmpeg test pattern and sine tones) in a temporary folder. It is
not a film asset and is never kept."""

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import struct
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "studio"))
import editor_package as EP  # noqa: E402


def wav_info(path):
    """Read a WAV header ourselves: the stdlib wave module rejects WAVE_FORMAT_EXTENSIBLE
    (what FFmpeg writes for 24-bit) before Python 3.12."""
    blob = Path(path).read_bytes()
    assert blob[:4] == b"RIFF" and blob[8:12] == b"WAVE", path
    pos, fmt, data = 12, None, None
    while pos + 8 <= len(blob):
        tag, size = blob[pos:pos + 4], struct.unpack("<I", blob[pos + 4:pos + 8])[0]
        body = blob[pos + 8:pos + 8 + size]
        if tag == b"fmt ":
            fmt = struct.unpack("<HHIIHH", body[:16])
        elif tag == b"data":
            data = body
        pos += 8 + size + (size & 1)
    channels, rate, align, bits = fmt[1], fmt[2], fmt[4], fmt[5]
    return {"channels": channels, "rate": rate, "width": bits // 8, "frames": len(data) // align, "data": data}

FPS = Fraction(24)


def clip(track, name, start, frames, **kw):
    return EP.Clip(track=track, name=name, src=Path("unused"), start_s=Fraction(start, 24), start=start,
                   frames=frames, **kw)


class FrameGridTest(unittest.TestCase):
    def test_exact_frame_math(self):
        self.assertEqual(EP.align(Fraction("9.6"), 48000, FPS), (230, 800, 25))  # 9.6 s = frame 230 + 800 samples
        self.assertEqual(EP.align(Fraction(0), 96000, FPS), (0, 0, 48))
        self.assertEqual(EP.frame_samples(25, FPS), 50000)
        self.assertEqual(EP.timecode(2893, FPS), "00:02:00:13")

    def test_frame_rates(self):
        self.assertEqual(EP.parse_fps(23.976), Fraction(24000, 1001))
        self.assertEqual(EP.timebase(EP.parse_fps("29.97")), (30, True))
        self.assertEqual(EP.timebase(EP.parse_fps(25)), (25, False))
        self.assertEqual(EP.frame_samples(1, Fraction(24000, 1001)), 2002)
        with self.assertRaises(EP.PackageError):
            EP.parse_fps(24.5)

    def test_shots_must_cover_the_picture_back_to_back(self):
        ok = EP.plan_shots([{"name": "a", "start": 0, "end": 1}, {"name": "b", "start": 1, "end": 2.5}], 60, FPS)
        self.assertEqual([(s.start, s.end) for s in ok], [(0, 24), (24, 60)])
        bad = [
            ([{"name": "a", "start": 0, "end": 1}, {"name": "b", "start": 1.5, "end": 2.5}], "gap"),
            ([{"name": "a", "start": 0, "end": 1}, {"name": "b", "start": 0.5, "end": 2.5}], "overlap"),
            ([{"name": "a", "start": 0, "end": 2}], "picture has 60 frames"),
            ([{"name": "a", "start": 1, "end": 0}], "ends at or before"),
            ([], "at least one shot"),
        ]
        for shots, message in bad:
            with self.assertRaisesRegex(EP.PackageError, message):
                EP.plan_shots(shots, 60, FPS)

    def test_overlapping_sounds_get_their_own_lane(self):
        clips = [clip("VO", "L1", 0, 48), clip("VO", "L2", 24, 48), clip("VO", "L3", 48, 10), clip("MUS", "MUS", 0, 99)]
        self.assertEqual(EP.assign_lanes(clips), ["VO", "VO 2", "MUS"])
        self.assertEqual([c.lane for c in clips], ["VO", "VO 2", "VO", "MUS"])

    def test_file_urls(self):
        self.assertEqual(EP.file_url("/Users/manik/My Edits/media", "VO_L1.wav"),
                         "file://localhost/Users/manik/My%20Edits/media/VO_L1.wav")
        self.assertEqual(EP.file_url("D:\\Edits\\Ramayana\\media", "V_picture.mp4"),
                         "file://localhost/D%3a/Edits/Ramayana/media/V_picture.mp4")
        with self.assertRaises(EP.PackageError):
            EP.file_url("relative/media", "x.wav")


class TimelineXmlTest(unittest.TestCase):
    def build(self):
        shots = [EP.Shot("open", 0, 24), EP.Shot("end", 24, 48)]
        vo = clip("VO", "L1", 12, 13, text="बहुत पुरानी बात है", file="VO_L1.wav")
        mus = clip("MUS drone", "MUS drone", 0, 48, file="MUS_drone.wav", depth=32)
        clips = [vo, mus]
        lanes = EP.assign_lanes(clips)
        markers = EP.collect_markers({"markers": [{"t": 1.5, "name": "hit"}]}, clips, FPS)
        xml = EP.build_xml("Test film", FPS, 1080, 1920, {"file": "V_picture.mp4", "frames": 48}, shots, clips,
                           lanes, markers, lambda n: EP.file_url("/media", n))
        return xml, ET.fromstring(xml.encode("utf-8"))

    def test_sequence_and_picture(self):
        xml, root = self.build()
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>'))
        self.assertEqual((root.tag, root.get("version")), ("xmeml", "4"))
        seq = root.find("sequence")
        self.assertEqual(seq.findtext("duration"), "48")
        self.assertEqual(seq.findtext("rate/timebase"), "24")
        fmt = seq.find("media/video/format/samplecharacteristics")
        self.assertEqual((fmt.findtext("width"), fmt.findtext("height")), ("1080", "1920"))
        v1 = seq.findall("media/video/track/clipitem")
        self.assertEqual([c.findtext("name") for c in v1], ["S01 open", "S02 end"])
        self.assertEqual([(c.findtext("start"), c.findtext("end"), c.findtext("in"), c.findtext("out")) for c in v1],
                         [("0", "24", "0", "24"), ("24", "48", "24", "48")])
        self.assertEqual(v1[0].findtext("file/pathurl"), "file://localhost/media/V_picture.mp4")
        self.assertEqual((v1[1].find("file").get("id"), len(v1[1].find("file"))), ("file-1", 0))

    def test_stereo_stems_are_linked_left_right_pairs(self):
        _, root = self.build()
        tracks = root.findall("sequence/media/audio/track")
        self.assertEqual(len(tracks), 4)  # two stems, each a left and a right track
        ids = {c.get("id") for c in root.iter("clipitem")}
        defined = {}
        for t in tracks:
            self.assertEqual(t.get("premiereTrackType"), "Stereo")
            out = t.findtext("outputchannelindex")
            for c in t.findall("clipitem"):
                self.assertEqual(c.findtext("sourcetrack/trackindex"), out)
                links = [ln.findtext("linkclipref") for ln in c.findall("link")]
                self.assertEqual(len(links), 2)
                self.assertTrue(set(links) <= ids)
                f = c.find("file")
                if len(f):
                    self.assertNotIn(f.get("id"), defined)
                    defined[f.get("id")] = f
        self.assertEqual(sorted(defined), ["file-2", "file-3"])
        self.assertEqual(defined["file-2"].findtext("media/audio/channelcount"), "2")
        self.assertEqual(defined["file-3"].findtext("media/audio/samplecharacteristics/depth"), "32")
        vo = tracks[0].find("clipitem")
        self.assertEqual([vo.findtext(k) for k in ("start", "end", "in", "out")], ["12", "25", "0", "13"])
        self.assertIn("बहुत पुरानी", vo.findtext("name"))

    def test_markers(self):
        _, root = self.build()
        marks = [(m.findtext("name"), m.findtext("in"), m.findtext("comment")) for m in root.findall("sequence/marker")]
        self.assertEqual(marks, [("L1", "12", "बहुत पुरानी बात है"), ("hit", "36", "")])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "media tests need FFmpeg")
class PackageMediaTest(unittest.TestCase):
    def test_builds_a_package_from_a_synthetic_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            film = tmp / "synthetic-fixture"
            film.mkdir()

            def ff(*args):
                subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *map(str, args)], check=True)

            # SYNTHETIC FIXTURE: an FFmpeg test pattern and sine tones, not film assets
            ff("-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24:duration=2", "-c:v", "libx264",
               "-pix_fmt", "yuv420p", film / "picture.mp4")
            ff("-f", "lavfi", "-i", "sine=frequency=440:sample_rate=24000:duration=0.5", film / "vo.wav")
            ff("-f", "lavfi", "-i", "sine=frequency=220:sample_rate=48000:duration=2", "-ac", "2",
               "-c:a", "pcm_f32le", film / "music.wav")
            (film / "subs.srt").write_text("1\n00:00:00,300 --> 00:00:00,800\nsynthetic\n", encoding="utf-8")
            manifest = {
                "title": "Synthetic fixture", "fps": 24, "picture": "picture.mp4", "picture_textless": True,
                "subtitles": "subs.srt",
                "shots": [{"name": "one", "start": 0, "end": 1}, {"name": "two", "start": 1, "end": 2}],
                "audio": [{"track": "VO", "name": "L1", "file": "vo.wav", "start": 0.3, "text": "synthetic line"},
                          {"track": "MUS", "file": "music.wav", "start": 0}],
                "notes": ["Synthetic fixture for the tests."],
            }
            (film / "editor.json").write_text(json.dumps(manifest), encoding="utf-8")
            out = EP.build_package(film / "editor.json", tmp / "editor", log=lambda s: None, crf=18)

            media = out / "media"
            self.assertEqual({p.name for p in media.iterdir()},
                             {"V_picture.mp4", "VO_L1.wav", "MUS.wav", "Synthetic_fixture.srt"})
            self.assertEqual(EP.count_frames(media / "V_picture.mp4"), 48)
            w = wav_info(media / "VO_L1.wav")  # 0.3 s = frame 7 + 400 samples; 0.5 s of sound
            self.assertEqual((w["channels"], w["rate"], w["width"], w["frames"]), (2, 48000, 3, 13 * 2000))
            raw = w["data"]
            self.assertEqual(raw[:400 * 6], bytes(400 * 6))  # silent until exactly 0.3 s
            self.assertTrue(any(raw[400 * 6:440 * 6]))
            w = wav_info(media / "MUS.wav")  # float source under full scale -> 24-bit
            self.assertEqual((w["width"], w["frames"]), (3, 48 * 2000))

            root = ET.parse(out / "Synthetic_fixture.xml").getroot()
            self.assertEqual(root.find("sequence/media/video/track/clipitem/file/pathurl").text,
                             EP.file_url(str(media), "V_picture.mp4"))
            vo = root.find("sequence/media/audio/track/clipitem")
            self.assertEqual([vo.findtext(k) for k in ("start", "end")], ["7", "20"])
            with open(out / "timeline.csv", encoding="utf-8") as fh:
                kinds = [row["kind"] for row in csv.DictReader(fh)]
            self.assertEqual(kinds, ["shot", "shot", "sound", "sound", "marker"])
            text = (out / "README.md").read_text(encoding="utf-8")
            for needle in ("Premiere Pro", "DaVinci Resolve", "textless", "Synthetic fixture for the tests."):
                self.assertIn(needle, text)

            with self.assertRaisesRegex(EP.PackageError, "already exists"):
                EP.build_package(film / "editor.json", out, log=lambda s: None)
            manifest["picture_filter"] = "no_such_filter"
            (film / "editor.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(EP.PackageError):
                EP.build_package(film / "editor.json", tmp / "broken", log=lambda s: None)
            self.assertFalse((tmp / "broken").exists() or (tmp / "broken.partial").exists())


if __name__ == "__main__":
    unittest.main()
