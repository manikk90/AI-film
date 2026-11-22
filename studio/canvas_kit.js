/*
 * Studio canvas kit: the shared helpers every canvas-drawn format skill uses, so each film starts from the same tested
 * parts instead of rewriting them, and the look stays the same run to run.
 *
 *   <link rel="stylesheet" href="../../studio/fonts/fonts.css">   (path relative to the page)
 *   <script src="../../studio/canvas_kit.js"></script>
 *   <script>
 *     const K = STUDIO;                         // everything below hangs off window.STUDIO
 *     K.whenReady(async () => { ...preload images, paint layers once... });
 *     window.FILM = { DUR: 6, init() {}, render(ctx, t) { ... } };
 *   </script>
 *
 * It sets window.READY = false on load and true once the studio fonts and every whenReady() task are done, which is
 * what studio/render_canvas.cjs waits for. Every helper is a pure function of its inputs and t, so frame N always
 * looks the same however the page is rendered.
 *
 * Lessons built in (from the studio's own runs and the living-painting breakdown, 2026-11-14):
 *   - seeded randomness only (rng, noise): never Math.random, or the picture changes every load
 *   - paint textured layers once (layer) and only move and combine them per frame: smooth and fast
 *   - every motion on an eased curve or a loop-safe wave (ease, keys, loopWave): no snaps
 *   - camera push-in with parallax by depth (camera, parallax); grain stays fixed to the frame (grain)
 *   - text never falls back to a system font (fonts are awaited), and stays inside the safe zone (SAFE, fitSafe)
 */
(function () {
  'use strict';
  const K = {};
  window.STUDIO = K;
  window.READY = false;

  // ---- numbers ---------------------------------------------------------------------------------------------------
  K.clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  K.lerp = (a, b, u) => a + (b - a) * u;
  K.invLerp = (a, b, x) => (b === a ? 0 : K.clamp((x - a) / (b - a)));

  /** Seeded generator (mulberry32): K.rng(7)() -> [0,1). Same seed, same sequence, every run. */
  K.rng = seed => {
    let s = seed >>> 0;
    return () => {
      s = (s + 0x6d2b79f5) >>> 0;
      let r = Math.imul(s ^ (s >>> 15), 1 | s);
      r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  };
  const hash = (x, y, seed) => {
    let h = (Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(seed | 0, 2246822519)) >>> 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  };
  /** Smooth value noise in [0,1]: wobble, boil, brush jitter, wind. */
  K.noise = (x, y = 0, seed = 1) => {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const a = hash(xi, yi, seed), b = hash(xi + 1, yi, seed), c = hash(xi, yi + 1, seed), d = hash(xi + 1, yi + 1, seed);
    return K.lerp(K.lerp(a, b, u), K.lerp(c, d, u), v);
  };

  // ---- easing and timing -----------------------------------------------------------------------------------------
  K.ease = {
    linear: u => u,
    inOut: u => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
    out: u => 1 - Math.pow(1 - u, 3),
    in: u => u * u * u,
    outExpo: u => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u)),   // fast in, long slow settle (no bounce)
    outBack: u => { const c = 1.70158; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); },  // pop
    smooth: u => u * u * (3 - 2 * u),
  };
  /** Value between t0 and t1, eased: K.tween(t, 1.2, 1.6, 0, 1, K.ease.outBack). Clamped outside the span. */
  K.tween = (t, t0, t1, a, b, e = K.ease.inOut) => K.lerp(a, b, e(K.invLerp(t0, t1, t)));
  /** Keyframes [[t, v], ...] sorted by t, eased between neighbours. */
  K.keys = (t, frames, e = K.ease.inOut) => {
    if (t <= frames[0][0]) return frames[0][1];
    for (let i = 1; i < frames.length; i++) {
      if (t <= frames[i][0]) return K.tween(t, frames[i - 1][0], frames[i][0], frames[i - 1][1], frames[i][1], e);
    }
    return frames[frames.length - 1][1];
  };
  /** A wave that closes exactly on a loop of length dur (whole cycles), so frame 0 and frame N match. */
  K.loopWave = (t, dur, cycles = 1, phase = 0) => Math.sin(2 * Math.PI * (Math.round(cycles) * t / dur + phase));
  /** Pulse 1 -> 0 after each event time (beats, kicks, hits), decaying over `len` seconds. */
  K.pulse = (t, times, len = 0.25) => {
    let best = 0;
    for (const s of times) { const d = t - s; if (d >= 0 && d < len) best = Math.max(best, 1 - d / len); if (s > t) break; }
    return best;
  };
  /** Mouth openness at t from studio/mouth_curve.py data ({fps, values}). */
  K.mouth = (m, t) => (m && m.values.length ? m.values[K.clamp(Math.round(t * m.fps), 0, m.values.length - 1)] : 0);

  // ---- layers and camera -----------------------------------------------------------------------------------------
  /** Paint once into an offscreen canvas; draw it every frame. draw(ctx, w, h) runs a single time. */
  K.layer = (w, h, draw) => {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    draw(c.getContext('2d'), w, h);
    return c;
  };
  /** Push-in camera around (cx, cy): zoom 1 -> 1.3 over the clip is the default living-painting move. */
  K.camera = (ctx, { zoom = 1, cx = ctx.canvas.width / 2, cy = ctx.canvas.height / 2, x = 0, y = 0, rot = 0 }, draw) => {
    ctx.save();
    ctx.translate(cx + x, cy + y);
    ctx.rotate(rot);
    ctx.scale(zoom, zoom);
    ctx.translate(-cx, -cy);
    draw();
    ctx.restore();
  };
  /** Layers [{img, depth}] with depth 0 (far) .. 1 (near): near layers slide faster. drift = {x, y} in px at depth 1. */
  K.parallax = (ctx, layers, drift) => {
    for (const L of layers) ctx.drawImage(L.img, drift.x * L.depth, drift.y * L.depth);
  };

  // ---- texture ---------------------------------------------------------------------------------------------------
  /** Paper / canvas grain as a layer to overlay with multiply; stays fixed to the frame. */
  K.paper = (w, h, seed = 3, amount = 0.08, tint = [246, 238, 222]) => K.layer(w, h, (c) => {
    const img = c.createImageData(w, h), r = K.rng(seed);
    for (let i = 0; i < img.data.length; i += 4) {
      const n = 1 - amount + amount * 2 * r();
      img.data[i] = tint[0] * n; img.data[i + 1] = tint[1] * n; img.data[i + 2] = tint[2] * n; img.data[i + 3] = 255;
    }
    c.putImageData(img, 0, 0);
  });
  /** Film grain: a few prebuilt noise tiles cycled by frame, so it moves but is the same on every render. */
  K.grain = (() => {
    const tiles = [];
    return (ctx, t, fps = 30, alpha = 0.06, size = 256) => {
      if (!tiles.length) for (let k = 0; k < 6; k++) tiles.push(K.layer(size, size, (c) => {
        const img = c.createImageData(size, size), r = K.rng(900 + k);
        for (let i = 0; i < img.data.length; i += 4) { const v = r() * 255; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255; }
        c.putImageData(img, 0, 0);
      }));
      const tile = tiles[Math.floor(t * fps) % tiles.length];
      ctx.save(); ctx.globalAlpha = alpha; ctx.globalCompositeOperation = 'overlay';
      ctx.fillStyle = ctx.createPattern(tile, 'repeat'); ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
      ctx.restore();
    };
  })();
  K.vignette = (ctx, strength = 0.45) => {
    const { width: w, height: h } = ctx.canvas;
    const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.3, w / 2, h / 2, Math.hypot(w, h) / 2);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${strength})`);
    ctx.save(); ctx.fillStyle = g; ctx.fillRect(0, 0, w, h); ctx.restore();
  };
  /** Halftone dots over a rect: comic shading. */
  K.halftone = (ctx, x, y, w, h, { step = 14, color = 'rgba(0,0,0,0.18)', angle = Math.PI / 4, size = 0.35 } = {}) => {
    ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip(); ctx.fillStyle = color;
    ctx.translate(x + w / 2, y + h / 2); ctx.rotate(angle);
    const R = Math.hypot(w, h) / 2;
    for (let i = -R; i < R; i += step) for (let j = -R; j < R; j += step) { ctx.beginPath(); ctx.arc(i, j, step * size, 0, 7); ctx.fill(); }
    ctx.restore();
  };
  /** Spiky comic burst with an optional word: K.burst(ctx, x, y, 160, 'POW!', {seed: 4}). */
  K.burst = (ctx, x, y, r, word, { points = 14, seed = 1, fill = '#fff', stroke = '#111', ink = '#e3242b', font = '"Bangers"', rot = -0.12, scale = 1 } = {}) => {
    const g = K.rng(seed);
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(scale, scale);
    ctx.beginPath();
    for (let i = 0; i <= points * 2; i++) {
      const a = (i / (points * 2)) * Math.PI * 2, rr = i % 2 ? r * (0.55 + 0.1 * g()) : r * (0.92 + 0.16 * g());
      ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
    }
    ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.lineWidth = r * 0.06; ctx.strokeStyle = stroke; ctx.stroke();
    if (word) {
      ctx.fillStyle = ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      let s = r * 0.62; ctx.font = `${s}px ${font}`;
      while (ctx.measureText(word).width > r * 1.3 && s > 10) { s *= 0.9; ctx.font = `${s}px ${font}`; }
      ctx.lineWidth = s * 0.12; ctx.strokeStyle = stroke; ctx.strokeText(word, 0, 0); ctx.fillText(word, 0, 0);
    }
    ctx.restore();
  };

  // ---- text and captions -----------------------------------------------------------------------------------------
  /** Instagram/Reels safe zone on a 1080x1920 frame: keep text out of the top 250 px and the bottom 420 px. */
  K.SAFE = { reel: { top: 250, bottom: 420, side: 60 }, wide: { top: 60, bottom: 90, side: 96 } };
  K.safeRect = (ctx, kind = ctx.canvas.height > ctx.canvas.width ? 'reel' : 'wide') => {
    const z = K.SAFE[kind], { width: w, height: h } = ctx.canvas;
    return { x: z.side, y: z.top, w: w - 2 * z.side, h: h - z.top - z.bottom };
  };
  /**
   * Group aligned words ({text, start, end, line}) into on-screen chunks of up to `max` words. A chunk never crosses
   * a line, and a pause longer than `gap` seconds starts a new one.
   */
  /** One word format for every timing tool: {text, start, end, line}. Accepts word_timing.py's {w, s, e, line},
   * mms_align.py's {text, start, end, line}, a bare array or a {words: [...]} object. */
  K.words = data => (Array.isArray(data) ? data : (data && data.words) || []).map(w => ({
    ...w, text: w.text !== undefined ? w.text : w.w, start: w.start !== undefined ? w.start : w.s,
    end: w.end !== undefined ? w.end : w.e, line: w.line !== undefined ? w.line : 0,
  }));
  K.chunks = (words, max = 3, gap = 0.6) => {
    const out = []; let cur = [];
    for (const w of K.words(words)) {
      const prev = cur[cur.length - 1];
      if (cur.length && (cur.length >= max || prev.line !== w.line || w.start - prev.end > gap)) { out.push(cur); cur = []; }
      cur.push(w);
    }
    if (cur.length) out.push(cur);
    return out.map(ws => ({ words: ws, start: ws[0].start, end: ws[ws.length - 1].end }));
  };
  /** The chunk on screen at t (held until the next chunk starts, at most `hold` s after its last word). */
  K.chunkAt = (chunks, t, hold = 0.8) => {
    for (let i = 0; i < chunks.length; i++) {
      const c = chunks[i], next = chunks[i + 1];
      const until = Math.min(next ? next.start : Infinity, c.end + hold);
      if (t >= c.start - 0.05 && t < until) return c;
    }
    return null;
  };
  /**
   * Karaoke caption: the chunk centred at (x, y), the word being spoken in `active` (optionally on a pill), words
   * already spoken in `done`, upcoming in `todo`. Shrinks to fit maxWidth. Returns the box drawn, for safe-zone checks.
   */
  K.caption = (ctx, chunk, t, {
    x = ctx.canvas.width / 2, y = ctx.canvas.height - 560, size = 72, font = '"Noto Sans Devanagari", "Inter"', weight = 800,
    todo = 'rgba(255,255,255,0.9)', done = '#fff', active = '#ffd400', pill = null, stroke = 'rgba(0,0,0,0.85)',
    maxWidth = ctx.canvas.width - 160, upper = false, pop = 0.12,
  } = {}) => {
    if (!chunk) return null;
    const words = chunk.words.map(w => (upper ? w.text.toUpperCase() : w.text));
    let s = size, space, widths, total;
    const measure = () => {
      ctx.font = `${weight} ${s}px ${font}`;
      space = ctx.measureText(' ').width; widths = words.map(w => ctx.measureText(w).width);
      total = widths.reduce((a, b) => a + b, 0) + space * (words.length - 1);
    };
    measure();
    while (total > maxWidth && s > 24) { s *= 0.92; measure(); }
    let cx = x - total / 2;
    ctx.save(); ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    chunk.words.forEach((w, i) => {
      const on = t >= w.start && t < w.end + 0.02, past = t >= w.end;
      const k = on ? 1 + 0.12 * (1 - K.clamp((t - w.start) / pop)) : 1;
      ctx.save(); ctx.translate(cx + widths[i] / 2, y); ctx.scale(k, k);
      if (on && pill) {
        ctx.fillStyle = pill; const pw = widths[i] + s * 0.4, ph = s * 1.25;
        ctx.beginPath(); ctx.roundRect(-pw / 2, -ph / 2, pw, ph, ph / 2); ctx.fill();
      }
      ctx.font = `${weight} ${s}px ${font}`; ctx.textAlign = 'center';
      if (stroke && !(on && pill)) { ctx.lineWidth = s * 0.14; ctx.strokeStyle = stroke; ctx.strokeText(words[i], 0, 0); }
      ctx.fillStyle = on ? (pill ? '#111' : active) : past ? done : todo;
      ctx.fillText(words[i], 0, 0);
      ctx.restore();
      cx += widths[i] + space;
    });
    ctx.restore();
    return { x: x - total / 2, y: y - s * 0.7, w: total, h: s * 1.4 };
  };
  /** True when a box sits inside the safe zone; logs once per frame when it does not. */
  K.inSafe = (ctx, box, kind) => {
    if (!box) return true;
    const r = K.safeRect(ctx, kind);
    const ok = box.x >= r.x && box.y >= r.y && box.x + box.w <= r.x + r.w && box.y + box.h <= r.y + r.h;
    if (!ok) console.warn('outside safe zone', JSON.stringify(box));
    return ok;
  };

  // ---- readiness -------------------------------------------------------------------------------------------------
  const tasks = [];
  K.whenReady = fn => { tasks.push(fn); };
  K.loadImage = src => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('image: ' + src)); i.src = src; });
  /** Families that must render; a page may push more before load. All studio families by default. */
  K.FONTS = ['Noto Sans Devanagari', 'Tiro Devanagari Hindi', 'Inter', 'Yatra One', 'Bangers', 'Rozha One', 'Kalam',
    'Caveat', 'Great Vibes', 'Teko', 'Cormorant', 'Quicksand', 'EB Garamond', 'Amatic SC', 'Instrument Serif',
    'Kaushan Script', 'Abril Fatface', 'Playfair Display', 'Saira Extra Condensed', 'Caladea'];
  K.fontsLoaded = () => K.FONTS.filter(f => document.fonts.check(`40px "${f}"`));
  window.STUDIO_FONTS = {
    ready: new Promise(res => window.addEventListener('load', () => {
      // load every declared face, not just regular: a bold or italic face loaded lazily would draw frame 0 in a
      // fallback font. document.fonts holds one FontFace per @font-face rule of fonts.css.
      const faces = [...document.fonts].map(f => f.load().catch(() => null));
      Promise.all(faces.concat(K.FONTS.map(f => document.fonts.load(`40px "${f}"`, 'अa').catch(() => null)))).then(res);
    })),
  };
  window.STUDIO_FONTS.ready
    .then(async () => { for (const fn of tasks) await fn(); })
    .then(() => { window.READY = true; })
    .catch(e => { console.error(e); window.READY_ERROR = String(e); });
})();
