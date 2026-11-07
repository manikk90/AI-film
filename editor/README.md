# Mann: AI video editor

Mann is the studio's editor agent (`.claude/agents/mann.md`). Give it raw footage plus a script or direction. Its smart engine analyses the footage and suggests how to edit it; **you make three decisions (style, script lock, storyboard)** and Mann handles everything else: assets, cut, motion graphics, sound design, colour, VFX, render and QC. Corrections are scoped: a whole-video note redoes the whole video, a one-part note redoes and re-shows only that part. Mann also studies reference videos, keeps a 50-style library (`styles/INDEX.md`), and turns every correction into a rule it checks next time.

## Your three decisions

| Decision | When | Command Mann runs with your words |
|---|---|---|
| 1. Style | after `SUGGESTIONS.md` (3 styles + 1 experiment + unique ideas) | `approve-style <edit> <slug> --words "..."` |
| 2. Script lock | when the film has narration/dialogue | `lock-script <edit> SCRIPT.md --words "..."` |
| 3. Storyboard | after the numbered frames (whole, or just the corrected part) | `approve <edit> --words "..."` or `approve <edit> --clips C04,C05 --words "..."` |

| Ask | Skill |
|---|---|
| "Ye raw clips hain, is script pe edit karo" | `/mann-edit` |
| "Is reel ka style samjho, style sheet banao" | `/mann-style-lab` |
| "Ye cut late hai / music loud hai" (any correction) | `/studio-learn` → `studio/LEARNINGS.md` (Editor) + `editor/rules.json` |

## Toolchain (open source)

| Tool | Used for | Install |
|---|---|---|
| [FFmpeg](https://ffmpeg.org) | trim, speed, crop/reframe, grade, LUTs, transitions (xfade), titles (drawtext with Devanagari shaping), burned subtitles (libass), music ducking, SFX, two-pass loudness, QC measurements | system package |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (or openai-whisper) | transcripts, word-timed phone captions | `pip install faster-whisper` |
| [OpenCV](https://opencv.org) 4.x (headless) | face tracking for reframing (bundled Haar cascades) | `pip install opencv-python-headless==4.10.0.84` |
| [fontTools](https://github.com/fonttools/fonttools) + [Fontsource](https://fontsource.org) | merging open-licensed Google Fonts (Latin + Devanagari) into TTFs for FFmpeg/libass | `pip install fonttools`; fonts via npm |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | downloading reference videos for the style lab | `pip install yt-dlp` |
| [Hyperframes](https://github.com/heygen-com/hyperframes) | HTML + GSAP motion graphics rendered to ProRes 4444 with alpha, laid over the cut | `npm i -g hyperframes@0.8.230` (Node ≥ 22) |

`bash editor/install.sh` installs all of them; `python3 -m aifilm.editor doctor` reports what is present.

Canvas and motion-template rendering also need Node, the `playwright` module and a Chromium browser. By default Playwright uses its downloaded browser. In an environment with Chromium already installed, select it explicitly, for example `export AIFILM_CHROMIUM_EXECUTABLE=/usr/bin/chromium`. Both renderers use that executable, without downloading a browser or changing their page/approval contracts. Use an absolute executable path; compatibility still needs a real render check on that host.

## Commands (`python3 -m aifilm.editor …`, or `mann …` after `pip install -e .`)

| Command | What it does |
|---|---|
| `doctor` | Which tools are installed |
| `ingest <edit> <files…> [--link]` | Copy (or symlink) raw files into `<edit>/raw/`, record probe + sha256 in `media.json` |
| `transcribe <media> <out> [--language hi] [--model small]` | `<stem>.json`, `<stem>.srt`, `<stem>.captions.srt` (≤ 4 words per cue) |
| `scenes <video>` | Detected cut times |
| `assets <edit>` | Analyse every file once (cached by hash): kind, footage guess (talking/B-roll/action/screen), shots, motion, colour, audio activity, loudness, music tempo |
| `suggest <edit> [--aspect 9:16]` | Smart engine: rank the 50 styles for this footage, 1 `experiment` mashup, unique ideas, hook candidates, problems → `SUGGESTIONS.md` |
| `styles [--family music]` | List the catalog |
| `approve-style`, `lock-script` | Record the owner's decisions 1 and 2 |
| `autocut <edit> --style <slug> [--seconds 30] [--aspect 9:16]` | Draft `edl.json`: speech-led A-roll with B-roll inserts, or motion-ranked montage; the style's grade, transitions, zooms, FX, captions, beat sync |
| `beats <audio>` | Tempo (BPM), beat times and a confidence score |
| `library-scan <folder>` | Index a reusable music/SFX/LUT/overlay library (`mann-library.json`) |
| `status <edit>` | What needs the owner: `none`, `part` (which clips) or `whole` |
| `preview-part <edit> --clips C04` | Quick 720p video of just the corrected part (plus neighbours) |
| `craft [--domain cuts]` | The craft rulebook (also `editor/craft/CRAFT.md`) |
| `craft-check <edit>` | Automatic craft checks (safe zones, captions, type hierarchy, fonts/Devanagari, text contrast, 30-degree rule, transitions, grades, variety, flash safety, music under voice); exit 1 on a FAIL; also part of `storyboard` and `qc` |
| `pairings`, `themes` | Font pairings (Devanagari verified) and colour themes |
| `fonts-install --pairing <id>` / `fonts-install <Family>…` | Fetch open-licensed fonts from npm (@fontsource), merge Latin + Devanagari into one TTF per weight, install to `~/.local/share/fonts/mann` (`MANN_FONTS` overrides) |
| `motion list` | The 10 motion-graphics templates and their variables |
| `motion still <template> <out-prefix> [--theme id] [--pairing id] [--vars json] [--times 0.5,1.5]` | PNG stills of a template, to look at |
| `motion render <template> <out.mov\|out.mp4> [--size 1080x1920] [--duration s] [--theme] [--pairing] [--vars json]` | Standalone clip: `.mov` = ProRes 4444 with alpha, `.mp4` = on the theme background |
| `motion add <template> <edit> --at s [--duration s] [--vars json]` | Render sized to the edit with its theme and fonts, keep it above the captions and off the tracked face, and add it to `edl.json` as an overlay |
| `footage search "<query>" [--source internet-archive\|wikimedia-commons\|nasa\|pexels]` | Free archive/stock clips with their licence and a rights category (`usable` true/false) |
| `footage fetch <edit> <n\|url> [--license … --credit …]` | Download search result *n* (or a direct/page link with an owner-stated licence) into `raw/archive/` with provenance |
| `footage add <edit> <file> --source-url … --license … --credit … [--rights owner-licensed --licence-ref …]` | A clip the owner downloaded or bought (e.g. from movingimagearchive.com) |
| `footage credits <edit>` / `footage list <edit>` | `renders/CREDITS.md` for the clips the cut uses / the provenance records |
| `validate <edit>` | Check `edl.json`, print the timeline and pace |
| `render <edit> --quality draft\|standard\|best` | Encoder speed vs size; clips come from the per-clip cache (`renders/cache/`) and only changed clips are re-processed |
| `storyboard <edit> [--two] [--changed] [--only C04]` | Numbered frames from the full edit graph + `STORYBOARD.md` (pace, sound plan, changes); `--changed` makes a part storyboard when only some clips changed |
| `approve <edit> --words "…" [--clips C04] [--final]` | Record the owner's exact approval; approvals are per clip plus one for the whole-video settings, tied to file hashes |
| `render <edit>` | Refuses unless the style, script lock and every clip's storyboard are approved; writes `renders/master.mp4` (−14 LUFS, two-pass) and `preview_720p.mp4` |
| `qc <edit> [--frames 1.5]` | Measures the master against the EDL, `editor/rules.json` and the style target; `renders/QC.md`; exit 1 on failure |
| `fetch <url> <dir>` | yt-dlp download for study |
| `analyze-style <video> <workdir> --name …` | Cut rhythm, pace curve, palette, tone, loudness, silences, one frame per shot, draft style sheet |
| `publish-style <workdir> <slug>` | Save a finished sheet + targets to `editor/styles/<slug>/` |
| `mg-new <edit> <name>` / `mg-render <edit> <name>` | Hyperframes composition in `<edit>/mg/<name>/` → `mg/<name>.mov` with alpha |

## Motion templates (`editor/motion/`)

`lower-third`, `title-card`, `counter` (Indian digit grouping), `callout`, `progress-bar`, `cta`, `kinetic-words`, `map-pin`, `stat-card`, `highlight-box`. Each is a canvas page drawn as a pure function of time (`templates/*.html`, shared `lib.js`), rendered by `render_motion.cjs` with Playwright Chromium and FFmpeg: the same command runs in the cloud session and on a laptop, with no `npx` and no network fetch. Colours come from a craft colour theme (roles chosen by measured contrast and saturation), fonts from a font pairing (Devanagari shaped by Chromium). Use them on their own (`motion render`) or inside an edit (`motion add`). Hyperframes (`mg-new`/`mg-render`) stays available for custom compositions where `npx`/the CLI is allowed.

## Archive footage (`footage`)

When a cut needs real shots the owner did not film, Mann searches free sources first (Internet Archive films with a licence URL, Wikimedia Commons, NASA, Pexels with `PEXELS_API_KEY`), then any site the owner names, such as movingimagearchive.com, through `footage add` (the owner's downloaded or licensed file) or `footage fetch` with a direct link. Every clip gets a record in `<edit>/footage.json` (source URL, licence, rights category, credit, licence reference, hash). Storyboard and render refuse: no-derivatives licences (editing is a derivative), non-commercial licences unless the owner confirms the video is non-commercial (`--noncommercial-ok`), unknown rights, owner-licensed clips without a licence reference, and any file in `raw/archive/` without a record or changed after it. `render` writes `renders/CREDITS.md` with every attribution and condition. In this cloud session the footage hosts are blocked; search runs on the laptop or after the owner allows the hosts.

## Edit folder (`projects/<slug>/edit/`, git-ignored)

```
BRIEF.md        the owner's direction, verbatim
SCRIPT.md       the script, if any (locked by the owner)
raw/            the owner's media (never modified)
media.json      probe + sha256 per file
assets.json     the engine's asset list; analysis/ holds per-file analysis
SUGGESTIONS.md  the engine's edit suggestions
transcripts/    Whisper output
LOG.md          Mann's footage log: best takes and moments
edl.json        the cut
mg/             Hyperframes compositions and their .mov renders
storyboard/     F01_<clip>_<timecode>.jpg …, STORYBOARD.md, storyboard.json; part/ for one-part corrections
approvals.json  the owner's decisions (style, script, storyboard whole/part, final) with their words
renders/        master.mp4, preview_720p.mp4, parts/, QC.md, qc.json, qc-frames/
```

## EDL (`edl.json`)

See `edl.example.json`. Fields:

- `format`: `width`, `height` (even), `fps`, `fit` (`cover` crops to fill, `contain` letterboxes).
- `sources`: id → file inside the edit folder.
- `clips[]`: `id`, `source`, `in`, `out` (source seconds), `speed` (0.25–4, audio pitch kept), `beat` (why the shot is there), `transition_in` (`cut`, `dissolve`, `fade`, `fadeblack`, `fadewhite`, `wipeleft|right|up|down`, `slideleft|right|up|down`, `smoothleft|right`, `circleopen|close`, `radial`, `pixelize`, `zoomin`, `hblur`, `distance`, `squeezeh|v`, with `duration`), `zoom` (`from`/`to`, punch-in or Ken Burns), `grade` (per-clip preset), `fx` (list: `shake`, `flash`, `fade_in`, `rgb_split`, `letterbox`, `step_print`, `vhs`, `stop_motion`, `glow`, `bw`), `freeze` (seconds held at the end), `inserts` (B-roll pictures over the clip while its sound runs: `source`, `in`, `out`, `at`), `audio` (false mutes the clip), `text` (one or a list: `value`, `position` top/center/bottom, `size`, `color`, `box`, `start`, `end`, `font`).
- `grade`: `preset` (`neutral`, `punchy-social`, `teal-orange`, `warm-film`, `cool-night`, `bw-contrast`, `faded-vintage`, `moody-dark`, `bright-clean`, `pastel`, `bleach-bypass`, `desat-doc`, `neon-night`, `vhs-retro`, `golden-hour`), `exposure`, `contrast`, `saturation`, `temperature` (K), `lut` (.cube), `grain`, `vignette`.
- `audio`: `keep_source`, `source_gain_db`, `music` (`file`, `gain_db`, `start`, `duck`, `fade_out`; looped to length), `sfx[]` (`file`, `at`, `gain_db`).
- `overlays[]`: `file` (Hyperframes .mov with alpha, or any video), `at`.
- `subtitles`: `file` (.srt), `burn`, `size` (fraction of height), `position` (top/center/bottom), `color` (white/yellow/green/red/cyan), `uppercase`, `box`, or a raw `force_style`; `margin_v`.
- `script`: the locked script file; the storyboard refuses if it changed after the lock.
- `typography`: `pairing` (font pairing id) and `theme` (colour theme id); text items take a `role` (`title`, `headline`, `body`, `caption`, `label`) that sets size and font from the type scale and pairing. All burned text is rendered through one ASS script with complex shaping (correct Devanagari).
- `reframe`: `auto` (on `format` or a clip) makes the crop follow the tracked face (OpenCV Haar cascades, smoothed path); `center` or omitted keeps a centre crop.
- `subtitles.animate`: `highlight`, `pop`, `word` or `karaoke`, with `highlight_color` and `words` (timeline word timings JSON, written by autocut; estimated from word length when missing).
- `style`: a slug in `editor/styles/`. `deliberate_silences`: timeline seconds where silence is intended. `master`: `lufs`, `true_peak`.

## What is verified and what is not

`tests/test_editor.py` builds synthetic FFmpeg fixtures (test patterns, tones, a 120 BPM click track, labelled as such) and checks: EDL validation, timeline maths, storyboard frames and change lists, the approval gates (style, script lock, whole and per-part storyboard, stale approvals), part previews, render duration/resolution/loudness, QC failures, every FX through the filter graph, asset classification, beat detection (120 ± 3 BPM), suggestions, a valid autocut draft in all 50 styles, style analysis and Hyperframes GSAP vendoring. These prove the pipeline's mechanics, not the creative quality of an edit, which is why the owner's decisions exist.

Speed: analysis is cached by file hash; a storyboard decodes the edit once (about real time on this machine for 1080x1920), and part corrections re-show only the changed clips.

Not built yet: automatic best-take selection between repeated takes, and audio judged by ear. Footage labels and style scores are heuristics; catalog pace numbers are estimates until measured from a reference. In this cloud environment `youtube.com`, `huggingface.co` / `openaipublic.azureedge.net` (Whisper models) and `cdn.jsdelivr.net` are blocked; `mg-new` and `mg-render` copy GSAP from npm instead of the CDN.
