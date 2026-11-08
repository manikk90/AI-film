# Studio harness for the imported format skills

The `.claude/skills/` folders listed in `studio/IMPORTED_SKILLS.json` come from the owner's [Ai-Animation](https://github.com/manikk90/Ai-Animation) repo. Upstream they are by aansh.ai, MIT licensed (`third_party/ai-animation/`). The owner asked for them to be imported, and `studio/import_skills.py` did it on 2026-11-02.

Each copy keeps its original text, and a short harness block under its title says how it runs here. This file is the full contract. Where a skill's own steps disagree with this file or with `studio/LEARNINGS.md`, this file and the ledger win, and the newest owner rule wins.

## Every run
1. Read `studio/LEARNINGS.md` and `studio/PROFILE.md`, and follow caveman mode (`studio/CAVEMAN.md`): minimum tokens. Every picture follows the 60-30-10 colour rule (`studio/COLOR.md`).
2. Make the project folder `projects/<slug>/` (git-ignored), with `STATUS.md` from `studio/templates/`, and log each step there.
3. Talk to the owner in Hinglish. Make routine choices yourself; the gates below are the owner's rules, not optional questions.
4. A skill can run on its own (`/madhubani-kahani kahani.mp3`) or as the format the director picks in a `/viral-studio` run. Either way the gates below apply.

## Words and the script gate
| Kind (in the registry) | Where the words come from | What applies |
|---|---|---|
| `voice` | the owner's recording | No script gate on the owner's own words. Captions use them exactly. |
| `script` | the owner's script and voice lines | Locked as given. With no script yet, the writer writes it and the owner approves it (Gate 2). |
| `song` | the owner's song and lyrics | Rights check (below). Captions follow the lyrics exactly. |
| `third-party-audio` | usually someone else's recording: a creator, a show, a pravachan speaker, a film scene | Rights and likeness check (below). The owner decides before publishing. |
| `written` | the skill writes them | Researcher (`FACTS.md`, dated sources), then writer, then critique, then owner approval (Gate 2), all before any voice or picture. |
| `visual` | place labels and titles only | The owner approves the labels and the route at the preview. |
| `clip` | the owner's own footage | Never re-voice, rewrite or re-grade the owner's face unless the skill says so. |
| `assets` | the owner's sketches and photos | Stock clips only with a licence that allows this use, noted in `CREDITS`. |

## Preview (Gate 3) and render
- **Preview before the full render:**
  - 3 numbered frames at 3 timecodes (the hook at about 0:01, the middle, the end), at the final aspect, with the captions as they will look
  - each frame captioned with its timecode and what is said there
  - a 20–30 s music sketch when the skill adds music
  - then wait for the owner's OK

  This replaces a skill's contact-sheet, stills or snapshot step: the owner wants individual frames, not a dense sheet.
- **Render:** renders are CPU-heavy, so run one at a time in the cloud session and never more than two.
- **Music** gets special attention (`LEARNINGS.md`, Production):
  - original music only
  - recorded samples for the lead instruments
  - hits and drops checked against the cuts

## Rights, facts and people
- **Facts:** every number, price or claim that is shown or said needs a sourced row in `FACTS.md`. News needs dated sources.
- **Songs and other people's recordings:** use them only when the owner holds the rights or has permission. The social agent flags the risk in the publish kit.
- **Real people:**
  - never put a real person's likeness or cloned voice on something they did not make or endorse
  - label drawn versions as illustrations
  - never imply an endorsement
- **Brands and shows:**
  - no real logos, mastheads, app or channel branding
  - original characters only: no characters, crests or names from an existing anime or show
  - a news look must never present opinion, satire or fiction as real news
- **Downloads:** only the owner's own videos, or ones they hold the rights to.
- **Footage and screenshots:** only when licensed for the use or quoted briefly with credit. Credit each one on screen and in `CREDITS`.

## Tools in the cloud session (checked 2026-11-02)
Run `python3 studio/check_env.py` at the start of every production, and put its table in `06-qc.md`. The notes below are the state on 2026-11-02.
- **Available:**
  - Node 22, FFmpeg 6.1, Python 3
  - Playwright Chromium (`/opt/pw-browsers/chromium`)
  - the npm registry (HyperFrames, Remotion) and PyPI
- **Blocked:**
  - Hugging Face, which hosts the Whisper models
  - `dl.fbaipublicfiles.com`, which hosts the torchaudio MMS_FA alignment model

  So the skills' own transcription and forced alignment cannot run here unless the owner provides the model file.
- **Word timing**, in this order:
  1. **Known words** (a script, lyrics, the locked dialogue): `studio/word_timing.py` works offline. Run it with the Lemo-Opuscar venv's Python: `<lemo-opuscar>/.venv/bin/python studio/word_timing.py voice.wav words.txt words.json --js assets/words.js --srt lines.srt`.
     - **How:** it speaks every word with Kokoro, male or female by the speaker's pitch, and warps that voice's spectrum to fit the speaker. Then it matches the reference and the recording with slope-limited DTW: first over the whole recording, then line by line.
     - **Measured on 2026-11-02, on Kokoro speech only:** in the other-voice word tests, word starts were within 17 ms for 90 % of words, worst 38–62 ms. On the Ramayana VO (continuous speech with room reverb), line starts were within 20 ms.
     - **Not measured yet:** human recordings, and sung vocals over music. For a song, use the vocal stem if there is one.
     - **Pauses:** a pause of over about 0.3 s inside a line with no punctuation can shift a word, so put a comma there. Look at any line the output marks `check`.
  2. Timings the studio already has, from its own voice lines and cue map.
  3. A transcript or alignment file the owner provides.
  4. **Unknown words** (a talking-head clip with no script) need transcription. That means Whisper or MMS_FA, which work only once the owner allows their hosts (below), or a transcript from the owner.

  Never guess timings. Say which route was used, in `06-qc.md`.
- **ElevenLabs** only when it is reachable and the key is in `ELEVENLABS_API_KEY` (see `LEARNINGS.md`).
- **Rendering:**
  - `node studio/render_canvas.cjs <page.html> <out.mp4> [--audio voice.mp3]` renders a canvas page frame by frame in the pre-installed Chromium and encodes it with FFmpeg, with nothing from the network. Pages that use `window.FILM.render(ctx, t)` (daksh-ai) or `window.render(t)` (Lemo-Opuscar) work.
  - `--stills 1,6,11` writes the Gate 3 preview frames.
- **`daksh-ai`:**
  - Its stub-canvas harness passes on the template.
  - The template renders end to end with `studio/render_canvas.cjs`: 360 frames, 12.0 s, 1920×1080 at 30 fps (2026-11-02).
- **HyperFrames:** npm is reachable, but the session's auto-mode classifier refuses to run npm packages with `npx` ("Code from External"). Use `studio/render_canvas.cjs`. If the owner wants HyperFrames itself, they can allow that command in their permission settings.
- **Reachability (checked 2026-11-02):**
  - Blocked: huggingface.co, dl.fbaipublicfiles.com, openaipublic.azureedge.net, download.pytorch.org, alphacephei.com (Vosk models), cdn.jsdelivr.net and api.elevenlabs.io.
  - Reachable: pypi.org, registry.npmjs.org and raw.githubusercontent.com.
- **To unblock word timing and voice,** the owner allows these hosts under Network access in the environment's settings (https://code.claude.com/docs/en/cloud-environments#network-access):
  - `dl.fbaipublicfiles.com`: the skills' own MMS_FA alignment
  - `openaipublic.azureedge.net`: Whisper models, for transcription
  - `api.elevenlabs.io`: ElevenLabs, together with the `ELEVENLABS_API_KEY` secret

  Then the doctor shows these capabilities as ready.

## Session setup verified 2026-11-08
The owner opened `dl.fbaipublicfiles.com`, `openaipublic.azureedge.net`, `huggingface.co`, `download.blender.org` and `download.pytorch.org`. The notes above from 2026-11-02 are older; run `check_env.py` for the current state.
- **Install** (a fresh container needs it again):
  - `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`
  - `pip install demucs uroman openai-whisper mediapipe librosa`
  - `apt-get install -y libegl1 libgles2 libgl1 espeak-ng`
  - Blender 4.5 LTS from download.blender.org into `/opt`, linked as `/usr/local/bin/blender`
- **Checked on synthetic espeak speech (2026-11-08):**
  - MMS_FA aligns English and Devanagari, with speakers.
  - On the demucs vocal stem of speech over a beat, word starts were within 20 ms of the clean alignment.
  - Whisper large-v3 transcribes Hindi on CPU, in about 200 s including the model load.
  - The MediaPipe Tasks matte, parts and landmarks run.
  - The 3d-explainer template renders in EEVEE headless.
- **Not checked yet:** human recordings and real footage.

## Shared skill tools (added 2026-11-08)
Every copy ends with a generated `## Render settings (studio)` section: outputs, fps, audio, engine and the tools for its steps.
- `studio/beats.py`: tempo, beats, downbeats, kicks, hits (librosa).
- `studio/mouth_curve.py`: mouth-open curve per frame from voice loudness, shut outside words.
- `studio/mms_align.py`: torchaudio MMS_FA with uroman, `SPEAKER|text` lines, ad-libs, `--windows` for squeezed lines. Needs `dl.fbaipublicfiles.com`.
- `studio/separate_vocals.py`: demucs two stems. Needs demucs and `dl.fbaipublicfiles.com`.
- `studio/person_matte.py`: MediaPipe person matte per frame.
- `studio/ref_analyze.py`: reference reel at 2 fps, cuts, shot lengths, levels.
- `studio/whatsapp_copy.py`: 720p two-pass copy under 20 MB, never overwrites without `--force`.
- `studio/frame_check.py`: black/frozen frames, size, fps, audio sync before delivery.
- `node studio/render_canvas.cjs ... --abitrate 256k` for songs.
`check_env.py` reports each of them. Tests: `tests/test_skill_tools.py` (synthetic fixtures).

## Delivery
- Output to `projects/<slug>/final/`, with a `06-qc.md` that says what was checked and what could not be checked.
- Send exactly 2 files with `studio/deliver.py`: the final video, and one zip with everything else. This is the owner's rule from 2026-11-02, and each file must be at most 400 MiB.
- A film built from code with separate stems also gets the editor package (`studio/editor_package.py`) inside the zip.
- Never publish, schedule or post anywhere.

## Updating
Re-run `python3 studio/import_skills.py <Ai-Animation clone>` after an upstream change, or `python3 studio/import_skills.py` alone after editing `studio/skill_sources/`. To change how a skill runs here, change this file or the generator's tables; never edit the imported copies by hand.
