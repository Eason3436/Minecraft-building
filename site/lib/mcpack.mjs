// .mcpack（ZIP）與 .mcstructure（未壓縮 little-endian NBT）讀取工具，零依賴。
import zlib from 'node:zlib';

// ---------------------------------------------------------------- ZIP
/** 讀 ZIP central directory，回傳 Map<路徑, () => Buffer>（延遲解壓）。 */
export function readZip(buf) {
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 22 - 65535); i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error('不是有效的 ZIP 檔（找不到 EOCD）');
  let count = buf.readUInt16LE(eocd + 10);
  let cdOffset = buf.readUInt32LE(eocd + 16);
  // ZIP64
  if (cdOffset === 0xffffffff || count === 0xffff) {
    const loc = eocd - 20;
    if (loc >= 0 && buf.readUInt32LE(loc) === 0x07064b50) {
      const z64 = Number(buf.readBigUInt64LE(loc + 8));
      count = Number(buf.readBigUInt64LE(z64 + 32));
      cdOffset = Number(buf.readBigUInt64LE(z64 + 48));
    }
  }
  const entries = new Map();
  let p = cdOffset;
  for (let n = 0; n < count; n++) {
    if (buf.readUInt32LE(p) !== 0x02014b50) throw new Error('ZIP central directory 損毀');
    const flags = buf.readUInt16LE(p + 8);
    const method = buf.readUInt16LE(p + 10);
    let csize = buf.readUInt32LE(p + 20);
    let usize = buf.readUInt32LE(p + 24);
    const nlen = buf.readUInt16LE(p + 28);
    const xlen = buf.readUInt16LE(p + 30);
    const clen = buf.readUInt16LE(p + 32);
    let lho = buf.readUInt32LE(p + 42);
    const nameBuf = buf.subarray(p + 46, p + 46 + nlen);
    const name = (flags & 0x800) || isUtf8(nameBuf) ? nameBuf.toString('utf8') : nameBuf.toString('latin1');
    // ZIP64 extra
    let x = p + 46 + nlen;
    const xend = x + xlen;
    while (x + 4 <= xend) {
      const id = buf.readUInt16LE(x), sz = buf.readUInt16LE(x + 2);
      if (id === 0x0001) {
        let q = x + 4;
        if (usize === 0xffffffff) { usize = Number(buf.readBigUInt64LE(q)); q += 8; }
        if (csize === 0xffffffff) { csize = Number(buf.readBigUInt64LE(q)); q += 8; }
        if (lho === 0xffffffff) { lho = Number(buf.readBigUInt64LE(q)); q += 8; }
      }
      x += 4 + sz;
    }
    p = xend + clen;
    if (name.endsWith('/')) continue;
    entries.set(name.replace(/\\/g, '/'), () => {
      if (buf.readUInt32LE(lho) !== 0x04034b50) throw new Error('ZIP local header 損毀: ' + name);
      const ln = buf.readUInt16LE(lho + 26), lx = buf.readUInt16LE(lho + 28);
      const start = lho + 30 + ln + lx;
      const data = buf.subarray(start, start + csize);
      if (method === 0) return Buffer.from(data);
      if (method === 8) return zlib.inflateRawSync(data);
      throw new Error(`不支援的 ZIP 壓縮方式 ${method}: ${name}`);
    });
  }
  return entries;
}

function isUtf8(b) {
  try { new TextDecoder('utf-8', { fatal: true }).decode(b); return true; } catch { return false; }
}

// ---------------------------------------------------------------- NBT (little-endian)
/**
 * 解析基岩版 little-endian NBT。Int list 會直接變成 Int32Array（block_indices 很大）。
 * 回傳 { name, value }；compound 是一般物件。
 */
export function readNBT(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  let p = 0;
  const dec = new TextDecoder('utf-8');
  const str = () => {
    const n = dv.getUint16(p, true); p += 2;
    const s = dec.decode(buf.subarray(p, p + n)); p += n; return s;
  };
  const read = (t) => {
    switch (t) {
      case 1: { const v = dv.getInt8(p); p += 1; return v; }
      case 2: { const v = dv.getInt16(p, true); p += 2; return v; }
      case 3: { const v = dv.getInt32(p, true); p += 4; return v; }
      case 4: { const v = dv.getBigInt64(p, true); p += 8; return v; }
      case 5: { const v = dv.getFloat32(p, true); p += 4; return v; }
      case 6: { const v = dv.getFloat64(p, true); p += 8; return v; }
      case 7: { const n = dv.getInt32(p, true); p += 4; const v = buf.subarray(p, p + n); p += n; return v; }
      case 8: return str();
      case 9: {
        const et = dv.getUint8(p); p += 1;
        const n = dv.getInt32(p, true); p += 4;
        if (et === 3) {
          const a = new Int32Array(n);
          for (let i = 0; i < n; i++) { a[i] = dv.getInt32(p, true); p += 4; }
          return a;
        }
        const arr = new Array(Math.max(0, n));
        for (let i = 0; i < n; i++) arr[i] = read(et);
        return arr;
      }
      case 10: {
        const o = {};
        for (;;) {
          const ct = dv.getUint8(p); p += 1;
          if (ct === 0) break;
          const k = str();
          o[k] = read(ct);
        }
        return o;
      }
      case 11: { const n = dv.getInt32(p, true); p += 4; const a = new Int32Array(n); for (let i = 0; i < n; i++) { a[i] = dv.getInt32(p, true); p += 4; } return a; }
      case 12: { const n = dv.getInt32(p, true); p += 4; const a = new Array(n); for (let i = 0; i < n; i++) { a[i] = dv.getBigInt64(p, true); p += 8; } return a; }
      default: throw new Error(`未知的 NBT tag ${t} @${p}`);
    }
  };
  const t = dv.getUint8(p); p += 1;
  const name = str();
  return { name, value: read(t) };
}

/**
 * 解析 .mcstructure，回傳
 * { size:[X,Y,Z], palette:[{name, states}], primary:Int32Array, secondary:Int32Array|null, origin }
 * 索引 = x*(Y*Z) + y*Z + z
 */
export function readStructure(buf) {
  const root = readNBT(buf).value;
  const size = root.size;
  const st = root.structure;
  const layers = st.block_indices;
  const pal = st.palette?.default?.block_palette || [];
  const palette = pal.map((b) => ({ name: b.name, states: plainStates(b.states || {}) }));
  return {
    size: [size[0], size[1], size[2]],
    palette,
    primary: layers[0],
    secondary: layers[1] && layers[1].length ? layers[1] : null,
    origin: root.structure_world_origin ? Array.from(root.structure_world_origin) : [0, 0, 0],
  };
}

function plainStates(s) {
  const o = {};
  for (const [k, v] of Object.entries(s)) {
    if (typeof v === 'bigint') o[k] = Number(v);
    else if (v instanceof Uint8Array) o[k] = Array.from(v);
    else o[k] = v;
  }
  return o;
}

// ---------------------------------------------------------------- functions
const LOAD_RE = /structure\s+load\s+("?)([A-Za-z0-9_.\-]+:[A-Za-z0-9_.\-/]+)\1\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+(\S+))?(?:\s+(\S+))?/;

/** 從一行 mcfunction 取出 structure load。座標若有 ^ 回傳 null。 */
export function parseLoadLine(line) {
  const s = line.trim();
  if (!s || s.startsWith('#')) return null;
  const m = LOAD_RE.exec(s);
  if (!m) return null;
  const coord = (c) => {
    if (c.startsWith('^')) return null;
    const rel = c.startsWith('~');
    const v = rel ? (c.length > 1 ? Number(c.slice(1)) : 0) : Number(c);
    return Number.isFinite(v) ? { v, rel } : null;
  };
  const xyz = [coord(m[3]), coord(m[4]), coord(m[5])];
  if (xyz.some((c) => !c)) return null;
  let rotation = '0_degrees', mirror = 'none';
  if (m[6] && /_degrees$/.test(m[6])) rotation = m[6];
  if (m[7] && /^(none|x|z|xz)$/.test(m[7])) mirror = m[7];
  // execute ... positioned <x y z> ... run structure load
  let pre = [0, 0, 0];
  const pos = /positioned\s+(\S+)\s+(\S+)\s+(\S+)\s/.exec(s.slice(0, m.index));
  if (pos) {
    const pc = [coord(pos[1]), coord(pos[2]), coord(pos[3])];
    if (pc.every(Boolean) && pc.every((c) => c.rel)) pre = pc.map((c) => c.v);
  }
  return {
    id: m[2],
    pos: xyz.map((c, i) => c.v + (c.rel ? pre[i] : 0)),
    rel: xyz.map((c) => c.rel),
    rotation,
    mirror,
  };
}
