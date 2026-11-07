/*
 * Mann motion library: shared helpers for the canvas motion templates in editor/motion/templates/.
 * Every template is a pure function of time drawn on one transparent <canvas>, so it renders the
 * same in the cloud and on a laptop (headless Chromium via Playwright, encoded by FFmpeg).
 *
 * Template contract:  MOTION = { defaults: {...}, init(v, W, H), render(ctx, t, v, W, H) }
 * The renderer sets window.__VARS (merged over MOTION.defaults) and window.__SIZE = [W, H] before load.
 * Theme keys every template understands: bg, ink, accent, accent2, muted, font_display, font_text.
 */
'use strict';
const M = {
  clamp: (x, a = 0, b = 1) => Math.min(Math.max(x, a), b),
  lerp: (a, b, k) => a + (b - a) * k,
  prog: (t, a, b) => M.clamp((t - a) / Math.max(b - a, 1e-6)),
  outCubic: k => 1 - Math.pow(1 - k, 3),
  inCubic: k => k * k * k,
  inOutCubic: k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
  outBack: k => { const c = 1.70158; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
  outElastic: k => (k === 0 || k === 1 ? k : Math.pow(2, -10 * k) * Math.sin((k * 10 - 0.75) * (2 * Math.PI) / 3) + 1),
  /* 0 -> 1 entrance over `inLen`, hold, 1 -> 0 exit over the last `outLen` seconds of `dur`. */
  env(t, dur, inLen = 0.45, outLen = 0.35) {
    if (t < inLen) return M.outCubic(M.prog(t, 0, inLen));
    if (t > dur - outLen) return 1 - M.inCubic(M.prog(t, dur - outLen, dur));
    return 1;
  },
  /* Safe zone (fractions of the frame) matching editor/craft/craft.json `standard` profiles. */
  /* `v.bottom_limit` (0-1) lifts the bottom edge above burned captions; set by `motion add`. */
  safe(W, H, v) {
    const r = W / H;
    const z = r < 0.7 ? [0.125, 0.25, 0.06, 0.13] : r < 0.9 ? [0.08, 0.15, 0.06, 0.06] : [0.05, 0.05, 0.05, 0.05];
    const y1 = Math.min(H * (1 - z[1]), v && v.bottom_limit ? H * v.bottom_limit : H);
    return { x0: W * z[2], x1: W * (1 - z[3]), y0: H * z[0], y1, w: W * (1 - z[2] - z[3]), h: y1 - H * z[0] };
  },
  /* Vertical centre for centred templates: `v.y` (0-1 of the frame) when given, else `def` of the safe box. */
  cy(s, H, v, def) { return v && v.y != null ? v.y * H : s.y0 + s.h * def; },
  font(v, role, size, weight) {
    const fam = role === 'display' ? v.font_display : v.font_text;
    return `${weight || (role === 'display' ? 800 : 600)} ${Math.round(size)}px "${fam}", "Noto Sans Devanagari", "Noto Sans", sans-serif`;
  },
  /* Largest size <= `size` at which `text` fits in `maxW`. */
  fit(ctx, text, maxW, size, v, role, weight) {
    let s = size;
    ctx.font = M.font(v, role, s, weight);
    while (s > 8 && ctx.measureText(text).width > maxW) { s *= 0.94; ctx.font = M.font(v, role, s, weight); }
    return s;
  },
  rrect(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  },
  alpha(hex, a) {
    const h = hex.replace('#', '');
    const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  },
  shadow(ctx, on, v) { ctx.shadowColor = on ? 'rgba(0,0,0,0.45)' : 'transparent'; ctx.shadowBlur = on ? 18 : 0; ctx.shadowOffsetY = on ? 4 : 0; },
};

const THEME_DEFAULTS = { bg: '#111111', ink: '#ffffff', accent: '#ffcc00', accent2: '#3e7bfa', muted: '#bbbbbb',
  font_display: 'Poppins', font_text: 'Hind', fonts: [] };

window.addEventListener('load', async () => {
  const [W, H] = window.__SIZE || [1080, 1920];
  const canvas = document.querySelector('canvas');
  canvas.width = W; canvas.height = H;
  const v = Object.assign({}, THEME_DEFAULTS, MOTION.defaults || {}, window.__VARS || {});
  for (const f of v.fonts || []) {
    try { const face = new FontFace(f.family, `url("${f.url}")`, { weight: String(f.weight || 400) }); document.fonts.add(await face.load()); }
    catch (e) { console.warn('font not loaded', f.family, String(e)); }
  }
  await document.fonts.ready;
  MOTION.init && MOTION.init(v, W, H);
  window.FILM = { DUR: v.duration, init() {}, render: (ctx, t) => { ctx.clearRect(0, 0, W, H); MOTION.render(ctx, t, v, W, H); } };
  window.READY = true;
});
