// 體素網格化（給 Web Worker 用，也能在 Node 測試）。
// - 體積 vol：Uint16Array，外圍各留 1 格空白（padding），索引 (x+1) + PX*((z+1) + PZ*(y+1))
// - 值 0 = 空，其餘 = 全域調色盤 id
// - 分塊網格化，只產生外露面；立方體面做 greedy 合併（同方塊、同 AO 才合併），附每頂點 AO
import { classify, dynBoxes, K_EMPTY, K_CUBE, K_BOXES, K_CROSS, K_DYN, L_OPAQUE, L_TRANS, L_GLOW, F_NONE, F_FENCE, F_PANE, F_WALL, F_NETHER_FENCE } from './blocks.js?v=__BUILD__';

// 方向：0 +X 1 -X 2 +Y 3 -Y 4 +Z 5 -Z；(u, v) 軸滿足 u × v = n（逆時針朝外）
export const DIRS = [
  { an: 0, sg: 1, au: 1, av: 2 },
  { an: 0, sg: -1, au: 2, av: 1 },
  { an: 1, sg: 1, au: 2, av: 0 },
  { an: 1, sg: -1, au: 0, av: 2 },
  { an: 2, sg: 1, au: 0, av: 1 },
  { an: 2, sg: -1, au: 1, av: 0 },
];
const OPPD = [1, 0, 3, 2, 5, 4];
const NORMALS = [[127, 0, 0], [-127, 0, 0], [0, 127, 0], [0, -127, 0], [0, 0, 127], [0, 0, -127]];
// 遮擋格線：每個軸向的面用世界座標 (U, V) 軸，讓 +X / -X 對得上
const MASK_AXES = [[2, 1], [0, 2], [0, 1]];
const AO_CURVE = [0.52, 0.70, 0.85, 1.0];

// ---------------------------------------------------------------- 調色盤資訊
export function buildPaletteInfo(blocks, colors) {
  // blocks[0] 保留為空
  const n = blocks.length;
  const kind = new Uint8Array(n), layer = new Uint8Array(n), family = new Uint8Array(n);
  const solid = new Uint8Array(n); // 不透明完整立方體（遮擋鄰面 + AO）
  const masks = new Uint16Array(n * 6); // 各面覆蓋格（4×4）
  const faceCol = new Uint8Array(n * 6 * 4);
  const group = new Uint16Array(n);
  const crossH = new Uint8Array(n);
  const boxes = new Array(n).fill(null);
  const dyn = new Array(n).fill(null);
  const groupIds = new Map();
  for (let i = 1; i < n; i++) {
    const { name, states } = blocks[i];
    const c = colors[name] || [150, 150, 150, 150, 150, 150, 150, 150, 150, 255];
    const alpha = c[9] / 255;
    const k = classify(name, states || {}, alpha);
    kind[i] = k.kind; layer[i] = k.layer; family[i] = k.family || F_NONE;
    if (!groupIds.has(name)) groupIds.set(name, groupIds.size + 1);
    group[i] = groupIds.get(name);
    if (k.boxes) boxes[i] = k.boxes;
    if (k.dyn) dyn[i] = { type: k.dyn, cache: new Array(16) };
    if (k.crossH) crossH[i] = k.crossH;
    // 面顏色：top / side / bottom；有 pillar_axis 的方塊端面跟著軸轉
    const top = [c[0], c[1], c[2]], side = [c[3], c[4], c[5]], bot = [c[6], c[7], c[8]];
    const axis = states && states.pillar_axis;
    const glow = k.layer === L_GLOW;
    for (let d = 0; d < 6; d++) {
      let col = d === 2 ? top : d === 3 ? bot : side;
      if (axis === 'x') col = d <= 1 ? top : side;
      else if (axis === 'z') col = d >= 4 ? top : side;
      const o = (i * 6 + d) * 4;
      const g = glow ? 1.12 : 1;
      faceCol[o] = Math.min(255, col[0] * g); faceCol[o + 1] = Math.min(255, col[1] * g); faceCol[o + 2] = Math.min(255, col[2] * g);
      // 不透明層：alpha 略低於 255 代表「鏤空」（樹葉），著色器用格點雜湊挖洞
      faceCol[o + 3] = k.layer === L_TRANS ? Math.max(40, c[9]) : (alpha < 1 && alpha >= 0.9 ? 250 : 255);
    }
    if (k.kind === K_CUBE && k.layer !== L_TRANS) {
      solid[i] = 1;
      for (let d = 0; d < 6; d++) masks[i * 6 + d] = 0xffff;
    } else if (k.kind === K_BOXES && k.layer !== L_TRANS) {
      for (const b of k.boxes) {
        for (let d = 0; d < 6; d++) {
          const { an, sg } = DIRS[d];
          const plane = sg > 0 ? b[an + 3] : b[an];
          if (plane !== (sg > 0 ? 16 : 0)) continue;
          const [ua, va] = MASK_AXES[an];
          masks[i * 6 + d] |= coveredCells(b[ua], b[ua + 3], b[va], b[va + 3]);
        }
      }
    }
  }
  return { n, kind, layer, family, solid, masks, faceCol, group, crossH, boxes, dyn };
}

// 完全被 [u0,u1]×[v0,v1] 覆蓋的 4×4 格
function coveredCells(u0, u1, v0, v1) {
  let m = 0;
  for (let cv = 0; cv < 4; cv++) for (let cu = 0; cu < 4; cu++) {
    if (u0 <= cu * 4 && u1 >= cu * 4 + 4 && v0 <= cv * 4 && v1 >= cv * 4 + 4) m |= 1 << (cv * 4 + cu);
  }
  return m;
}
// 與 [u0,u1]×[v0,v1] 有重疊的格
function touchedCells(u0, u1, v0, v1) {
  let m = 0;
  for (let cv = 0; cv < 4; cv++) for (let cu = 0; cu < 4; cu++) {
    if (u0 < cu * 4 + 4 && u1 > cu * 4 && v0 < cv * 4 + 4 && v1 > cv * 4) m |= 1 << (cv * 4 + cu);
  }
  return m;
}

// ---------------------------------------------------------------- 輸出緩衝
class Buf {
  constructor(cap = 4096) { this.pos = new Int16Array(cap * 3); this.nor = new Int8Array(cap * 3); this.col = new Uint8Array(cap * 4); this.idx = new Uint32Array(cap * 1.5); this.nv = 0; this.ni = 0; }
  grow() {
    const cap = (this.pos.length / 3) * 2;
    const p = new Int16Array(cap * 3); p.set(this.pos); this.pos = p;
    const n = new Int8Array(cap * 3); n.set(this.nor); this.nor = n;
    const c = new Uint8Array(cap * 4); c.set(this.col); this.col = c;
    const ix = new Uint32Array(cap * 1.5); ix.set(this.idx); this.idx = ix;
  }
  /** 4 個頂點（逆時針）。p = [x,y,z]*4（1/16 單位）、shade = 4 個亮度 0..1、flip = 換對角線 */
  quad(p, nrm, r, g, b, a, s0, s1, s2, s3, flip) {
    if (this.nv + 4 > this.pos.length / 3) this.grow();
    const v = this.nv, P = this.pos, N = this.nor, C = this.col;
    for (let k = 0; k < 4; k++) {
      const o = (v + k) * 3;
      P[o] = p[k * 3]; P[o + 1] = p[k * 3 + 1]; P[o + 2] = p[k * 3 + 2];
      N[o] = nrm[0]; N[o + 1] = nrm[1]; N[o + 2] = nrm[2];
      const s = k === 0 ? s0 : k === 1 ? s1 : k === 2 ? s2 : s3;
      const oc = (v + k) * 4;
      C[oc] = r * s; C[oc + 1] = g * s; C[oc + 2] = b * s; C[oc + 3] = a;
    }
    const I = this.idx; let i = this.ni;
    if (flip) { I[i] = v + 1; I[i + 1] = v + 2; I[i + 2] = v + 3; I[i + 3] = v + 1; I[i + 4] = v + 3; I[i + 5] = v; }
    else { I[i] = v; I[i + 1] = v + 1; I[i + 2] = v + 2; I[i + 3] = v; I[i + 4] = v + 2; I[i + 5] = v + 3; }
    this.ni += 6; this.nv += 4;
  }
  take() {
    if (!this.nv) return null;
    const nv = this.nv;
    const idx = nv <= 65535 ? Uint16Array.from(this.idx.subarray(0, this.ni)) : this.idx.slice(0, this.ni);
    return { pos: this.pos.slice(0, nv * 3), nor: this.nor.slice(0, nv * 3), col: this.col.slice(0, nv * 4), idx, nv };
  }
  reset() { this.nv = 0; this.ni = 0; }
}

// ---------------------------------------------------------------- 網格化
export class Mesher {
  /** vol：含 padding 的體積；dims = [X,Y,Z]（不含 padding） */
  constructor(vol, dims, info, chunk = [64, 32, 64]) {
    this.vol = vol; this.dims = dims; this.info = info; this.chunk = chunk;
    this.PX = dims[0] + 2; this.PZ = dims[2] + 2;
    const [cw, ch, cd] = chunk;
    this.L = new Uint16Array((cw + 2) * (ch + 2) * (cd + 2));
    this.mask = new Int32Array(Math.max(cw, ch, cd) ** 2);
    this.bufs = [new Buf(), new Buf(), new Buf()];
    this.tmp = new Int16Array(12);
  }

  chunkList() {
    const [X, Y, Z] = this.dims, [cw, ch, cd] = this.chunk;
    const list = [];
    for (let cy = 0; cy < Math.ceil(Y / ch); cy++) for (let cz = 0; cz < Math.ceil(Z / cd); cz++) for (let cx = 0; cx < Math.ceil(X / cw); cx++) list.push([cx, cy, cz]);
    return list;
  }

  /** 網格化一個分塊；yMax（含）以上視為空（剖切）。回傳 { layers: [opaque, trans, glow] } */
  mesh(cx, cy, cz, yMax = Infinity) {
    const [X, Y, Z] = this.dims, [cw, ch, cd] = this.chunk;
    const x0 = cx * cw, y0 = cy * ch, z0 = cz * cd;
    const W = Math.min(cw, X - x0), H = Math.min(ch, Y - y0), D = Math.min(cd, Z - z0);
    const LW = W + 2, LD = D + 2, LH = H + 2;
    const L = this.L, vol = this.vol, PX = this.PX, PZ = this.PZ;
    // 複製分塊（含 1 格邊界）到區域緩衝
    let any = false;
    for (let ly = 0; ly < LH; ly++) {
      const y = y0 - 1 + ly;
      const rowBase = ly * LW * LD;
      if (y < 0 || y >= Y || y > yMax) { L.fill(0, rowBase, rowBase + LW * LD); continue; }
      for (let lz = 0; lz < LD; lz++) {
        const z = z0 - 1 + lz;
        const src = x0 + PX * ((z + 1) + PZ * (y + 1)); // x0-1 的 padded 索引 = x0
        const dst = rowBase + lz * LW;
        L.set(vol.subarray(src, src + LW), dst);
      }
    }
    // 只要內部有東西才做
    for (let ly = 1; ly <= H && !any; ly++) for (let lz = 1; lz <= D && !any; lz++) {
      const b = ly * LW * LD + lz * LW;
      for (let lx = 1; lx <= W; lx++) if (L[b + lx]) { any = true; break; }
    }
    if (!any) return null;
    for (const b of this.bufs) b.reset();
    const S = [1, LW * LD, LW];
    const dimsL = [W, H, D];
    const org = [x0, y0, z0];
    this.greedy(L, S, dimsL, org);
    this.shapes(L, S, dimsL, org);
    return { layers: this.bufs.map((b) => b.take()) };
  }

  greedy(L, S, dimsL, org) {
    const { kind, layer, solid, group, faceCol, masks } = this.info;
    const mask = this.mask;
    const p = this.tmp;
    for (let d = 0; d < 6; d++) {
      const { an, sg, au, av } = DIRS[d];
      const od = OPPD[d];
      const sn = S[an] * sg, su = S[au], sv = S[av];
      const NU = dimsL[au], NV = dimsL[av], NN = dimsL[an];
      const nrm = NORMALS[d];
      for (let s = 0; s < NN; s++) {
        // 建立遮罩
        let has = false;
        for (let j = 0; j < NV; j++) {
          for (let i = 0; i < NU; i++) {
            const li = (s + 1) * S[an] + (i + 1) * su + (j + 1) * sv;
            const id = L[li];
            let key = 0;
            if (id && kind[id] === K_CUBE) {
              const nb = L[li + sn];
              const lay = layer[id];
              if (!(masks[nb * 6 + od] === 0xffff) && !(lay === L_TRANS && group[nb] === group[id] && kind[nb] === K_CUBE)) {
                let ao = 0xff;
                if (lay === L_OPAQUE) {
                  const q = li + sn;
                  const a = solid[L[q - su]], b = solid[L[q + su]], c = solid[L[q - sv]], e = solid[L[q + sv]];
                  const c0 = a && c ? 0 : 3 - (a + c + solid[L[q - su - sv]]);
                  const c1 = b && c ? 0 : 3 - (b + c + solid[L[q + su - sv]]);
                  const c2 = b && e ? 0 : 3 - (b + e + solid[L[q + su + sv]]);
                  const c3 = a && e ? 0 : 3 - (a + e + solid[L[q - su + sv]]);
                  ao = c0 | (c1 << 2) | (c2 << 4) | (c3 << 6);
                }
                key = id * 256 + ao;
                has = true;
              }
            }
            mask[i + j * NU] = key;
          }
        }
        if (!has) continue;
        // greedy 合併
        const plane = (org[an] + s + (sg > 0 ? 1 : 0)) * 16;
        for (let j = 0; j < NV; j++) {
          for (let i = 0; i < NU;) {
            const key = mask[i + j * NU];
            if (!key) { i++; continue; }
            let w = 1;
            while (i + w < NU && mask[i + w + j * NU] === key) w++;
            let h = 1;
            outer: for (; j + h < NV; h++) {
              for (let k = 0; k < w; k++) if (mask[i + k + (j + h) * NU] !== key) break outer;
            }
            for (let hh = 0; hh < h; hh++) mask.fill(0, i + (j + hh) * NU, i + w + (j + hh) * NU);
            const id = key >>> 8, ao = key & 0xff;
            const u0 = (org[au] + i) * 16, u1 = (org[au] + i + w) * 16;
            const v0 = (org[av] + j) * 16, v1 = (org[av] + j + h) * 16;
            setQuad(p, an, au, av, plane, u0, u1, v0, v1);
            const o = (id * 6 + d) * 4;
            const lay = layer[id];
            const a0 = ao & 3, a1 = (ao >> 2) & 3, a2 = (ao >> 4) & 3, a3 = (ao >> 6) & 3;
            const flip = Math.abs(a0 - a2) > Math.abs(a1 - a3);
            this.bufs[lay].quad(p, nrm, faceCol[o], faceCol[o + 1], faceCol[o + 2], faceCol[o + 3],
              AO_CURVE[a0], AO_CURVE[a1], AO_CURVE[a2], AO_CURVE[a3], flip);
            i += w;
          }
        }
      }
    }
  }

  shapes(L, S, dimsL, org) {
    const info = this.info;
    const { kind, layer, faceCol, masks, family, boxes, crossH, dyn } = info;
    const [W, H, D] = dimsL;
    const p = this.tmp;
    for (let ly = 1; ly <= H; ly++) for (let lz = 1; lz <= D; lz++) {
      const rb = ly * S[1] + lz * S[2];
      for (let lx = 1; lx <= W; lx++) {
        const li = rb + lx;
        const id = L[li];
        if (!id) continue;
        const k = kind[id];
        if (k === K_CUBE || k === K_EMPTY) continue;
        const wx = (org[0] + lx - 1) * 16, wy = (org[1] + ly - 1) * 16, wz = (org[2] + lz - 1) * 16;
        const buf = this.bufs[layer[id]];
        if (k === K_CROSS) {
          const h = crossH[id];
          const o = (id * 6 + 4) * 4;
          const r = faceCol[o], g = faceCol[o + 1], b = faceCol[o + 2], a = faceCol[o + 3];
          const up = NORMALS[2];
          const lo = 2, hi = 14;
          // 兩片斜面，各兩面
          const quads = [
            [lo, lo, hi, hi], [hi, hi, lo, lo], [lo, hi, hi, lo], [hi, lo, lo, hi],
          ];
          for (const [ax, az, bx, bz] of quads) {
            p[0] = wx + ax; p[1] = wy; p[2] = wz + az;
            p[3] = wx + bx; p[4] = wy; p[5] = wz + bz;
            p[6] = wx + bx; p[7] = wy + h; p[8] = wz + bz;
            p[9] = wx + ax; p[10] = wy + h; p[11] = wz + az;
            buf.quad(p, up, r, g, b, a, 0.86, 0.86, 1, 1, false);
          }
          continue;
        }
        let bl = boxes[id];
        if (k === K_DYN) bl = this.dynFor(id, L, li, S);
        if (!bl) continue;
        for (let bi = 0; bi < bl.length; bi++) {
          const bx = bl[bi];
          for (let d = 0; d < 6; d++) {
            const { an, sg, au, av } = DIRS[d];
            const plane = sg > 0 ? bx[an + 3] : bx[an];
            const onEdge = plane === (sg > 0 ? 16 : 0);
            if (onEdge) {
              const nb = L[li + sg * S[an]];
              if (nb) {
                const [ua, va] = MASK_AXES[an];
                const t = touchedCells(bx[ua], bx[ua + 3], bx[va], bx[va + 3]);
                if ((t & ~masks[nb * 6 + OPPD[d]]) === 0) continue;
                const f = family[id];
                if (f && family[nb] && (f === family[nb] || (f === F_PANE && family[nb] === F_WALL) || (f === F_WALL && family[nb] === F_PANE)) && an !== 1) continue;
                // 同種半透明方塊相鄰（玻璃板接玻璃塊）也略過
                if (layer[id] === L_TRANS && kind[nb] === K_CUBE && info.group[nb] === info.group[id]) continue;
              }
            } else if (coveredByOther(bl, bi, an, sg, plane, au, av)) continue;
            setQuad(p, an, au, av, wx * (an === 0) + wy * (an === 1) + wz * (an === 2) + plane,
              (au === 0 ? wx : au === 1 ? wy : wz) + bx[au], (au === 0 ? wx : au === 1 ? wy : wz) + bx[au + 3],
              (av === 0 ? wx : av === 1 ? wy : wz) + bx[av], (av === 0 ? wx : av === 1 ? wy : wz) + bx[av + 3]);
            const o = (id * 6 + d) * 4;
            const sh = d === 3 ? 0.8 : 0.96;
            buf.quad(p, NORMALS[d], faceCol[o], faceCol[o + 1], faceCol[o + 2], faceCol[o + 3], sh, sh, sh, sh, false);
          }
        }
      }
    }
  }

  dynFor(id, L, li, S) {
    const { family, masks, dyn } = this.info;
    const f = family[id];
    const nbs = [L[li + 1], L[li - 1], L[li + S[2]], L[li - S[2]]];
    const faceTo = [1, 0, 5, 4]; // 鄰居朝向本格的面
    let c = 0;
    for (let k = 0; k < 4; k++) {
      const nb = nbs[k];
      if (!nb) continue;
      const nf = family[nb];
      const ok = masks[nb * 6 + faceTo[k]] === 0xffff || (nf && (nf === f || (f === F_PANE && nf === F_WALL) || (f === F_WALL && nf === F_PANE) || (f === F_FENCE && nf === F_FENCE)));
      if (ok) c |= 1 << k;
    }
    const dd = dyn[id];
    if (!dd.cache[c]) dd.cache[c] = dynBoxes(dd.type, [c & 1, (c >> 1) & 1, (c >> 2) & 1, (c >> 3) & 1]);
    return dd.cache[c];
  }
}

function coveredByOther(bl, bi, an, sg, plane, au, av) {
  const a = bl[bi];
  for (let k = 0; k < bl.length; k++) {
    if (k === bi) continue;
    const b = bl[k];
    if (sg > 0 ? b[an] !== plane : b[an + 3] !== plane) continue;
    if (b[au] <= a[au] && b[au + 3] >= a[au + 3] && b[av] <= a[av] && b[av + 3] >= a[av + 3]) return true;
  }
  return false;
}

// 4 個頂點：(u0,v0) (u1,v0) (u1,v1) (u0,v1)
function setQuad(p, an, au, av, plane, u0, u1, v0, v1) {
  p[an] = plane; p[au] = u0; p[av] = v0;
  p[3 + an] = plane; p[3 + au] = u1; p[3 + av] = v0;
  p[6 + an] = plane; p[6 + au] = u1; p[6 + av] = v1;
  p[9 + an] = plane; p[9 + au] = u0; p[9 + av] = v1;
}

// ---------------------------------------------------------------- 解碼 .bin（已解 gzip）
export function decodeVox(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  const magic = String.fromCharCode(buf[0], buf[1], buf[2], buf[3]);
  if (magic !== 'MCV1') throw new Error('資料格式錯誤');
  const X = dv.getUint16(4, true), Y = dv.getUint16(6, true), Z = dv.getUint16(8, true);
  const palLen = dv.getUint32(12, true), runs = dv.getUint32(16, true);
  const palette = JSON.parse(new TextDecoder().decode(buf.subarray(20, 20 + palLen)));
  let p = 20 + ((palLen + 3) & ~3);
  const values = new Uint16Array(buf.buffer.slice(buf.byteOffset + p, buf.byteOffset + p + runs * 2));
  p += (runs * 2 + 3) & ~3;
  const lengths = new Uint16Array(buf.buffer.slice(buf.byteOffset + p, buf.byteOffset + p + runs * 2));
  return { size: [X, Y, Z], palette, values, lengths };
}

/** 把一個分件寫進體積。remap：分件調色盤 → 全域 id（0xffff 視為空）。 */
export function writePart(vol, dims, part, offset, remap) {
  const PX = dims[0] + 2, PZ = dims[2] + 2;
  const [X, Y, Z] = part.size;
  const { values, lengths } = part;
  let x = 0, y = 0, z = 0;
  const ox = offset[0] + 1, oy = offset[1] + 1, oz = offset[2] + 1;
  let row = ox + PX * (oz + PZ * oy);
  for (let r = 0; r < values.length; r++) {
    const v = values[r];
    let len = lengths[r];
    const g = v === 0xffff ? 0 : remap[v];
    while (len > 0) {
      const take = Math.min(len, X - x);
      if (g) vol.fill(g, row + x, row + x + take);
      x += take; len -= take;
      if (x === X) {
        x = 0; z++;
        if (z === Z) { z = 0; y++; }
        row = ox + PX * ((oz + z) + PZ * (oy + y));
      }
    }
  }
}
