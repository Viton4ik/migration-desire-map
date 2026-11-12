// Headless render: node render/render.js [mode] [args]
//   chunk  <out.mp4> n0 n1        -> silent H.264 of global frames [n0, n1)
//   video  <out.mp4> [t0] [t1]   -> H.264 1920x1080 30fps, frames piped to ffmpeg
//   frames <outdir> t1,t2,...     -> PNG stills at given times
//   tech   <outdir>               -> technical check frames
// Serves the project folder over a local HTTP server so canvas export is never tainted.
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '..');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.json': 'application/json', '.wav': 'audio/wav', '.mp3': 'audio/mpeg' };
function serve() {
  return new Promise(res => {
    const srv = http.createServer((q, r) => {
      const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { r.writeHead(404); r.end(); MISSING.push(q.url); return; }
      r.writeHead(200, { 'content-type': MIME[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(r);
    }).listen(0, () => res(srv));
  });
}
const MISSING = [];
(async () => {
  const [mode, out, a1, a2] = process.argv.slice(2);
  const srv = await serve();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(`http://localhost:${srv.address().port}/index.html?render=1`);
  await page.evaluate(() => window.READY);
  const canvas = page.locator('#c');
  const E = await page.evaluate(() => ({ fps: EPISODE.fps, dur: EPISODE.duration }));
  const t0c = Date.now();
  if (mode === 'video') {
    const t0 = a1 ? +a1 : 0, t1 = a2 ? +a2 : E.dur;
    const n = Math.round((t1 - t0) * E.fps);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(E.fps), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', String(E.fps), '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) {
      const t = t0 + i / E.fps;
      await page.evaluate(t => window.drawFrame(t), t);
      const buf = await canvas.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log(JSON.stringify({ frames: n, seconds: (Date.now() - t0c) / 1000, msPerFrame: Math.round((Date.now() - t0c) / n) }));
  } else if (mode === 'chunk') {
    // global frame indices [n0, n1): frame n shows t = n / fps on the single episode timeline
    const n0 = +a1, n1 = +a2;
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(E.fps), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', String(E.fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let n = n0; n < n1; n++) {
      await page.evaluate(t => window.drawFrame(t), n / E.fps);
      const buf = await canvas.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log(JSON.stringify({ chunk: [n0, n1], seconds: (Date.now() - t0c) / 1000 }));
  } else if (mode === 'checkpoint') {
    // continuation state at global frame n (the first frame of the next region)
    const n = +a1;
    const cp = await page.evaluate(n => {
      const t = n / EPISODE.fps; drawFrame(t); const st = stateAt(t);
      const cnt = {}; for (const k in EPISODE.statuses) cnt[k] = 0; for (const s of st.visited) cnt[s.status]++;
      return { frame: n, t, camera: { ...camAt(t) }, cameraStill: JSON.stringify(camAt(t)) === JSON.stringify(camAt(t + 1 / EPISODE.fps)),
        shot: shotAt(t), visited: st.visited.map(s => ({ code: s.code, status: s.status, activate: s.activate, reaction: s.reaction })),
        counters: cnt, progress: [st.visited.length, EPISODE.totalCountries], current: st.current && st.current.code,
        recent: st.visited.slice(-5).reverse().map(s => s.code),
        clouds: { seed: EPISODE.seed, anchors: CLOUDS.length, sample: CLOUDS.slice(0, 3).map(c => ({ x: +c.x.toFixed(1), y: +c.y.toFixed(1), s: +c.s.toFixed(1), ph: +c.ph.toFixed(3) })) },
        animationClock: 'global t (faces, clouds, blinks use the episode time, never a per-clip time)' };
    }, n);
    fs.writeFileSync(out, JSON.stringify(cp, null, 1)); console.log(JSON.stringify({ checkpoint: out, still: cp.cameraStill }));
  } else if (mode === 'frames') {
    fs.mkdirSync(out, { recursive: true });
    for (const t of a1.split(',').map(Number)) {
      await page.evaluate(t => window.drawFrame(t), t);
      await canvas.screenshot({ path: path.join(out, `frame_${t.toFixed(2).replace('.', '_')}s.png`) });
    }
  } else if (mode === 'tech') {
    fs.mkdirSync(out, { recursive: true });
    const kinds = await page.evaluate(() => ['statuses', ...(EPISODE.techChecks || []).map(x => x.kind)]);
    for (const k of kinds) {
      await page.evaluate(k => window.drawTech(k), k);
      await canvas.screenshot({ path: path.join(out, `check_${k}.png`) });
    }
  }
  const jsErr = await page.evaluate(() => window.JS_ERRORS || []);
  console.log(JSON.stringify({ errors: errors.concat(jsErr), missing: MISSING }));
  await browser.close(); srv.close();
})();
