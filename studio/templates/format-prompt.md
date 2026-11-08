# Format prompt (template)

This is the one-prompt method from the "12 Claude Video Formats" guide, adapted to the studio's renderer. The format list is in `studio/formats/claude-video-formats.json`. Fill in the brackets, keep the rest as it is, and change only the last line to try another format. Inside a studio run, this prompt is the picture brief: the words still go through the script gate, and the look goes through the Gate 3 preview.

```
Make a [SECONDS]-second vertical animated video for [WHAT IT IS, AND ITS NAME], as one self-contained HTML file.

It shows: [THE NAME OR TITLE], the line "[THE LOCKED LINE]", [TWO OR THREE THINGS FROM THE STORY] (draw them in code, no image or video files).

Size 1080 by 1920, no scrolling. Treat it as a film with a beginning, a middle and an end, not a web page: no buttons, and something big is moving in every second.

Draw every frame from time alone: one <canvas>, and window.FILM = { DUR: [SECONDS], init(), render(ctx, t) } that draws the frame at t seconds. No timers, no requestAnimationFrame loop, no CSS animation, no Math.random() (use a seeded hash), so the same t always gives the same picture. A preview loop may call FILM.render only when window.FILM_PREVIEW is set. Any Hindi text is Devanagari, set in a font that shapes it correctly.

Colour: 60-30-10: [MAIN #hex] about 60 % (the world), [SECOND #hex] about 30 % (people and props), [ACCENT #hex] about 10 %, only on [WHAT THE EYE MUST FOLLOW].

Format: [FORMAT].
```

## Why these parts matter (from the guide)
- **`Format: …`** is the only line that changes between films. A name of two or three words is enough; the model already knows these looks.
- **"A film with a beginning, a middle and an end"** gets scenes in an order instead of a page layout.
- **"Something big is moving in every second"** keeps motion going all the way through, instead of text fading in over a still background.
- **"Draw them in code, no image or video files"** keeps everything in one file. It also means no real photo of the product appears.
- **Your own words steer the picture.** In the guide, the name "Harbour" put boats and lighthouses in most of the films, and a line about Tuesday and Friday became a journey through the week.

## The studio's changes to the guide's prompt
- **1080×1920 instead of 540×960,** so the film is ready for Reels and Shorts.
- **A pure function of time instead of real-time animation.** The guide recorded each film on a virtual clock that took over timers, requestAnimationFrame and CSS animations. The `window.FILM` contract lets the studio's own renderer draw the exact frame for any t, with nothing to install.

## Render it
- **Video:** `node studio/render_canvas.cjs film.html out.mp4 --size 1080x1920 --fps 30`. Add `--audio mix.wav` once the sound exists.
- **Gate 3 preview frames:** `node studio/render_canvas.cjs film.html preview/frame --size 1080x1920 --stills 1,3.5,6`.

## Fix one moment (re-prompt)
Watch it through, note the second, and ask only for that moment:

```
At about [SECOND] seconds the film shows [WHAT YOU SEE]. Change it to [WHAT YOU WANT]. Leave the rest of the film as it is.
```

The guide's first tries had such moments: plain water at about 2 s in Claymation, and a white flash at about 5 s in Neon synthwave. The static at about 1 s in the VHS film was on purpose.
