# Studio fonts

Every font the format skills name, vendored so a render never falls back to a system font and the look is the same
on every machine. All are from [google/fonts](https://github.com/google/fonts) (`ofl/<family>/`), fetched 2026-11-14,
licensed under the SIL Open Font License 1.1: each family's licence is in `licenses/<family>-OFL.txt`.

- `fonts.css`: one `@font-face` per file. Link it from a canvas page and wait for `STUDIO_FONTS.ready`
  (`studio/canvas_kit.js`) before the first frame.
- `families.json`: the family names, for tests and pickers.
- Devanagari: Tiro Devanagari Hindi (serif, lyrics), Noto Sans Devanagari (captions, UI), Yatra One (comic boxes),
  Rozha One (big hero words), Kalam (handwriting). The rest are Latin only; put Devanagari in one of these five.

To add a family: download `ofl/<family>/<file>.ttf` and its `OFL.txt` from google/fonts, add a line to `fonts.css`
and to `families.json`, and run `python3 -m unittest tests.test_canvas_kit`.
