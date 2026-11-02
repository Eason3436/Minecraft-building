// Web Worker：下載體素資料 → 組裝分件 → 分塊網格化 → 把幾何回傳主執行緒。
import { buildPaletteInfo, Mesher, decodeVox, writePart } from './mesher.js?v=__BUILD__';

const CHUNK = [64, 32, 64];
let st = null; // { mesher, dims }

async function fetchBytes(url, onBytes) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`下載失敗（HTTP ${res.status}）：${url}`);
  const buf = new Uint8Array(await res.arrayBuffer());
  onBytes(buf.length);
  // 伺服器可能已經用 Content-Encoding 解過 gzip，先看檔頭
  if (buf[0] === 0x1f && buf[1] === 0x8b) {
    const ds = new DecompressionStream('gzip');
    const out = await new Response(new Blob([buf]).stream().pipeThrough(ds)).arrayBuffer();
    return new Uint8Array(out);
  }
  return buf;
}

async function load(msg) {
  const t0 = performance.now();
  const { parts, size, colorsUrl, base } = msg;
  const post = (m, tr) => self.postMessage(m, tr || []);
  post({ type: 'progress', stage: 'download', done: 0, total: parts.length });
  const colorsP = fetch(base + colorsUrl).then((r) => r.json());
  let done = 0, bytes = 0;
  const decoded = new Array(parts.length);
  let next = 0;
  const workerFn = async () => {
    while (next < parts.length) {
      const i = next++;
      const raw = await fetchBytes(base + parts[i].url, (n) => { bytes += n; });
      decoded[i] = decodeVox(raw);
      done++;
      post({ type: 'progress', stage: 'download', done, total: parts.length, bytes });
    }
  };
  await Promise.all(Array.from({ length: Math.min(6, parts.length) }, workerFn));
  const colors = await colorsP;
  const t1 = performance.now();
  post({ type: 'progress', stage: 'assemble' });

  // 全域調色盤
  const keyMap = new Map();
  const blocks = [null];
  const dims = size;
  const cells = (dims[0] + 2) * (dims[1] + 2) * (dims[2] + 2);
  const vol = new Uint16Array(cells);
  for (let i = 0; i < parts.length; i++) {
    const part = decoded[i];
    const remap = new Uint16Array(part.palette.length);
    part.palette.forEach((e, k) => {
      const key = e[0] + (e[1] ? JSON.stringify(e[1]) : '');
      let g = keyMap.get(key);
      if (g === undefined) { g = blocks.length; keyMap.set(key, g); blocks.push({ name: e[0], states: e[1] || {} }); }
      remap[k] = g;
    });
    writePart(vol, dims, part, parts[i].offset, remap);
    decoded[i] = null;
  }
  const info = buildPaletteInfo(blocks, colors);
  const mesher = new Mesher(vol, dims, info, CHUNK);
  st = { mesher, dims };
  const t2 = performance.now();

  const list = mesher.chunkList();
  let nv = 0, ntri = 0;
  for (let i = 0; i < list.length; i++) {
    const [cx, cy, cz] = list[i];
    const r = mesher.mesh(cx, cy, cz);
    if (r) {
      const tr = [];
      for (const l of r.layers) if (l) { nv += l.nv; ntri += l.idx.length / 3; tr.push(l.pos.buffer, l.nor.buffer, l.col.buffer, l.idx.buffer); }
      post({ type: 'chunk', key: `${cx},${cy},${cz}`, cy, layers: r.layers }, tr);
    }
    if (i % 4 === 3 || i === list.length - 1) post({ type: 'progress', stage: 'mesh', done: i + 1, total: list.length });
  }
  const t3 = performance.now();
  post({
    type: 'done', vertices: nv, triangles: ntri, palette: blocks.length - 1, bytes, chunkH: CHUNK[1],
    times: { download: t1 - t0, assemble: t2 - t1, mesh: t3 - t2, total: t3 - t0 },
  });
}

function cut(msg) {
  if (!st) return;
  const { yMax, gen } = msg;
  const { mesher, dims } = st;
  const cy = Math.floor(yMax / CHUNK[1]);
  const t0 = performance.now();
  if (yMax >= 0 && yMax < dims[1]) {
    const nx = Math.ceil(dims[0] / CHUNK[0]), nz = Math.ceil(dims[2] / CHUNK[2]);
    for (let cz = 0; cz < nz; cz++) for (let cx = 0; cx < nx; cx++) {
      const r = mesher.mesh(cx, cy, cz, yMax);
      if (!r) continue;
      const tr = [];
      for (const l of r.layers) if (l) tr.push(l.pos.buffer, l.nor.buffer, l.col.buffer, l.idx.buffer);
      self.postMessage({ type: 'cutChunk', gen, key: `${cx},${cy},${cz}`, layers: r.layers }, tr);
    }
  }
  self.postMessage({ type: 'cutDone', gen, yMax, cy, ms: performance.now() - t0 });
}

self.onmessage = (e) => {
  const m = e.data;
  try {
    if (m.type === 'load') load(m).catch((err) => self.postMessage({ type: 'error', message: String(err && err.message || err) }));
    else if (m.type === 'cut') cut(m);
  } catch (err) {
    self.postMessage({ type: 'error', message: String(err && err.message || err) });
  }
};
