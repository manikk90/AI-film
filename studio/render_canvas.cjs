#!/usr/bin/env node
/*
 * Render a canvas page frame by frame in headless Chromium and encode it with FFmpeg: the studio's local renderer for
 * pages whose picture is a pure function of time. It needs nothing from the network.
 *
 *   node studio/render_canvas.cjs <page.html> <out.mp4> [--fps 30] [--size 1920x1080] [--audio voice.mp3]
 *                                 [--from 0] [--to <seconds>] [--crf 18]
 *   node studio/render_canvas.cjs <page.html> <out-prefix> --stills 1,6.5,11
 *       → <out-prefix>_1.png ... : the owner's Gate 3 preview frames at those timecodes (seconds)
 *
 * Two page contracts are supported:
 *   - daksh-ai (and the imported canvas skills): window.FILM = { DUR, init(), render(ctx, t) } drawing on the first <canvas>
 *   - Lemo-Opuscar films: window.render(t) and window.DUR
 * It waits for document.fonts and window.READY (when the page defines it), draws every frame at t = from + i / fps,
 * takes the canvas as PNG and pipes it to FFmpeg. It prints the output path and the frame count.
 * Requires Playwright and Chromium. Set AIFILM_CHROMIUM_EXECUTABLE to use an installed browser.
 */
'use strict';
const { chromium } = require('playwright');
const { launchOptions } = require('./chromium.cjs');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function args(argv) {
  const pos = [], opt = { fps: 30, size: '1920x1080', crf: 18 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) opt[argv[i].slice(2)] = argv[++i];
    else pos.push(argv[i]);
  }
  if (pos.length !== 2) {
    console.error('usage: node studio/render_canvas.cjs <page.html> <out.mp4> [--fps 30] [--size 1920x1080] [--audio a.mp3] [--from 0] [--to s] [--crf 18]');
    process.exit(2);
  }
  const [w, h] = String(opt.size).split('x').map(Number);
  const stills = opt.stills ? String(opt.stills).split(',').map(Number) : null;
  if (stills && stills.some(t => !(t >= 0))) { console.error('--stills takes timecodes in seconds, like 1,6.5,11'); process.exit(2); }
  return { page: path.resolve(pos[0]), out: path.resolve(pos[1]), fps: +opt.fps, w, h, audio: opt.audio, from: +(opt.from || 0), to: opt.to, crf: +opt.crf, stills };
}

(async () => {
  const a = args(process.argv.slice(2));
  if (!fs.existsSync(a.page)) { console.error(`page not found: ${a.page}`); process.exit(2); }
  const browser = await chromium.launch(launchOptions());
  const page = await browser.newPage({ viewport: { width: a.w, height: a.h } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto('file://' + a.page);
  await page.waitForFunction(() => (window.FILM || window.render) && document.fonts.status === 'loaded' && (window.READY === undefined || window.READY === true), null, { timeout: 60000 });
  const kind = await page.evaluate(() => {
    if (window.FILM) { window.FILM.init && window.FILM.init(); window.__ctx = document.querySelector('canvas').getContext('2d'); return 'film'; }
    return 'render';
  });
  const draw = t => page.evaluate(([k, t]) => {
    if (k === 'film') window.FILM.render(window.__ctx, t); else window.render(t);
    return document.querySelector('canvas').toDataURL('image/png').split(',')[1];
  }, [kind, t]);
  if (a.stills) {
    fs.mkdirSync(path.dirname(a.out), { recursive: true });
    const written = [];
    for (const [i, t] of a.stills.entries()) {
      const f = `${a.out}_${i + 1}.png`;
      fs.writeFileSync(f, Buffer.from(await draw(t), 'base64'));
      written.push(`${f} (t=${t}s)`);
    }
    await browser.close();
    if (errors.length) { console.error('page errors:\n' + errors.join('\n')); process.exit(1); }
    console.log(written.join('\n'));
    return;
  }
  const dur = a.to !== undefined ? +a.to : await page.evaluate(() => (window.FILM ? window.FILM.DUR : window.DUR));
  if (!(dur > a.from)) { console.error(`bad duration: ${dur}`); process.exit(2); }
  const frames = Math.round((dur - a.from) * a.fps);
  fs.mkdirSync(path.dirname(a.out), { recursive: true });
  const tmp = a.out + '.partial.mp4';
  const ff = ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(a.fps), '-i', '-'];
  if (a.audio) ff.push('-ss', String(a.from), '-i', path.resolve(a.audio));
  ff.push('-map', '0:v:0');
  if (a.audio) ff.push('-map', '1:a:0', '-c:a', 'aac', '-b:a', '192k', '-shortest');
  ff.push('-c:v', 'libx264', '-preset', 'slow', '-crf', String(a.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp);
  const enc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => enc.on('close', c => (c === 0 ? res() : rej(new Error(`ffmpeg exited ${c}`)))));
  for (let i = 0; i < frames; i++) {
    const t = a.from + i / a.fps;
    const b64 = await draw(t);
    if (!enc.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => enc.stdin.once('drain', r));
    if (errors.length) break;
  }
  enc.stdin.end();
  await browser.close();
  if (errors.length) { console.error('page errors:\n' + errors.join('\n')); try { fs.unlinkSync(tmp); } catch (e) {} process.exit(1); }
  await done;
  fs.renameSync(tmp, a.out);
  console.log(`${a.out} (${frames} frames, ${a.fps} fps, ${kind} contract)`);
})().catch(e => { console.error(e.stack || String(e)); process.exit(1); });
