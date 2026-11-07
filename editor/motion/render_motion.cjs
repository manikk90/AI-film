#!/usr/bin/env node
/*
 * Render a Mann motion template (editor/motion/templates/*.html) to a video or PNG stills.
 * Headless Chromium via Playwright draws each frame at t = i / fps; FFmpeg encodes it.
 * Works the same in the cloud session (Playwright pre-installed) and on a laptop
 * (`npm i -g playwright && npx playwright install chromium`). Nothing is fetched at render time.
 *
 *   node editor/motion/render_motion.cjs <template.html> <out.mov|out.mp4> --size 1080x1920 --dur 3 [--fps 30] [--vars '{"title":"..."}']
 *   node editor/motion/render_motion.cjs <template.html> <out-prefix> --size 1080x1920 --dur 3 --stills 0.5,1.5
 *
 * .mov is ProRes 4444 with alpha (for overlays); .mp4 is H.264 on the template's `bg` colour.
 */
'use strict';
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function parse(argv) {
  const pos = [], opt = { fps: 30, size: '1080x1920', dur: 3, vars: '{}' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) opt[argv[i].slice(2)] = argv[++i];
    else pos.push(argv[i]);
  }
  if (pos.length !== 2) { console.error('usage: render_motion.cjs <template.html> <out> --size WxH --dur s [--fps 30] [--vars json] [--stills t1,t2]'); process.exit(2); }
  const [w, h] = String(opt.size).split('x').map(Number);
  const vars = opt['vars-file'] ? JSON.parse(fs.readFileSync(opt['vars-file'], 'utf8')) : JSON.parse(opt.vars);
  vars.duration = +opt.dur;
  return { page: path.resolve(pos[0]), out: path.resolve(pos[1]), w, h, fps: +opt.fps, dur: +opt.dur, vars,
           stills: opt.stills ? String(opt.stills).split(',').map(Number) : null };
}

(async () => {
  const a = parse(process.argv.slice(2));
  if (!fs.existsSync(a.page)) { console.error('template not found: ' + a.page); process.exit(2); }
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: a.w, height: a.h } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.addInitScript(([vars, size]) => { window.__VARS = vars; window.__SIZE = size; }, [a.vars, [a.w, a.h]]);
  await page.goto('file://' + a.page);
  await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
  const frame = t => page.evaluate(t => {
    window.FILM.render(document.querySelector('canvas').getContext('2d'), t);
    return document.querySelector('canvas').toDataURL('image/png').split(',')[1];
  }, t);
  if (a.stills) {
    fs.mkdirSync(path.dirname(a.out), { recursive: true });
    for (const [i, t] of a.stills.entries()) {
      const f = `${a.out}_${i + 1}.png`;
      fs.writeFileSync(f, Buffer.from(await frame(t), 'base64'));
      console.log(f);
    }
  } else {
    const alpha = a.out.toLowerCase().endsWith('.mov');
    const enc = alpha
      ? ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-vendor', 'apl0']
      : ['-filter_complex', `color=c=${(a.vars.bg || '#000000').replace('#', '0x')}:s=${a.w}x${a.h}:r=${a.fps}[b];[b][0:v]overlay=shortest=1,format=yuv420p`,
         '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast'];
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(a.fps), '-i', '-', ...enc, a.out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const n = Math.max(1, Math.round(a.dur * a.fps));
    for (let i = 0; i < n; i++) {
      const buf = Buffer.from(await frame(i / a.fps), 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    const code = await new Promise(r => ff.on('close', r));
    if (code !== 0) { console.error('ffmpeg failed'); process.exit(1); }
    console.log(JSON.stringify({ file: a.out, frames: n, alpha }));
  }
  await browser.close();
  if (errors.length) { console.error('page errors:\n' + errors.join('\n')); process.exit(1); }
})().catch(e => { console.error(String(e)); process.exit(1); });
