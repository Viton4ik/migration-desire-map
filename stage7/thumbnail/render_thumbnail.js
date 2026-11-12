// Render thumbnail.html to thumbnail.png (1280x720) and a 320 px preview. usage: node render_thumbnail.js
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const root = __dirname, types = { '.html': 'text/html', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, b) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(b); });
}).listen(0, async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('requestfailed', q => errs.push('failed ' + q.url()));
  await p.goto(`http://127.0.0.1:${srv.address().port}/thumbnail.html`);
  await p.waitForSelector('body[data-ready="1"]', { timeout: 30000 }); await p.waitForTimeout(300);
  await (await p.$('#c')).screenshot({ path: path.join(root, 'thumbnail.png') });
  console.log(errs.length ? errs.join('\n') : 'no page errors'); await b.close(); srv.close();
});
