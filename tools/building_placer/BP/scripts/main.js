// 建築放置台：點方塊 → 圖形選單選建築 → 粒子框預覽 → 以方塊為中心放置。
// 目標 @minecraft/server 2.0.0 / @minecraft/server-ui 2.0.0（遊戲 1.21.90 以上）。
import {
  world,
  system,
  BlockPermutation,
  StructureRotation,
  StructureMirrorAxis,
  StructureSaveMode,
} from '@minecraft/server';
import { ActionFormData, ModalFormData, MessageFormData } from '@minecraft/server-ui';
import { CATALOG } from './catalog.js';

const BLOCK_ID = 'eason:building_placer';
const STATE_PREFIX = 'placer_state:';
const UNDO_KEY = 'placer_undo';
const UNDO_KEEP = 3;
const CELL = 64; // 備份與分批的格子大小（/structure save 上限是 64 寬）
const TICKING_PREFIX = 'placer_tmp_';
const PREVIEW_RANGE = 160;

const ROTATIONS = [StructureRotation.None, StructureRotation.Rotate90, StructureRotation.Rotate180, StructureRotation.Rotate270];
const ROT_LABELS = ['0°（原始方向）', '90°', '180°', '270°'];
const MIRRORS = [StructureMirrorAxis.None, StructureMirrorAxis.X, StructureMirrorAxis.Z];
const MIRROR_LABELS = ['不鏡像', '鏡像 X 軸', '鏡像 Z 軸'];

const sleep = (ticks) => new Promise((r) => system.runTimeout(r, Math.max(1, ticks)));

// ───────────── 放置台狀態（存在世界動態屬性，重開世界還在） ─────────────

const states = new Map(); // key -> state
let statesLoaded = false;

function keyOf(dimensionId, p) {
  return `${dimensionId}|${p.x}|${p.y}|${p.z}`;
}

function parseKey(key) {
  const [dim, x, y, z] = key.split('|');
  return { dim, pos: { x: +x, y: +y, z: +z } };
}

function loadStates() {
  if (statesLoaded) return;
  statesLoaded = true;
  for (const id of world.getDynamicPropertyIds()) {
    if (!id.startsWith(STATE_PREFIX)) continue;
    try {
      states.set(id.slice(STATE_PREFIX.length), JSON.parse(world.getDynamicProperty(id)));
    } catch {
      world.setDynamicProperty(id, undefined);
    }
  }
}

function saveState(key, state) {
  if (state) {
    states.set(key, state);
    world.setDynamicProperty(STATE_PREFIX + key, JSON.stringify(state));
  } else {
    states.delete(key);
    world.setDynamicProperty(STATE_PREFIX + key, undefined);
  }
}

// state = { packName, layout } 或 { custom: 'ns:id', size: [x,y,z] }，加上 rot, mirror, dy, twoPass, backup
function layoutOf(state) {
  if (state.custom) {
    const [sx, sy, sz] = state.size;
    return { title: state.custom, name: '自訂結構', size: state.size, pieces: [[state.custom, 0, 0, 0, sx, sy, sz]] };
  }
  const pack = CATALOG.find((p) => p.name === state.packName);
  const layout = pack?.layouts[state.layout];
  if (!layout) return undefined;
  const title = pack.layouts.length > 1 ? `${pack.name}｜${layout.name}` : pack.name;
  return { title, ...layout };
}

// ───────────── 旋轉／鏡像校正 ─────────────
// 不同版本的旋轉方向與「先鏡像或先旋轉」不一定相同，第一次用時在世界最高層
// 放一個 2×1×3 的測試結構，看三個色塊跑去哪裡，得到每種組合的實際對應。

const transforms = new Map(); // `${rot}_${mirror}` -> { ex:[dx,dz], ez:[dx,dz] }
let calibrated = false;

function assumedTransform(rot, mirror) {
  let ex = [1, 0];
  let ez = [0, 1];
  if (mirror === 1) ex = [-1, 0];
  if (mirror === 2) ez = [0, -1];
  const cw = ([x, z]) => [-z, x]; // 從上往下看順時針 90°：東 → 南
  for (let i = 0; i < rot; i++) {
    ex = cw(ex);
    ez = cw(ez);
  }
  return { ex, ez };
}

function transformOf(rot, mirror) {
  return transforms.get(`${rot}_${mirror}`) ?? assumedTransform(rot, mirror);
}

function calibrate(dimension, at, force = false) {
  if (calibrated && !force) return;
  const sm = world.structureManager;
  const y = dimension.heightRange.max - 2;
  const base = { x: at.x, y, z: at.z };
  const saved = [];
  try {
    for (let dx = 0; dx < 3; dx++)
      for (let dz = 0; dz < 3; dz++) {
        const b = dimension.getBlock({ x: base.x + dx, y, z: base.z + dz });
        if (!b) return; // 區塊沒載入，下次再試
        saved.push([dx, dz, b.permutation]);
      }
    const id = 'placer_cal:test';
    if (sm.get(id)) sm.delete(id);
    const test = sm.createEmpty(id, { x: 2, y: 1, z: 3 }, StructureSaveMode.Memory);
    const white = BlockPermutation.resolve('minecraft:white_wool');
    for (let x = 0; x < 2; x++) for (let z = 0; z < 3; z++) test.setBlockPermutation({ x, y: 0, z }, white);
    test.setBlockPermutation({ x: 0, y: 0, z: 0 }, BlockPermutation.resolve('minecraft:red_wool'));
    test.setBlockPermutation({ x: 1, y: 0, z: 0 }, BlockPermutation.resolve('minecraft:blue_wool'));
    test.setBlockPermutation({ x: 0, y: 0, z: 1 }, BlockPermutation.resolve('minecraft:lime_wool'));
    const air = BlockPermutation.resolve('minecraft:air');
    for (let rot = 0; rot < 4; rot++)
      for (let mirror = 0; mirror < 3; mirror++) {
        for (const [dx, dz] of saved) dimension.getBlock({ x: base.x + dx, y, z: base.z + dz })?.setPermutation(air);
        sm.place(test, dimension, base, { rotation: ROTATIONS[rot], mirror: MIRRORS[mirror], includeEntities: false });
        const found = {};
        for (let dx = 0; dx < 3; dx++)
          for (let dz = 0; dz < 3; dz++) {
            const t = dimension.getBlock({ x: base.x + dx, y, z: base.z + dz })?.typeId;
            if (t) found[t] = [dx, dz];
          }
        const A = found['minecraft:red_wool'];
        const B = found['minecraft:blue_wool'];
        const C = found['minecraft:lime_wool'];
        if (A && B && C) transforms.set(`${rot}_${mirror}`, { ex: [B[0] - A[0], B[1] - A[1]], ez: [C[0] - A[0], C[1] - A[1]] });
      }
    sm.delete(id);
    calibrated = transforms.size === 12;
  } catch (e) {
    console.warn(`[建築放置台] 旋轉校正失敗，改用預設方向：${e}`);
  } finally {
    for (const [dx, dz, perm] of saved) {
      try {
        dimension.getBlock({ x: base.x + dx, y, z: base.z + dz })?.setPermutation(perm);
      } catch {}
    }
  }
}

// ───────────── 由放置台位置算出每一塊的世界座標 ─────────────

function planOf(state, center) {
  const layout = layoutOf(state);
  if (!layout) return undefined;
  const { ex, ez } = transformOf(state.rot, state.mirror);
  const map = (x, z) => [x * ex[0] + z * ez[0], x * ex[1] + z * ez[1]];
  const rectMin = (x0, z0, w, d) => {
    const pts = [map(x0, z0), map(x0 + w - 1, z0), map(x0, z0 + d - 1), map(x0 + w - 1, z0 + d - 1)];
    return [Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1]))];
  };
  const swap = ex[0] === 0; // 旋轉 90/270 時寬深互換
  const [Sx, Sy, Sz] = layout.size;
  const F = swap ? [Sz, Sy, Sx] : [Sx, Sy, Sz];
  const origin = { x: center.x - Math.floor(F[0] / 2), y: center.y + state.dy, z: center.z - Math.floor(F[2] / 2) };
  const lmin = rectMin(0, 0, Sx, Sz);
  const pieces = layout.pieces.map(([id, ox, oy, oz, sx, sy, sz]) => {
    const m = rectMin(ox, oz, sx, sz);
    return {
      id,
      loc: { x: origin.x + m[0] - lmin[0], y: origin.y + oy, z: origin.z + m[1] - lmin[1] },
      size: swap ? { x: sz, y: sy, z: sx } : { x: sx, y: sy, z: sz },
    };
  });
  const o = map(0, 0);
  const corner = { x: origin.x + o[0] - lmin[0], z: origin.z + o[1] - lmin[1] };
  return {
    layout,
    origin,
    size: { x: F[0], y: F[1], z: F[2] },
    max: { x: origin.x + F[0] - 1, y: origin.y + F[1] - 1, z: origin.z + F[2] - 1 },
    pieces,
    corner,
  };
}

// ───────────── 粒子預覽 ─────────────

function drawPreview(dimension, plan, center, players) {
  const a = plan.origin;
  const b = { x: plan.max.x + 1, y: plan.max.y + 1, z: plan.max.z + 1 };
  const total = 4 * (plan.size.x + plan.size.y + plan.size.z);
  const step = Math.max(1, Math.ceil(total / 700));
  const near = (p) => players.some((pl) => Math.abs(pl.location.x - p.x) < 96 && Math.abs(pl.location.z - p.z) < 96 && Math.abs(pl.location.y - p.y) < 96);
  const dot = (p, particle = 'minecraft:villager_happy') => {
    if (!near(p)) return;
    try {
      dimension.spawnParticle(particle, p);
    } catch {}
  };
  const line = (p, axis, len) => {
    for (let t = 0; t <= len; t += step) dot({ ...p, [axis]: p[axis] + t });
  };
  for (const y of [a.y, b.y])
    for (const z of [a.z, b.z]) line({ x: a.x, y, z }, 'x', b.x - a.x);
  for (const y of [a.y, b.y])
    for (const x of [a.x, b.x]) line({ x, y, z: a.z }, 'z', b.z - a.z);
  for (const x of [a.x, b.x])
    for (const z of [a.z, b.z]) line({ x, y: a.y, z }, 'y', b.y - a.y);
  // 藍色柱 = 放置台中心；火焰柱 = 建築原始的西北角（看旋轉方向用）
  const h = Math.min(plan.size.y, 24);
  for (let t = 0; t <= h; t += 2) {
    dot({ x: center.x + 0.5, y: center.y + 1 + t, z: center.z + 0.5 }, 'minecraft:blue_flame_particle');
    dot({ x: plan.corner.x + 0.5, y: plan.origin.y + t, z: plan.corner.z + 0.5 }, 'minecraft:basic_flame_particle');
  }
}

let tick = 0;
system.runInterval(() => {
  loadStates();
  tick++;
  for (const [key, state] of states) {
    const { dim, pos } = parseKey(key);
    let dimension;
    try {
      dimension = world.getDimension(dim);
    } catch {
      continue;
    }
    // 放置台被拆掉就清掉預覽
    if (tick % 4 === 0 && !(job && job.key === key)) {
      let block;
      try {
        block = dimension.getBlock(pos);
      } catch {}
      if (block && block.typeId !== BLOCK_ID) {
        saveState(key, undefined);
        continue;
      }
    }
    const players = dimension.getPlayers().filter((p) => Math.abs(p.location.x - pos.x) < PREVIEW_RANGE * 6 && Math.abs(p.location.z - pos.z) < PREVIEW_RANGE * 6);
    if (!players.length) continue;
    const plan = planOf(state, pos);
    if (!plan) continue;
    drawPreview(dimension, plan, pos, players);
    for (const p of players) {
      if (Math.abs(p.location.x - pos.x) < 12 && Math.abs(p.location.z - pos.z) < 12 && !job) {
        p.onScreenDisplay.setActionBar(
          `§e${plan.layout.title}§r  ${plan.size.x}×${plan.size.y}×${plan.size.z}  旋轉 ${ROT_LABELS[state.rot].replace('（原始方向）', '')}  高度 ${state.dy >= 0 ? '+' : ''}${state.dy}`,
        );
      }
    }
  }
}, 10);

// ───────────── 載入區塊（tickingarea） ─────────────

function rectsOf(r) {
  // 把一個範圍切成 ≤128×128 的小塊，每塊最多 9×9=81 個區塊，不超過 tickingarea 的 100 區塊上限
  const out = [];
  for (let x = r.x0; x <= r.x1; x += 128)
    for (let z = r.z0; z <= r.z1; z += 128) out.push({ x0: x, z0: z, x1: Math.min(r.x1, x + 127), z1: Math.min(r.z1, z + 127) });
  return out;
}

function chunksLoaded(dimension, r, y) {
  for (let cx = Math.floor(r.x0 / 16); cx <= Math.floor(r.x1 / 16); cx++)
    for (let cz = Math.floor(r.z0 / 16); cz <= Math.floor(r.z1 / 16); cz++) {
      try {
        const x = Math.min(Math.max(cx * 16, r.x0), r.x1);
        const z = Math.min(Math.max(cz * 16, r.z0), r.z1);
        if (!dimension.getBlock({ x, y, z })) return false;
      } catch {
        return false;
      }
    }
  return true;
}

function removeTicking(dimension) {
  for (let i = 0; i < 9; i++) {
    try {
      dimension.runCommand(`tickingarea remove ${TICKING_PREFIX}${i}`);
    } catch {}
  }
}

async function ensureLoaded(dimension, r, y) {
  if (chunksLoaded(dimension, r, y)) return true;
  removeTicking(dimension);
  rectsOf(r).forEach((s, i) => {
    try {
      dimension.runCommand(`tickingarea add ${s.x0} ${y} ${s.z0} ${s.x1} ${y} ${s.z1} ${TICKING_PREFIX}${i} true`);
    } catch (e) {
      console.warn(`[建築放置台] tickingarea 加入失敗：${e}`);
    }
  });
  for (let waited = 0; waited < 600; waited += 10) {
    await sleep(10);
    if (job?.cancel) return false;
    if (chunksLoaded(dimension, r, y)) return true;
  }
  return false;
}

// ───────────── 放置流程 ─────────────

let job; // 同時只跑一個放置作業 { key, cancel, player }

function union(rects) {
  return {
    x0: Math.min(...rects.map((r) => r.x0)),
    z0: Math.min(...rects.map((r) => r.z0)),
    x1: Math.max(...rects.map((r) => r.x1)),
    z1: Math.max(...rects.map((r) => r.z1)),
  };
}

const intersects = (a, b) => a.x0 <= b.x1 && b.x0 <= a.x1 && a.z0 <= b.z1 && b.z0 <= a.z1;
const DEBRIS = ['minecraft:item', 'minecraft:falling_block'];

function debrisIn(dimension, r, y0, y1) {
  const out = [];
  for (const type of DEBRIS) {
    try {
      out.push(
        ...dimension.getEntities({
          type,
          location: { x: r.x0, y: y0, z: r.z0 },
          volume: { x: r.x1 - r.x0 + 1, y: y1 - y0 + 1, z: r.z1 - r.z0 + 1 },
        }),
      );
    } catch {}
  }
  return out;
}

/**
 * pieces: [{ id, loc, size }]（size 為旋轉後尺寸）
 * opts: { rotation, mirror, twoPass, backup, title, player }
 * 回傳 undo 紀錄（有備份時）。
 */
async function placePieces(dimension, pieces, box, opts) {
  const sm = world.structureManager;
  const report = (msg) => {
    try {
      opts.player?.onScreenDisplay.setActionBar(msg);
    } catch {}
  };
  const y0 = box.origin.y;
  const y1 = box.max.y;
  const pieceRect = (p) => ({ x0: p.loc.x, z0: p.loc.z, x1: p.loc.x + p.size.x - 1, z1: p.loc.z + p.size.z - 1 });

  // 備份格：以建築範圍左上角為基準的 64×64 網格
  const nx = Math.ceil(box.size.x / CELL);
  const nz = Math.ceil(box.size.z / CELL);
  const jobId = `${Date.now().toString(36)}`;
  const cellRect = (i, j) => ({
    x0: box.origin.x + i * CELL,
    z0: box.origin.z + j * CELL,
    x1: Math.min(box.max.x, box.origin.x + i * CELL + CELL - 1),
    z1: Math.min(box.max.z, box.origin.z + j * CELL + CELL - 1),
  });
  const backedUp = new Set();
  const undo = opts.backup ? { job: jobId, dim: dimension.id, x: box.origin.x, y: y0, z: box.origin.z, nx, nz, title: opts.title } : undefined;

  // 依 64 網格分批：每塊放進「最小角所在的格子」
  const batches = new Map();
  for (const p of pieces) {
    const i = Math.min(nx - 1, Math.max(0, Math.floor((p.loc.x - box.origin.x) / CELL)));
    const j = Math.min(nz - 1, Math.max(0, Math.floor((p.loc.z - box.origin.z) / CELL)));
    const k = `${i},${j}`;
    if (!batches.has(k)) batches.set(k, []);
    batches.get(k).push(p);
  }
  const order = [...batches.keys()].sort((a, b) => {
    const [ai, aj] = a.split(',').map(Number);
    const [bi, bj] = b.split(',').map(Number);
    return aj - bj || ai - bi;
  });

  let done = 0;
  const started = Date.now();
  for (const k of order) {
    if (job?.cancel) break;
    const list = batches.get(k);
    const rects = list.map(pieceRect);
    const touched = union(rects);
    const needBackup = [];
    if (opts.backup)
      for (let i = 0; i < nx; i++)
        for (let j = 0; j < nz; j++) {
          const c = cellRect(i, j);
          if (!backedUp.has(`${i},${j}`) && intersects(c, touched)) needBackup.push([i, j, c]);
        }
    const region = union([touched, ...needBackup.map((n) => n[2])]);
    report(`§e放置中 ${done}/${pieces.length}§r：載入區塊…`);
    const loaded = await ensureLoaded(dimension, region, Math.max(y0, dimension.heightRange.min));
    if (job?.cancel) break;
    if (!loaded) world.sendMessage('§c[建築放置台] 有區塊載入逾時，仍嘗試放置；若有缺塊可再放一次或用復原。');

    for (const [i, j, c] of needBackup) {
      try {
        const id = `placer_undo:${jobId}_${i}_${j}`;
        if (sm.get(id)) sm.delete(id);
        sm.createFromWorld(id, dimension, { x: c.x0, y: y0, z: c.z0 }, { x: c.x1, y: y1, z: c.z1 }, {
          saveMode: StructureSaveMode.World,
          includeEntities: false,
          includeBlocks: true,
        });
      } catch (e) {
        console.warn(`[建築放置台] 備份 ${i},${j} 失敗：${e}`);
      }
      backedUp.add(`${i},${j}`);
    }

    const before = new Set(debrisIn(dimension, touched, y0, y1).map((e) => e.id));
    const placeAll = (includeEntities) => {
      for (const p of list) {
        try {
          sm.place(p.id, dimension, p.loc, { rotation: opts.rotation, mirror: opts.mirror, includeEntities });
        } catch (e) {
          world.sendMessage(`§c[建築放置台] 放置 ${p.id} 失敗：${e}`);
        }
      }
    };
    placeAll(true);
    if (opts.twoPass) {
      // 第二次放置時支撐方塊已經在了，燈籠、火把、沙子等不會再掉
      await sleep(2);
      placeAll(false);
    }
    await sleep(4);
    for (const e of debrisIn(dimension, touched, y0, y1)) {
      if (!before.has(e.id)) {
        try {
          e.remove();
        } catch {}
      }
    }
    done += list.length;
    const sec = Math.round((Date.now() - started) / 1000);
    report(`§e放置中 ${done}/${pieces.length}§r  已用 ${sec} 秒`);
  }
  removeTicking(dimension);
  return undo;
}

function readUndo() {
  try {
    return JSON.parse(world.getDynamicProperty(UNDO_KEY) ?? '[]');
  } catch {
    return [];
  }
}

function writeUndo(list) {
  world.setDynamicProperty(UNDO_KEY, JSON.stringify(list));
}

async function deleteBackups(rec) {
  const sm = world.structureManager;
  let n = 0;
  for (let i = 0; i < rec.nx; i++)
    for (let j = 0; j < rec.nz; j++) {
      try {
        sm.delete(`placer_undo:${rec.job}_${i}_${j}`);
      } catch {}
      if (++n % 20 === 0) await sleep(1);
    }
}

async function startPlacement(player, key, state) {
  const { dim, pos } = parseKey(key);
  const dimension = world.getDimension(dim);
  calibrate(dimension, pos);
  const plan = planOf(state, pos);
  if (!plan) return;
  job = { key, cancel: false, player };
  const t0 = Date.now();
  world.sendMessage(`§a[建築放置台] ${player.name} 開始放置「${plan.layout.title}」，共 ${plan.pieces.length} 塊。`);
  let undo;
  try {
    undo = await placePieces(dimension, plan.pieces, plan, {
      rotation: ROTATIONS[state.rot],
      mirror: MIRRORS[state.mirror],
      twoPass: state.twoPass,
      backup: state.backup,
      title: plan.layout.title,
      player,
    });
  } finally {
    const cancelled = job?.cancel;
    job = undefined;
    const sec = Math.round((Date.now() - t0) / 1000);
    if (undo) {
      const list = readUndo();
      list.push(undo);
      while (list.length > UNDO_KEEP) await deleteBackups(list.shift());
      writeUndo(list);
    }
    if (cancelled) {
      world.sendMessage(`§6[建築放置台] 已停止放置「${plan.layout.title}」。已放好的部分${undo ? '可用「復原上一次放置」還原' : '不會自動還原'}。`);
    } else {
      saveState(key, undefined);
      try {
        const b = dimension.getBlock(pos);
        if (b?.typeId === BLOCK_ID) b.setType('minecraft:air');
      } catch {}
      world.sendMessage(`§a[建築放置台] 「${plan.layout.title}」放置完成，用時 ${sec} 秒。${undo ? '不滿意可放新的放置台並選「復原上一次放置」。' : ''}`);
    }
  }
}

async function startUndo(player) {
  const list = readUndo();
  const rec = list.pop();
  if (!rec) return;
  const sm = world.structureManager;
  const dimension = world.getDimension(rec.dim);
  const pieces = [];
  let maxY = rec.y;
  for (let i = 0; i < rec.nx; i++)
    for (let j = 0; j < rec.nz; j++) {
      const id = `placer_undo:${rec.job}_${i}_${j}`;
      const s = sm.get(id);
      if (!s) continue;
      pieces.push({ id, loc: { x: rec.x + i * CELL, y: rec.y, z: rec.z + j * CELL }, size: s.size });
      maxY = Math.max(maxY, rec.y + s.size.y - 1);
    }
  if (!pieces.length) {
    writeUndo(list);
    player.sendMessage('§c[建築放置台] 找不到備份資料，無法復原。');
    return;
  }
  const box = {
    origin: { x: rec.x, y: rec.y, z: rec.z },
    size: { x: rec.nx * CELL, y: maxY - rec.y + 1, z: rec.nz * CELL },
    max: { x: rec.x + rec.nx * CELL - 1, y: maxY, z: rec.z + rec.nz * CELL - 1 },
  };
  job = { key: 'undo', cancel: false, player };
  world.sendMessage(`§a[建築放置台] ${player.name} 開始復原「${rec.title}」。`);
  try {
    await placePieces(dimension, pieces, box, {
      rotation: StructureRotation.None,
      mirror: StructureMirrorAxis.None,
      twoPass: true,
      backup: false,
      title: rec.title,
      player,
    });
  } finally {
    const cancelled = job?.cancel;
    job = undefined;
    if (!cancelled) {
      writeUndo(list);
      await deleteBackups(rec);
      world.sendMessage(`§a[建築放置台] 已復原「${rec.title}」。`);
    } else {
      world.sendMessage('§6[建築放置台] 復原已停止，備份仍保留，可再按一次復原。');
    }
  }
}

// ───────────── 選單 ─────────────

function sizeText(s) {
  return `${s[0]}×${s[1]}×${s[2]}`;
}

async function pickBuilding(player) {
  const form = new ActionFormData().title('建築放置台').body(`選一座建築（共 ${CATALOG.length} 座）。\n需要先在世界啟用該建築的行為包。`);
  CATALOG.forEach((pack) => {
    const sub = pack.layouts.length > 1 ? `${pack.layouts.length} 種版面` : sizeText(pack.layouts[0].size);
    form.button(`${pack.name}\n§8${sub}`, pack.icon);
  });
  form.button('手動輸入結構 ID\n§8其他行為包的結構', 'textures/placer_ui/edit');
  const res = await form.show(player);
  if (res.canceled || res.selection === undefined) return undefined;
  if (res.selection === CATALOG.length) return pickCustom(player);
  const pack = CATALOG[res.selection];
  if (pack.layouts.length === 1) return { packName: pack.name, layout: 0 };
  const sub = new ActionFormData().title(pack.name).body('選擇要放的版面：');
  pack.layouts.forEach((l) => sub.button(`${l.name}\n§8${sizeText(l.size)}・${l.pieces.length} 塊`, pack.icon));
  const r2 = await sub.show(player);
  if (r2.canceled || r2.selection === undefined) return undefined;
  return { packName: pack.name, layout: r2.selection };
}

async function pickCustom(player) {
  const form = new ModalFormData().title('手動輸入結構 ID').textField('結構 ID', '例如 mystructure:house').submitButton('確定');
  const res = await form.show(player);
  if (res.canceled) return undefined;
  const id = String(res.formValues?.[0] ?? '').trim();
  const s = id && world.structureManager.get(id);
  if (!s) {
    player.sendMessage(`§c[建築放置台] 找不到結構「${id}」，請確認 ID 與行為包是否已啟用。`);
    return undefined;
  }
  return { custom: id, size: [s.size.x, s.size.y, s.size.z] };
}

async function editSettings(player, key, state) {
  const form = new ModalFormData()
    .title('放置設定')
    .dropdown('旋轉', ROT_LABELS, { defaultValueIndex: state.rot })
    .dropdown('鏡像', MIRROR_LABELS, { defaultValueIndex: state.mirror })
    .slider('高度偏移（0＝建築底層與放置台同高）', -64, 64, { defaultValue: state.dy, valueStep: 1 })
    .toggle('防掉落：放兩次，避免燈籠、火把、沙子掉落', { defaultValue: state.twoPass })
    .toggle('建立復原備份（大型建築會佔較多存檔空間）', { defaultValue: state.backup })
    .submitButton('套用');
  const res = await form.show(player);
  if (res.canceled || !res.formValues) return;
  const [rot, mirror, dy, twoPass, backup] = res.formValues;
  saveState(key, { ...state, rot: Number(rot), mirror: Number(mirror), dy: Number(dy), twoPass: !!twoPass, backup: !!backup });
}

function installed(state) {
  const layout = layoutOf(state);
  if (!layout) return false;
  try {
    return !!world.structureManager.get(layout.pieces[0][0]);
  } catch {
    return true; // 無法確認時不阻擋
  }
}

async function confirmPlace(player, key, state) {
  const { pos } = parseKey(key);
  const dimension = player.dimension;
  const plan = planOf(state, pos);
  const hr = dimension.heightRange;
  if (plan.origin.y < hr.min || plan.max.y >= hr.max) {
    player.sendMessage(`§c[建築放置台] 超出世界高度（${hr.min}～${hr.max - 1}），請調整高度偏移。`);
    return;
  }
  const big = plan.size.x * plan.size.z > 256 * 256;
  const form = new MessageFormData()
    .title('確認放置')
    .body(
      `${plan.layout.title}\n` +
        `範圍：(${plan.origin.x}, ${plan.origin.y}, ${plan.origin.z}) ～ (${plan.max.x}, ${plan.max.y}, ${plan.max.z})\n` +
        `尺寸：${plan.size.x}×${plan.size.y}×${plan.size.z}，共 ${plan.pieces.length} 塊\n` +
        `防掉落：${state.twoPass ? '開' : '關'}　復原備份：${state.backup ? '開' : '關'}\n\n` +
        `§c範圍內原有的方塊會被覆蓋。${big ? '\n這座很大，可能要放好幾分鐘，期間請不要關閉世界。' : ''}`,
    )
    .button1('開始放置')
    .button2('取消');
  const res = await form.show(player);
  if (res.canceled || res.selection !== 0) return;
  if (job) {
    player.sendMessage('§c[建築放置台] 已有放置作業進行中。');
    return;
  }
  startPlacement(player, key, state);
}

async function openMenu(player, block) {
  loadStates();
  const key = keyOf(block.dimension.id, block.location);
  const state = states.get(key);
  const undo = readUndo();
  calibrate(block.dimension, block.location);

  if (!state) {
    const pick = await pickBuilding(player);
    if (!pick) return;
    saveState(key, { ...pick, rot: 0, mirror: 0, dy: 0, twoPass: true, backup: true });
    player.sendMessage('§a[建築放置台] 已顯示預覽框。§r綠點＝範圍、藍柱＝中心、火焰柱＝建築原本的西北角。再點一次放置台可確認放置或調整；空手蹲下點擊可快速旋轉 90°。');
    return;
  }

  const plan = planOf(state, block.location);
  if (!plan) {
    saveState(key, undefined);
    return;
  }
  const ok = installed(state);
  const buttons = [];
  const form = new ActionFormData()
    .title(plan.layout.title)
    .body(
      `尺寸 ${plan.size.x}×${plan.size.y}×${plan.size.z}，${plan.pieces.length} 塊\n` +
        `旋轉 ${ROT_LABELS[state.rot]}　${MIRROR_LABELS[state.mirror]}　高度 ${state.dy >= 0 ? '+' : ''}${state.dy}\n` +
        (ok ? '' : '§c找不到這個結構，請確認已啟用該建築的行為包。§r\n') +
        (job ? '§6目前有放置作業進行中。' : ''),
    );
  const add = (text, icon, fn) => {
    form.button(text, icon);
    buttons.push(fn);
  };
  if (job) add('§c停止目前放置', 'textures/placer_ui/stop', () => (job.cancel = true));
  else add('§2確認放置', 'textures/placer_ui/confirm', () => confirmPlace(player, key, state));
  add('調整旋轉／鏡像／高度', 'textures/placer_ui/settings', () => editSettings(player, key, state));
  add('更換建築', 'textures/placer_ui/swap', async () => {
    const pick = await pickBuilding(player);
    if (pick) saveState(key, { ...state, packName: undefined, layout: undefined, custom: undefined, size: undefined, ...pick });
  });
  add('取消預覽', 'textures/placer_ui/trash', () => saveState(key, undefined));
  if (undo.length && !job) add(`復原上一次放置\n§8${undo[undo.length - 1].title}`, 'textures/placer_ui/undo', () => startUndo(player));
  const res = await form.show(player);
  if (res.canceled || res.selection === undefined) return;
  await buttons[res.selection]?.();
}

// ───────────── 方塊自訂元件 ─────────────

system.beforeEvents.startup.subscribe(({ blockComponentRegistry }) => {
  blockComponentRegistry.registerCustomComponent('eason:placer', {
    onPlayerInteract({ block, player }) {
      if (!player) return;
      system.run(() => {
        loadStates();
        const key = keyOf(block.dimension.id, block.location);
        const state = states.get(key);
        const hand = player.getComponent('minecraft:equippable')?.getEquipment('Mainhand');
        if (player.isSneaking && state && !hand && !job) {
          saveState(key, { ...state, rot: (state.rot + 1) % 4 });
          return;
        }
        openMenu(player, block).catch((e) => console.warn(`[建築放置台] 選單錯誤：${e}`));
      });
    },
  });
});

world.afterEvents.worldLoad.subscribe(() => {
  loadStates();
  // 上次沒跑完的作業可能留下 tickingarea
  for (const d of ['overworld', 'nether', 'the_end']) {
    try {
      removeTicking(world.getDimension(d));
    } catch {}
  }
});

// 給離線測試用（遊戲內不會用到）
export const __test = { planOf, transforms, calibrate, assumedTransform };
