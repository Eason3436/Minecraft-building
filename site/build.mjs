#!/usr/bin/env node
// 建置 Minecraft 建築展示網站：掃描 structures/ 下所有 .mcpack，產生 site/dist/。
//   node site/build.mjs            （npm run build）
// 不需要 Python；sharp（optionalDependencies）裝不起來時改用原始 PNG，不會讓建置失敗。
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { readZip, readStructure, parseLoadLine } from './lib/mcpack.mjs';

const t0 = Date.now();
const SITE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(SITE, '..');
const STRUCT_DIR = path.join(ROOT, 'structures');
const SRC = path.join(SITE, 'src');
const DIST = path.join(SITE, 'dist');
const REPO_URL = 'https://github.com/eason3436/minecraft-building';
const FORMAT = 'MCV1';
const TILE = 64; // part_<i>_<j> 類命名的分件偏移單位

const log = (...a) => console.log('[build]', ...a);
const warn = (...a) => console.warn('[build] 警告：', ...a);

// ---------------------------------------------------------------- 工具
const walk = (d) => fs.readdirSync(d, { withFileTypes: true })
  .sort((a, b) => natCmp(a.name, b.name))
  .flatMap((e) => (e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]));
const collator = new Intl.Collator('zh-Hant', { numeric: true, sensitivity: 'base' });
function natCmp(a, b) { return collator.compare(a, b); }
const sha = (buf, n = 16) => crypto.createHash('sha1').update(buf).digest('hex').slice(0, n);
const mkdirp = (d) => fs.mkdirSync(d, { recursive: true });
const asciiSlug = (s) => s.normalize('NFKD').replace(/[^\x00-\x7f]/g, '').toLowerCase()
  .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
const stripBom = (s) => s.replace(/^﻿/, '');

// ---------------------------------------------------------------- 方塊顏色
const BLOCK_COLORS = JSON.parse(fs.readFileSync(path.join(SITE, 'data', 'block-colors.json'), 'utf8'));
const usedNames = new Set();
function isHidden(name) {
  const c = BLOCK_COLORS[name];
  if (c) return c.alpha === 0;
  return /(^|:)(air|structure_void|barrier|light_block(_\d+)?)$/.test(name);
}
const DYE = { white: [233, 236, 236], orange: [240, 118, 19], magenta: [189, 68, 179], light_blue: [58, 175, 217], yellow: [248, 197, 39], lime: [112, 185, 25], pink: [237, 141, 172], gray: [62, 68, 71], light_gray: [142, 142, 134], cyan: [21, 137, 145], purple: [121, 42, 172], blue: [53, 57, 157], brown: [114, 71, 40], green: [84, 109, 27], red: [161, 39, 34], black: [20, 21, 25] };
function guessColor(name) {
  const n = name.replace(/^minecraft:/, '');
  for (const d of Object.keys(DYE).sort((a, b) => b.length - a.length)) if (n.startsWith(d + '_')) return DYE[d];
  // 去掉形狀字尾，找本體方塊
  const base = n.replace(/_(stairs|slab|wall|fence|fence_gate|door|trapdoor|button|pressure_plate|double_slab)$/, '');
  for (const cand of [base, base + 's', base + '_block', base + '_planks', 'minecraft:' + base]) {
    const c = BLOCK_COLORS['minecraft:' + cand.replace(/^minecraft:/, '')];
    if (c && c.alpha > 0) return c.side;
  }
  return [150, 150, 150];
}

// ---------------------------------------------------------------- 體素編碼
// 檔案格式（gzip 後）：見 site/README.md「資料格式」
function canonicalStates(states) {
  const o = {};
  for (const k of Object.keys(states).sort()) o[k] = states[k];
  return o;
}

function encodeStructure(s) {
  const [X, Y, Z] = s.size;
  const keyMap = new Map();
  const pal = [];
  const remap = new Uint16Array(s.palette.length).fill(0xffff);
  const isAir = new Uint8Array(s.palette.length);
  s.palette.forEach((p, i) => {
    if (p.name === 'minecraft:air') isAir[i] = 1;
    if (isHidden(p.name)) return;
    usedNames.add(p.name);
    const st = canonicalStates(p.states);
    const key = p.name + '|' + JSON.stringify(st);
    let j = keyMap.get(key);
    if (j === undefined) {
      j = pal.length;
      keyMap.set(key, j);
      pal.push(Object.keys(st).length ? [p.name, st] : [p.name]);
    }
    remap[i] = j;
  });
  const prim = s.primary, sec = s.secondary;
  // 輸出順序：y → z → x（x 最快）
  const values = [], lengths = [];
  let cur = -1, run = 0, nonAir = 0, visible = 0;
  const minB = [Infinity, Infinity, Infinity], maxB = [-1, -1, -1];
  for (let y = 0; y < Y; y++) {
    for (let z = 0; z < Z; z++) {
      for (let x = 0; x < X; x++) {
        const i = x * Y * Z + y * Z + z;
        const pi = prim[i];
        let v = 0xffff;
        if (pi >= 0) {
          if (!isAir[pi]) nonAir++;
          v = remap[pi];
        }
        // 含水方塊的次層：主層是空的時候才把水畫出來（其他情況忽略）
        if (v === 0xffff && sec) {
          const si = sec[i];
          if (si >= 0 && remap[si] !== 0xffff) v = remap[si];
        }
        if (v !== 0xffff) {
          visible++;
          if (x < minB[0]) minB[0] = x; if (y < minB[1]) minB[1] = y; if (z < minB[2]) minB[2] = z;
          if (x > maxB[0]) maxB[0] = x; if (y > maxB[1]) maxB[1] = y; if (z > maxB[2]) maxB[2] = z;
        }
        if (v === cur && run < 0xffff) run++;
        else {
          if (run) { values.push(cur); lengths.push(run); }
          cur = v; run = 1;
        }
      }
    }
  }
  if (run) { values.push(cur); lengths.push(run); }
  const palJson = Buffer.from(JSON.stringify(pal), 'utf8');
  const palPad = (palJson.length + 3) & ~3;
  const n = values.length;
  const valBytes = (n * 2 + 3) & ~3;
  const out = Buffer.alloc(20 + palPad + valBytes + n * 2);
  out.write(FORMAT, 0, 'ascii');
  out.writeUInt16LE(X, 4); out.writeUInt16LE(Y, 6); out.writeUInt16LE(Z, 8);
  out.writeUInt16LE(pal.length, 10);
  out.writeUInt32LE(palJson.length, 12);
  out.writeUInt32LE(n, 16);
  palJson.copy(out, 20);
  let p = 20 + palPad;
  for (let i = 0; i < n; i++) out.writeUInt16LE(values[i], p + i * 2);
  p += valBytes;
  for (let i = 0; i < n; i++) out.writeUInt16LE(lengths[i], p + i * 2);
  return {
    data: zlib.gzipSync(out, { level: 9 }),
    nonAir, visible, runs: n, palette: pal.length,
    bounds: visible ? [minB, maxB] : null,
  };
}

// ---------------------------------------------------------------- 分件組裝
const FN_PREFER = /(^|\/)(build|place|all|full|assemble)/;

function functionGroups(funcs, structIds) {
  const buckets = new Map();
  for (const [name, text] of funcs) {
    const loads = [];
    for (const line of text.split(/\r?\n/)) {
      const l = parseLoadLine(line);
      if (!l || !structIds.has(l.id)) continue;
      if (l.rotation !== '0_degrees' || l.mirror !== 'none') continue;
      loads.push(l);
    }
    if (!loads.length) continue;
    let key, label;
    if (loads.length >= 2) { key = 'f:' + name; label = name; }
    else {
      const dir = path.posix.dirname(name);
      const stem = path.posix.basename(name).replace(/\d+$/, '');
      key = 'b:' + dir + '/' + stem;
      label = (dir === '.' ? '' : dir + '/') + stem + '*';
    }
    if (!buckets.has(key)) buckets.set(key, { label, file: name, loads: [] });
    buckets.get(key).loads.push(...loads);
  }
  let groups = [];
  for (const g of buckets.values()) {
    const seen = new Map();
    for (const l of g.loads) if (!seen.has(l.id)) seen.set(l.id, l.pos);
    if (seen.size < 2) continue;
    const min = [0, 1, 2].map((a) => Math.min(...[...seen.values()].map((p) => p[a])));
    const parts = [...seen].map(([id, p]) => ({ id, offset: p.map((v, a) => v - min[a]) }))
      .sort((a, b) => natCmp(a.id, b.id));
    const sig = parts.map((q) => q.id + '@' + q.offset.join(',')).join(';');
    groups.push({ label: g.label, file: g.file, parts, sig, ids: new Set(parts.map((q) => q.id)) });
  }
  // 偏好 build/place 類的檔名作為代表
  groups.sort((a, b) => (FN_PREFER.test(b.file) - FN_PREFER.test(a.file)) || b.parts.length - a.parts.length || natCmp(a.file, b.file));
  const uniq = [];
  for (const g of groups) if (!uniq.some((u) => u.sig === g.sig)) uniq.push(g);
  // 移除是其他組子集合的組（例如只放車站、單列 row_0）
  return uniq.filter((g) => !uniq.some((o) => o !== g && o.ids.size > g.ids.size && [...g.ids].every((id) => o.ids.has(id))));
}

const GRID_RE = /^(.*?)(\d+)_z?(\d+)$/;
function gridGroups(structs) {
  const by = new Map();
  for (const s of structs) {
    const [ns, nm] = s.id.split(':');
    const m = GRID_RE.exec(nm);
    if (!m) continue;
    const prefix = ns + ':' + m[1].replace(/x$/, '');
    if (!by.has(prefix)) by.set(prefix, []);
    by.get(prefix).push({ s, i: +m[2], j: +m[3] });
  }
  const groups = [];
  for (const [prefix, list] of by) {
    if (list.length < 2) continue;
    if (!list.every(({ s }) => s.size[0] <= TILE && s.size[2] <= TILE)) continue;
    const parts = list.map(({ s, i, j }) => ({ id: s.id, offset: [i * TILE, 0, j * TILE] }))
      .sort((a, b) => natCmp(a.id, b.id));
    groups.push({ label: prefix.split(':')[1] + '<i>_<j>', file: null, parts, ids: new Set(parts.map((p) => p.id)) });
  }
  return groups;
}

// ---------------------------------------------------------------- 分類
const CATS = [
  ['紅石', /紅石|計算機|顯示器|刷怪塔|計數器/],
  ['載具', /戰車|戰艦|巡洋艦|戰鬥機|太空梭|登月艙|飛船|潛艇|艦/],
  ['鐵道', /鐵道|鐵路|雙軌|車站|月台|隧道|高架/],
  ['橋梁', /大橋|橋梁|拱橋/],
];
function categorize(name, texts) {
  let primary = '建築';
  for (const [c, re] of CATS) if (re.test(name)) { primary = c; break; }
  const tags = [primary];
  for (const [c, re] of CATS) if (!tags.includes(c) && (re.test(name) || texts.some((t) => re.test(t)))) tags.push(c);
  if (!tags.includes('建築') && /樓|閣|塔|府邸|教堂|宮|城|島|劇院|鬥獸場|競技場|町|街|港/.test(name)) tags.push('建築');
  return tags;
}

// ---------------------------------------------------------------- 圖片
let sharp = null;
try { sharp = (await import('sharp')).default; } catch { warn('沒有 sharp，首頁縮圖改用原始 PNG（lazy-load）'); }
const imageJobs = [];
function queueImage(src, kind) {
  const buf = fs.readFileSync(src);
  const h = sha(buf, 12);
  const job = { src, buf, h, kind, out: {} };
  imageJobs.push(job);
  return job;
}
async function runImageJobs() {
  const sizes = { thumb: 720, large: 1800 };
  let i = 0;
  const worker = async () => {
    while (i < imageJobs.length) {
      const job = imageJobs[i++];
      job.width = null;
      if (!sharp) continue;
      try {
        const meta = await sharp(job.buf).metadata();
        job.width = meta.width; job.height = meta.height;
        for (const [k, w] of Object.entries(sizes)) {
          const rel = `img/${job.h}-${w}.webp`;
          const dst = path.join(DIST, rel);
          if (!fs.existsSync(dst)) {
            await sharp(job.buf).resize({ width: Math.min(w, meta.width), withoutEnlargement: true })
              .webp({ quality: k === 'thumb' ? 78 : 84, effort: 4 }).toFile(dst);
          }
          job.out[k] = rel;
        }
      } catch (e) {
        warn('縮圖失敗，改用原圖：', path.relative(ROOT, job.src), e.message);
        job.out = {};
      }
    }
  };
  await Promise.all([1, 2, 3, 4].map(worker));
}

// ---------------------------------------------------------------- 主流程
fs.rmSync(DIST, { recursive: true, force: true });
mkdirp(path.join(DIST, 'data', 'v'));
mkdirp(path.join(DIST, 'img'));
mkdirp(path.join(DIST, 'files'));

if (!fs.existsSync(STRUCT_DIR)) throw new Error('找不到 structures/ 資料夾');
const packFiles = walk(STRUCT_DIR).filter((f) => f.toLowerCase().endsWith('.mcpack'));
log(`找到 ${packFiles.length} 個 .mcpack`);

const voxCache = new Map(); // hash -> info
const buildings = new Map(); // 資料夾名 -> { name, packs: [] }
let totalBytesIn = 0;

for (const file of packFiles) {
  const rel = path.relative(STRUCT_DIR, file).split(path.sep);
  const bname = rel[0];
  if (rel.length < 2) { warn('mcpack 不在建築資料夾內，略過：', rel.join('/')); continue; }
  const dir = path.dirname(file);
  const relDir = rel.slice(1, -1).join('/');
  const buf = fs.readFileSync(file);
  totalBytesIn += buf.length;
  let zip;
  try { zip = readZip(buf); } catch (e) { warn('無法讀取', rel.join('/'), e.message); continue; }
  let manifest = {};
  const mf = [...zip.keys()].find((k) => /(^|\/)manifest\.json$/i.test(k) && k.split('/').length <= 2);
  if (mf) {
    try { manifest = JSON.parse(stripBom(zip.get(mf)().toString('utf8'))); } catch (e) { warn('manifest.json 解析失敗', rel.join('/')); }
  }
  const prefix = mf && mf.includes('/') ? mf.slice(0, mf.indexOf('/') + 1) : '';
  const header = manifest.header || {};

  // 結構
  const structs = [];
  for (const k of zip.keys()) {
    if (!k.startsWith(prefix + 'structures/') || !k.toLowerCase().endsWith('.mcstructure')) continue;
    const sub = k.slice((prefix + 'structures/').length, -'.mcstructure'.length);
    const parts = sub.split('/');
    const id = parts.length >= 2 ? parts[0] + ':' + parts.slice(1).join('/') : 'mystructure:' + parts[0];
    const raw = zip.get(k)();
    const h = sha(Buffer.concat([Buffer.from(FORMAT), raw]));
    let info = voxCache.get(h);
    if (!info) {
      let s;
      try { s = readStructure(raw); } catch (e) { warn('結構解析失敗', k, e.message); continue; }
      const enc = encodeStructure(s);
      const out = `data/v/${h}.bin`;
      fs.writeFileSync(path.join(DIST, out), enc.data);
      info = { file: out, size: s.size, blocks: enc.nonAir, visible: enc.visible, bytes: enc.data.length, bounds: enc.bounds };
      voxCache.set(h, info);
    }
    structs.push({ id, ...info });
  }
  structs.sort((a, b) => natCmp(a.id, b.id));
  if (!structs.length) { warn('沒有結構檔，略過：', rel.join('/')); continue; }

  // functions
  const funcs = [];
  for (const k of zip.keys()) {
    if (k.startsWith(prefix + 'functions/') && k.endsWith('.mcfunction')) {
      funcs.push([k.slice((prefix + 'functions/').length, -'.mcfunction'.length), stripBom(zip.get(k)().toString('utf8'))]);
    }
  }
  funcs.sort((a, b) => natCmp(a[0], b[0]));
  const structIds = new Set(structs.map((s) => s.id));
  let groups = functionGroups(funcs, structIds);
  if (!groups.length) groups = gridGroups(structs);

  // 同目錄檔案
  const siblings = fs.readdirSync(dir, { withFileTypes: true });
  const txts = siblings.filter((e) => e.isFile() && e.name.toLowerCase().endsWith('.txt')).map((e) => e.name).sort(natCmp);
  const txt = txts.find((n) => n.includes('使用說明')) || txts[0] || null;
  const pngs = siblings.filter((e) => e.isFile() && /\.(png|jpe?g|webp)$/i.test(e.name)).map((e) => path.join(dir, e.name));
  // 不含 mcpack 的子資料夾（例如 預覽圖/）裡的圖片當作圖庫
  for (const e of siblings) {
    if (!e.isDirectory()) continue;
    const sub = path.join(dir, e.name);
    const files = walk(sub);
    if (files.some((f) => f.endsWith('.mcpack'))) continue;
    pngs.push(...files.filter((f) => /\.(png|jpe?g|webp)$/i.test(f)));
  }
  pngs.sort((a, b) => natCmp(path.relative(dir, a), path.relative(dir, b)));

  if (!buildings.has(bname)) buildings.set(bname, { name: bname, packs: [] });
  buildings.get(bname).packs.push({ file, dir, relDir, buf, header, structs, groups, funcs, txt, pngs });
}

// ---------------------------------------------------------------- 整理 catalog
const slugUsed = new Map();
const catalog = { generated: new Date().toISOString(), repo: REPO_URL, buildings: [] };

function nsBase(id) { return id.split(':')[0].replace(/_?\d{6,}$/, '').replace(/_/g, '-'); }
function nsDate(ids) {
  let best = null;
  for (const id of ids) {
    const m = /(\d{2})(\d{2})(\d{2})$/.exec(id.split(':')[0]);
    if (!m) continue;
    const mo = +m[2], d = +m[3];
    if (mo < 1 || mo > 12 || d < 1 || d > 31) continue;
    const s = `20${m[1]}-${m[2]}-${m[3]}`;
    if (!best || s > best) best = s;
  }
  return best;
}

// 先決定 slug（同名衝突時加短雜湊）
const bList = [...buildings.values()];
for (const b of bList) {
  b.packs.sort((a, c) => natCmp(a.relDir, c.relDir));
  b.slugBase = asciiSlug(nsBase(b.packs[0].structs[0].id)) || 'b';
  slugUsed.set(b.slugBase, (slugUsed.get(b.slugBase) || 0) + 1);
}
for (const b of bList) {
  b.slug = slugUsed.get(b.slugBase) > 1 ? `${b.slugBase}-${sha(Buffer.from(b.name, 'utf8'), 4)}` : b.slugBase;
}

for (const b of bList) {
  const versions = [];
  const vidUsed = new Set();
  for (const [vi, pk] of b.packs.entries()) {
    let vid = asciiSlug(pk.relDir);
    if (!vid) vid = pk.header.version ? 'v' + pk.header.version.join('-') : 'v' + (vi + 1);
    while (vidUsed.has(vid)) vid += '-' + (vi + 1);
    vidUsed.add(vid);
    const filesDir = `files/${b.slug}/${vid}`;
    mkdirp(path.join(DIST, filesDir));
    const verStr = Array.isArray(pk.header.version) ? pk.header.version.join('.') : '';
    let packName = (pk.header.name || b.name).trim();
    let label = packName.startsWith(b.name) ? packName.slice(b.name.length).trim() : packName;
    if (!label || label === b.name) label = pk.relDir ? pk.relDir.split('/').filter((s) => !/^分區成果$/.test(s)).join(' / ') : '';
    if (!label) label = '版本';
    if (b.packs.length > 1 && pk.relDir && label !== pk.relDir && /^v\d+$/i.test(pk.relDir.split('/').pop()) && !label.includes(pk.relDir.split('/').pop())) {
      label += ` (${pk.relDir.split('/').pop()})`;
    }

    // 下載檔
    const packOut = `${filesDir}/${b.slug}.mcpack`;
    fs.writeFileSync(path.join(DIST, packOut), pk.buf);
    const files = { mcpack: { url: packOut, name: path.basename(pk.file), bytes: pk.buf.length } };
    if (pk.txt) {
      const src = path.join(pk.dir, pk.txt);
      const out = `${filesDir}/${b.slug}-guide.txt`;
      fs.copyFileSync(src, path.join(DIST, out));
      files.txt = { url: out, name: pk.txt, bytes: fs.statSync(src).size };
    }
    const images = [];
    let gi = 0;
    for (const src of pk.pngs) {
      const base = path.basename(src);
      const kind = /整體渲染/.test(base) && path.dirname(src) === pk.dir ? 'render'
        : /內部剖視|剖視/.test(base) && path.dirname(src) === pk.dir ? 'cutaway' : 'gallery';
      const ext = path.extname(src).toLowerCase();
      const out = `${filesDir}/${b.slug}-${kind === 'gallery' ? 'g' + String(++gi).padStart(2, '0') : kind}${ext}`;
      fs.copyFileSync(src, path.join(DIST, out));
      const title = base.replace(/\.[^.]+$/, '').replace(new RegExp('^' + b.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '_?'), '').replace(/_/g, ' ');
      images.push({ kind, title, name: base, full: out, bytes: fs.statSync(src).size, job: queueImage(src, kind) });
    }
    images.sort((a, c) => ({ render: 0, cutaway: 1, gallery: 2 }[a.kind] - { render: 0, cutaway: 1, gallery: 2 }[c.kind]));

    // 模型
    const byId = new Map(pk.structs.map((s) => [s.id, s]));
    const models = [];
    const idUsed = new Set();
    const shortNames = pk.structs.map((s) => s.id.split(':')[1]);
    const dupShort = shortNames.length !== new Set(shortNames).size;
    pk.groups.forEach((g, gi2) => {
      const parts = g.parts.map((p) => ({ ...byId.get(p.id), offset: p.offset }));
      const size = [0, 1, 2].map((a) => Math.max(...parts.map((p) => p.offset[a] + p.size[a])));
      const mid = gi2 === 0 ? 'all' : `all-${gi2 + 1}`;
      idUsed.add(mid);
      const lab = pk.groups.length === 1 ? '整體組裝' : `組裝：${groupName(g)}`;
      models.push({
        id: mid, label: lab, kind: 'assembly', size,
        blocks: parts.reduce((t, p) => t + p.blocks, 0),
        parts: parts.map((p) => ({ id: p.id, url: p.file, offset: p.offset, size: p.size, bytes: p.bytes })),
        source: g.file ? `functions/${g.file}.mcfunction` : '依分件命名推算（每格 64）',
      });
    });
    for (const s of pk.structs) {
      let mid = asciiSlug(s.id.replace(':', '-')) || 'm';
      while (idUsed.has(mid)) mid += '-x';
      idUsed.add(mid);
      const [ns, nm] = s.id.split(':');
      const inGroup = pk.groups.some((g) => g.ids.has(s.id));
      models.push({
        id: mid, label: dupShort ? `${nsBase(s.id)} / ${nm}` : nm,
        kind: pk.structs.length === 1 ? 'single' : inGroup ? 'part' : 'module',
        size: s.size, blocks: s.blocks,
        parts: [{ id: s.id, url: s.file, offset: [0, 0, 0], size: s.size, bytes: s.bytes }],
      });
    }
    // 結構 ID 與在組裝中的偏移
    const offsets = new Map();
    if (pk.groups[0]) for (const p of pk.groups[0].parts) offsets.set(p.id, p.offset);
    const structures = pk.structs.map((s) => ({ id: s.id, size: s.size, blocks: s.blocks, offset: offsets.get(s.id) || null }));
    const entryFns = pk.funcs.map(([n]) => n).filter((n) => /^(.*\/)?(start|build|place|prepare|cleanup|station|stop|cancel|port_build|berth\d*)$/.test(n));

    versions.push({
      id: vid, label, rel: pk.relDir, packName, version: verStr,
      description: (pk.header.description || '').trim(),
      blocks: pk.structs.reduce((t, s) => t + s.blocks, 0),
      files, images, models, structures, functions: entryFns,
      date: nsDate(pk.structs.map((s) => s.id)),
    });
  }
  // 預設版本：方塊最多者（同數取較新）
  let def = 0;
  versions.forEach((v, i) => { if (v.blocks > versions[def].blocks || (v.blocks === versions[def].blocks && (v.date || '') > (versions[def].date || ''))) def = i; });
  const dv = versions[def];
  const texts = versions.flatMap((v) => [v.description, v.packName, v.label]);
  catalog.buildings.push({
    slug: b.slug, name: b.name,
    tags: categorize(b.name, texts),
    date: versions.map((v) => v.date).filter(Boolean).sort().pop() || null,
    defaultVersion: dv.id,
    versions,
  });
}

function groupName(g) {
  if (g.file) return path.posix.basename(g.file).replace(/_?\d*$/, '') || g.file;
  return g.label;
}

catalog.buildings.sort((a, b) => (b.date || '').localeCompare(a.date || '') || natCmp(a.name, b.name));

// 圖片縮圖
await runImageJobs();
for (const b of catalog.buildings) {
  for (const v of b.versions) {
    for (const im of v.images) {
      const j = im.job; delete im.job;
      im.thumb = j.out.thumb || im.full;
      im.large = j.out.large || im.full;
      if (j.width) { im.w = j.width; im.h = j.height; }
    }
  }
  const dv = b.versions.find((v) => v.id === b.defaultVersion);
  const cover = dv.images.find((i) => i.kind === 'render') || dv.images[0] || b.versions.flatMap((v) => v.images)[0];
  b.cover = cover ? cover.thumb : null;
}

// 顏色表（只輸出用到的方塊）：name -> [top r,g,b, side r,g,b, bottom r,g,b, alpha*255]
const colors = {};
for (const n of [...usedNames].sort()) {
  const c = BLOCK_COLORS[n];
  if (c) colors[n] = [...c.top, ...c.side, ...c.bottom, Math.round(c.alpha * 255)];
  else { const g = guessColor(n); colors[n] = [...g, ...g, ...g, 255]; warn('顏色表沒有', n, '，用推測色'); }
}
fs.writeFileSync(path.join(DIST, 'data', 'colors.json'), JSON.stringify(colors));
fs.writeFileSync(path.join(DIST, 'catalog.json'), JSON.stringify(catalog));

// ---------------------------------------------------------------- 前端檔案
const copyDir = (from, to) => {
  mkdirp(to);
  for (const e of fs.readdirSync(from, { withFileTypes: true })) {
    const s = path.join(from, e.name), d = path.join(to, e.name);
    if (e.isDirectory()) copyDir(s, d); else fs.copyFileSync(s, d);
  }
};
copyDir(SRC, DIST);
// 版本字串：避免瀏覽器快取舊的 js/css
const buildId = sha(Buffer.from(catalog.generated + Math.random()), 8);
for (const f of ['index.html']) {
  const p = path.join(DIST, f);
  fs.writeFileSync(p, fs.readFileSync(p, 'utf8').replaceAll('__BUILD__', buildId));
}
for (const f of fs.readdirSync(DIST).filter((f) => f.endsWith('.js'))) {
  const p = path.join(DIST, f);
  fs.writeFileSync(p, fs.readFileSync(p, 'utf8').replaceAll('__BUILD__', buildId));
}
// three.js（npm 依賴）→ dist/vendor，改成相對路徑 import，不需要 import map
const threeDir = path.join(ROOT, 'node_modules', 'three');
if (!fs.existsSync(threeDir)) throw new Error('找不到 node_modules/three，請先執行 npm install');
mkdirp(path.join(DIST, 'vendor'));
for (const f of ['three.core.js', 'three.module.js']) {
  const src = path.join(threeDir, 'build', f);
  if (fs.existsSync(src)) fs.copyFileSync(src, path.join(DIST, 'vendor', f));
}
const orbit = fs.readFileSync(path.join(threeDir, 'examples', 'jsm', 'controls', 'OrbitControls.js'), 'utf8')
  .replace(/from\s+['"]three['"]/g, "from './three.module.js'");
fs.writeFileSync(path.join(DIST, 'vendor', 'OrbitControls.js'), orbit);
fs.copyFileSync(path.join(threeDir, 'LICENSE'), path.join(DIST, 'vendor', 'three-LICENSE.txt'));

// ---------------------------------------------------------------- 統計
let distBytes = 0, distFiles = 0, biggest = 0;
for (const f of walk(DIST)) { const s = fs.statSync(f).size; distBytes += s; distFiles++; biggest = Math.max(biggest, s); }
const voxBytes = [...voxCache.values()].reduce((t, v) => t + v.bytes, 0);
log(`建築 ${catalog.buildings.length} 棟、版本 ${catalog.buildings.reduce((t, b) => t + b.versions.length, 0)} 個、獨立結構 ${voxCache.size} 個`);
log(`體素資料 ${(voxBytes / 1048576).toFixed(1)} MB（原始 mcpack ${(totalBytesIn / 1048576).toFixed(1)} MB）`);
log(`dist：${distFiles} 個檔案、${(distBytes / 1048576).toFixed(1)} MB（最大單檔 ${(biggest / 1048576).toFixed(1)} MB）`);
log(`完成，用時 ${((Date.now() - t0) / 1000).toFixed(1)} 秒`);
