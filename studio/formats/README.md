# Format prompts

**Owner ke liye:** "12 Claude Video Formats" guide ke 12 film styles yahan save hain. Har ek ek line ka prompt hai, "Format: Comic book." jaisa. Inhe kisi bhi film ke picture brief mein laga sakte ho. Poori list `studio/STYLE_MENU.md` mein "Format prompts" ke neeche hai, aur prompt ka template `studio/templates/format-prompt.md` mein hai.

## What this is
- **Source:** the owner shared the "12 Claude Video Formats" guide (PDF, signed Simon) on 2026-11-07.
- **The guide's method:** it ran one prompt 12 times and changed only its last line, `Format: <name>.`. Each run was a fresh Claude agent writing a 7-second, 540×960 film for an invented coffee roaster as one self-contained HTML file, drawn in code.
- **The 12 formats** are kinetic typography, claymation stop motion, pixel art game, whiteboard sketch, 80s VHS commercial, rubber hose cartoon, isometric 3D, anime opening, paper cut-out, comic book, neon synthwave and liquid motion. Ten were in the guide's reel; neon synthwave and liquid motion were not.
- **`claude-video-formats.json`** holds, for each format:
  - the exact words typed
  - the look
  - what the guide's first-try film did, in our words
  - what it suits on the owner's channels
  - the nearest existing studio styles
- The guide's images are not copied into this repo.

## Status
None of these has been made in this repo. They are named looks with a known first-try result elsewhere: not library styles, and not tested here.

When one is close to a library style that has a demo and an engine (`rubber-hose`, `pixel-rpg`, `whiteboard`, `synthwave` …), prefer the library style for a full film. Use the format prompt for a quick look, a test or a short promo.

## Use one
1. **Pick a format.** The director proposes one in the format brief (`03-format.md`), or the owner names one.
2. **Fill in the prompt.** Use `studio/templates/format-prompt.md`, with the locked words from `04-script/dialogue-lock.md`.
   - The studio's version asks for 1080×1920.
   - It also asks for a `window.FILM.render(ctx, t)` page that draws every frame from time alone, so `node studio/render_canvas.cjs` can render it frame by frame.
3. **Gate 3:** run `--stills` for the 3 preview frames.
4. **Render, then QC and delivery** as usual (`studio/deliver.py`: 2 files).
5. **Fix one moment** with the re-prompt line in the template.
