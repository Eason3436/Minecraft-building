#!/usr/bin/env node
// 本機預覽 site/dist：node site/serve.mjs [port]（npm run preview）
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = path.join(path.dirname(fileURLToPath(import.meta.url)), 'dist');
const port = Number(process.argv[2] || process.env.PORT || 4173);
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp',
  '.jpg': 'image/jpeg', '.txt': 'text/plain; charset=utf-8', '.bin': 'application/octet-stream', '.mcpack': 'application/octet-stream',
};
http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(DIST, path.normalize(p));
  if (!f.startsWith(DIST)) { res.writeHead(403).end(); return; }
  fs.stat(f, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' }).end('404'); return; }
    const ext = path.extname(f).toLowerCase();
    const headers = { 'content-type': TYPES[ext] || 'application/octet-stream', 'content-length': st.size, 'cache-control': 'no-cache' };
    if (ext === '.mcpack') headers['content-disposition'] = 'attachment';
    res.writeHead(200, headers);
    fs.createReadStream(f).pipe(res);
  });
}).listen(port, () => console.log(`預覽：http://localhost:${port}/`));
