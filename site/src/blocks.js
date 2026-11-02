// 方塊外型分類：把 (名稱, states) 轉成網格化需要的資訊。
// 座標單位 1/16 格，box = [x0, y0, z0, x1, y1, z1]，x 東、y 上、z 南（與 Minecraft 相同）。
//
// kind：0 空、1 立方體（可 greedy 合併）、2 固定外型（多個 box）、3 十字面植物、4 依鄰居連接（柵欄/玻璃板類，缺 state 時）
// layer：0 不透明、1 半透明、2 發光（不受光照）

export const K_EMPTY = 0, K_CUBE = 1, K_BOXES = 2, K_CROSS = 3, K_DYN = 4;
export const L_OPAQUE = 0, L_TRANS = 1, L_GLOW = 2;
// 連接家族
export const F_NONE = 0, F_FENCE = 1, F_NETHER_FENCE = 2, F_PANE = 3, F_WALL = 4;

const GLOW = /^(glowstone|sea_lantern|shroomlight|\w+_froglight|lit_redstone_lamp|lit_pumpkin|beacon|magma|lava|flowing_lava|end_rod|(\w+_)?lantern|(\w+_)?torch|colored_torch_\w+|underwater_torch|campfire|soul_campfire|fire|soul_fire|conduit|glow_lichen|sea_pickle|lit_\w+_ore|redstone_ore_lit|crying_obsidian|respawn_anchor|enchanting_table|end_gateway|amethyst_cluster|ochre_froglight|verdant_froglight|pearlescent_froglight|copper_bulb|lit_copper_bulb|\w+_copper_bulb|creaking_heart|glow_berries|cave_vines_\w*berries|lit_blast_furnace|lit_furnace|lit_smoker)$/;
const NOT_GLOW = /^(unlit_redstone_torch|redstone_torch_unlit|torchflower|torchflower_crop|jack_o_lantern_unlit)$/;

const FLOWERS = /^(poppy|dandelion|blue_orchid|allium|azure_bluet|\w+_tulip|oxeye_daisy|cornflower|lily_of_the_valley|wither_rose|torchflower|open_eyeblossom|closed_eyeblossom|cactus_flower|red_flower|yellow_flower)$/;
const PLANTS_FULL = /^(sunflower|lilac|rose_bush|peony|tall_grass|large_fern|pitcher_plant|double_plant|tall_dry_grass|reeds|sugar_cane|kelp|kelp_plant|twisting_vines|weeping_vines|cave_vines\w*|bamboo_sapling|big_dripleaf|small_dripleaf_block|hanging_roots|tall_seagrass|seagrass|firefly_bush|bush)$/;
const PLANTS = /(_sapling$|^(short_grass|tallgrass|fern|deadbush|dead_bush|short_dry_grass|wheat|carrots|potatoes|beetroot|nether_wart|sweet_berry_bush|brown_mushroom|red_mushroom|crimson_fungus|warped_fungus|crimson_roots|warped_roots|nether_sprouts|spore_blossom|azalea_sapling|mangrove_propagule|pink_petals_cross|amethyst_cluster|large_amethyst_bud|medium_amethyst_bud|small_amethyst_bud|pointed_dripstone|torchflower_crop|pitcher_crop|melon_stem|pumpkin_stem|cobweb|web|sculk_vein_cross)$|_coral$|_coral_fan$)/;

const box = (x0, y0, z0, x1, y1, z1) => [x0, y0, z0, x1, y1, z1];

// 以「朝 +X（東）」定義的 box 旋轉到 facing：0=E(+X) 1=W(-X) 2=S(+Z) 3=N(-Z)
function rotBox(b, f) {
  if (f === 0) return b;
  const tr = (x, z) => (f === 1 ? [16 - x, 16 - z] : f === 2 ? [16 - z, x] : [z, 16 - x]);
  const [ax, az] = tr(b[0], b[2]), [bx, bz] = tr(b[3], b[5]);
  return [Math.min(ax, bx), b[1], Math.min(az, bz), Math.max(ax, bx), b[4], Math.max(az, bz)];
}
const flipY = (b) => [b[0], 16 - b[4], b[2], b[3], 16 - b[1], b[5]];
const CARD = { east: 0, west: 1, south: 2, north: 3 };
// facing_direction 0下 1上 2北 3南 4西 5東 → 水平 facing 索引
const FD = { 2: 3, 3: 2, 4: 1, 5: 0 };

/** 牆面貼附物：attach = 貼附的那一側（0E 1W 2S 3N），thickness、y 範圍。 */
function plate(attach, t, y0 = 0, y1 = 16, inset = 0) {
  // 先定義貼在 +X 側（東牆）的板子，再旋轉
  return rotBox([16 - t, y0, inset, 16, y1, 16 - inset], attach);
}
const OPP = [1, 0, 3, 2];

function fenceBoxes(c /* [e,w,s,n] */) {
  const out = [box(6, 0, 6, 10, 16, 10)];
  const arm = (f) => [rotBox(box(10, 6, 7, 16, 9, 9), f), rotBox(box(10, 12, 7, 16, 15, 9), f)];
  for (let f = 0; f < 4; f++) if (c[f]) out.push(...arm(f));
  return out;
}
function paneBoxes(c) {
  const out = [box(7, 0, 7, 9, 16, 9)];
  for (let f = 0; f < 4; f++) if (c[f]) out.push(rotBox(box(9, 0, 7, 16, 16, 9), f));
  return out;
}
function wallBoxes(c /* 0 none 1 short 2 tall */, post) {
  const out = [];
  const any = c.some((v) => v);
  if (post || !any) out.push(box(4, 0, 4, 12, 16, 12));
  for (let f = 0; f < 4; f++) if (c[f]) out.push(rotBox(box(8, 0, 5, 16, c[f] === 2 ? 16 : 14, 11), f));
  return out;
}

const CONN = ['east', 'west', 'south', 'north'];

/**
 * 分類一個方塊。回傳
 * { kind, layer, boxes?, family?, crossH?, conn? (動態連接用) }
 */
export function classify(fullName, st, alpha) {
  const n = fullName.replace(/^minecraft:/, '');
  let layer = alpha < 0.9 ? L_TRANS : L_OPAQUE;
  if (GLOW.test(n) && !NOT_GLOW.test(n)) {
    if (!(st.extinguished === 1 || st.extinguished === true) && !(/candle/.test(n) && !st.lit)) layer = L_GLOW;
  }
  if (/candle/.test(n) && st.lit) layer = L_GLOW;
  const R = (boxes, extra = {}) => ({ kind: K_BOXES, layer, boxes, ...extra });

  if (alpha === 0) return { kind: K_EMPTY, layer };
  // ---- 半磚
  if (/_slab$/.test(n) && !/double_slab$/.test(n)) {
    const top = st['minecraft:vertical_half'] === 'top' || st.top_slot_bit === 1;
    return R([top ? box(0, 8, 0, 16, 16, 16) : box(0, 0, 0, 16, 8, 16)]);
  }
  // ---- 樓梯
  if (/_stairs$/.test(n)) {
    const d = st.weirdo_direction | 0;
    const f = [0, 1, 2, 3][d] ?? 0;
    let b = [box(0, 0, 0, 8, 8, 16), box(8, 0, 0, 16, 8, 16), box(8, 8, 0, 16, 16, 16)];
    b = b.map((x) => rotBox(x, f));
    if (st.upside_down_bit) b = b.map(flipY);
    return R(b);
  }
  // ---- 柵欄門
  if (/fence_gate$/.test(n)) {
    const f = CARD[st['minecraft:cardinal_direction']] ?? (st.direction != null ? [2, 1, 3, 0][st.direction & 3] : 3);
    const alongX = f === 2 || f === 3; // 朝南北 → 門板沿 X
    let b;
    if (st.open_bit) b = [box(0, 5, 7, 2, 16, 9), box(14, 5, 7, 16, 16, 9)];
    else b = [box(0, 5, 7, 2, 16, 9), box(14, 5, 7, 16, 16, 9), box(2, 6, 7, 14, 9, 9), box(2, 12, 7, 14, 15, 9)];
    if (!alongX) b = b.map((x) => rotBox(x, 2));
    return R(b, { family: F_FENCE });
  }
  // ---- 柵欄
  if (/(^|_)fence$/.test(n)) {
    const family = n === 'nether_brick_fence' ? F_NETHER_FENCE : F_FENCE;
    if (st['minecraft:connection_east'] !== undefined) {
      return R(fenceBoxes(CONN.map((c) => st['minecraft:connection_' + c] | 0)), { family });
    }
    return { kind: K_DYN, layer, family, dyn: 'fence' };
  }
  // ---- 玻璃板、鐵欄杆
  if (/glass_pane$|^iron_bars$|_bars$/.test(n)) {
    if (st['minecraft:connection_east'] !== undefined) {
      return R(paneBoxes(CONN.map((c) => st['minecraft:connection_' + c] | 0)), { family: F_PANE });
    }
    return { kind: K_DYN, layer, family: F_PANE, dyn: 'pane' };
  }
  // ---- 牆
  if (/_wall$/.test(n) && !/(wall_sign|wall_banner|wall_fan|wall_torch|wall_head|wall_skull|wall_hanging_sign)$/.test(n)) {
    if (st.wall_connection_type_east !== undefined) {
      const v = (s) => (s === 'tall' ? 2 : s === 'short' ? 1 : 0);
      return R(wallBoxes(CONN.map((c) => v(st['wall_connection_type_' + c])), st.wall_post_bit), { family: F_WALL });
    }
    return { kind: K_DYN, layer, family: F_WALL, dyn: 'wall' };
  }
  // ---- 門
  if (/(^|_)door$/.test(n) && !/trapdoor$/.test(n)) {
    // 基岩版 cardinal_direction 與 Java facing 差 90°：south→E、west→S、north→W、east→N；板子在 facing 的反側
    const cd = st['minecraft:cardinal_direction'];
    const javaFacing = { south: 0, west: 2, north: 1, east: 3 }[cd] ?? (st.direction != null ? [0, 2, 1, 3][st.direction & 3] : 0);
    const attach = OPP[javaFacing];
    return R([plate(attach, 3)]);
  }
  // ---- 活板門
  if (/trapdoor$/.test(n)) {
    const f = [0, 1, 2, 3][st.direction & 3]; // 0E 1W 2S 3N（Java facing）
    if (st.open_bit) return R([plate(OPP[f], 3)]);
    return R([st.upside_down_bit ? box(0, 13, 0, 16, 16, 16) : box(0, 0, 0, 16, 3, 16)]);
  }
  // ---- 薄層
  if (/carpet$/.test(n)) return R([box(0, 0, 0, 16, 1, 16)]);
  if (/pressure_plate$/.test(n)) return R([box(1, 0, 1, 15, 1, 15)]);
  if (n === 'snow_layer') { const h = ((st.height | 0) + 1) * 2; return h >= 16 ? { kind: K_CUBE, layer } : R([box(0, 0, 0, 16, h, 16)]); }
  if (/(^|_)rail$/.test(n) || n === 'redstone_wire' || n === 'tripwire' || n === 'trip_wire') {
    if (n === 'tripwire' || n === 'trip_wire') return { kind: K_EMPTY, layer };
    return R([box(0, 0, 0, 16, 1, 16)]);
  }
  if (/(repeater|comparator)$/.test(n)) return R([box(0, 0, 0, 16, 2, 16)]);
  if (/daylight_detector/.test(n)) return R([box(0, 0, 0, 16, 6, 16)]);
  if (n === 'waterlily' || n === 'lily_pad' || n === 'frog_spawn') return R([box(1, 0, 1, 15, 1, 15)]);
  if (/^(pink_petals|wildflowers|leaf_litter|glow_lichen|sculk_vein|resin_clump)$/.test(n)) return R([box(0, 0, 0, 16, 1, 16)]);
  // ---- 燈籠、火把、蠟燭
  if (/lantern$/.test(n) && n !== 'sea_lantern' && n !== 'jack_o_lantern') {
    if (st.hanging) return R([box(5, 1, 5, 11, 8, 11), box(6, 8, 6, 10, 10, 10), box(7, 10, 7, 9, 16, 9)]);
    return R([box(5, 0, 5, 11, 7, 11), box(6, 7, 6, 10, 9, 10)]);
  }
  if ((/torch$/.test(n) || /^colored_torch/.test(n)) && !/^torchflower/.test(n)) {
    const tf = st.torch_facing_direction;
    const at = { west: 1, east: 0, north: 3, south: 2 }[tf];
    if (at === undefined) return R([box(7, 0, 7, 9, 10, 9)]);
    return R([rotBox(box(12, 3, 7, 14, 13, 9), at)]);
  }
  if (/candle_cake$/.test(n) || n === 'cake') return R([box(1, 0, 1, 15, 8, 15)]);
  if (/candle$/.test(n)) return R([(st.candles | 0) > 0 ? box(5, 0, 5, 11, 6, 11) : box(7, 0, 7, 9, 6, 9)]);
  // ---- 細柱
  if (n === 'iron_chain' || n === 'chain' || /_chain$/.test(n)) {
    const a = st.pillar_axis || 'y';
    return R([a === 'x' ? box(0, 7, 7, 16, 9, 9) : a === 'z' ? box(7, 7, 0, 9, 9, 16) : box(7, 0, 7, 9, 16, 9)]);
  }
  if (/lightning_rod$/.test(n) || n === 'end_rod') {
    const fd = st.facing_direction | 0;
    const ax = fd <= 1 ? 'y' : fd <= 3 ? 'z' : 'x';
    return R([ax === 'x' ? box(0, 7, 7, 16, 9, 9) : ax === 'z' ? box(7, 7, 0, 9, 9, 16) : box(7, 0, 7, 9, 16, 9)]);
  }
  if (/^bamboo$/.test(n)) return R([box(6, 0, 6, 10, 16, 10)]);
  if (n === 'pointed_dripstone') return R([box(6, 0, 6, 10, 16, 10)]);
  // ---- 床與家具
  if (n === 'bed' || /_bed$/.test(n)) return R([box(0, 0, 0, 16, 9, 16)]);
  if (/^(chest|trapped_chest|ender_chest|copper_chest|\w+_copper_chest)$/.test(n)) return R([box(1, 0, 1, 15, 14, 15)]);
  if (/campfire$/.test(n)) return R([box(0, 0, 0, 16, 7, 16)]);
  if (n === 'flower_pot' || /^flower_pot/.test(n)) return R([box(5, 0, 5, 11, 6, 11)]);
  if (/(skull|head)$/.test(n)) return R([box(4, 0, 4, 12, 8, 12)]);
  if (n === 'enchanting_table') return R([box(0, 0, 0, 16, 12, 16)]);
  if (n === 'end_portal_frame') return R([box(0, 0, 0, 16, 13, 16)]);
  if (n === 'stonecutter_block' || n === 'stonecutter') return R([box(0, 0, 0, 16, 9, 16)]);
  if (n === 'lectern') return R([box(4, 0, 4, 12, 13, 12), box(0, 0, 0, 16, 2, 16), box(0, 12, 0, 16, 15, 16)]);
  if (n === 'brewing_stand') return R([box(7, 0, 7, 9, 14, 9), box(1, 0, 1, 15, 2, 15)]);
  if (n === 'bell') return R([box(4, 4, 4, 12, 13, 12), box(7, 13, 7, 9, 16, 9)]);
  if (/anvil$/.test(n)) return R([box(2, 0, 2, 14, 4, 14), box(4, 4, 3, 12, 10, 13), box(0, 10, 3, 16, 16, 13)]);
  if (n === 'hopper') return R([box(0, 10, 0, 16, 16, 16), box(4, 4, 4, 12, 10, 12), box(6, 0, 6, 10, 4, 10)]);
  if (n === 'decorated_pot') return R([box(1, 0, 1, 15, 16, 15)]);
  if (n === 'cactus') return R([box(1, 0, 1, 15, 16, 15)]);
  if (n === 'conduit') return R([box(5, 5, 5, 11, 11, 11)]);
  if (n === 'sea_pickle' || n === 'turtle_egg') return R([box(5, 0, 5, 11, 6, 11)]);
  if (n === 'azalea' || n === 'flowering_azalea') return R([box(0, 6, 0, 16, 16, 16), box(6, 0, 6, 10, 6, 10)]);
  if (n === 'scaffolding') return R([box(0, 14, 0, 16, 16, 16), box(0, 0, 0, 2, 14, 2), box(14, 0, 0, 16, 14, 2), box(0, 0, 14, 2, 14, 16), box(14, 0, 14, 16, 14, 16)]);
  if (n === 'grindstone') return R([box(4, 2, 2, 12, 14, 14)]);
  if (n === 'heavy_core') return R([box(4, 0, 4, 12, 8, 12)]);
  // ---- 牆上的小物件
  if (n === 'ladder') { const f = FD[st.facing_direction] ?? 2; return R([plate(OPP[f], 1)]); }
  if (/wall_sign$/.test(n)) { const f = FD[st.facing_direction] ?? 2; return R([plate(OPP[f], 2, 4, 12)]); }
  if (/hanging_sign$/.test(n)) return R([box(1, 0, 7, 15, 10, 9)]);
  if (/(standing_sign|^\w+_sign|^sign)$/.test(n)) return R([box(7, 0, 7, 9, 9, 9), box(0, 9, 7, 16, 16, 9)]);
  if (n === 'wall_banner') { const f = FD[st.facing_direction] ?? 2; return R([plate(OPP[f], 1, 0, 16, 1)]); }
  if (n === 'standing_banner') return R([box(7, 0, 7, 9, 16, 9), box(1, 4, 6, 15, 16, 7)]);
  if (/(^|_)button$/.test(n)) {
    const fd = st.facing_direction | 0;
    if (fd === 0) return R([box(5, 14, 6, 11, 16, 10)]);
    if (fd === 1) return R([box(5, 0, 6, 11, 2, 10)]);
    return R([plate(OPP[FD[fd]], 2, 6, 10, 5)]);
  }
  if (n === 'lever') {
    const d = st.lever_direction || 'up_north_south';
    if (d.startsWith('up')) return R([box(5, 0, 4, 11, 3, 12), box(7, 3, 7, 9, 10, 9)]);
    if (d.startsWith('down')) return R([box(5, 13, 4, 11, 16, 12), box(7, 6, 7, 9, 13, 9)]);
    const f = CARD[d] ?? 3; // lever 朝向 → 貼在反側
    return R([plate(OPP[f], 3, 4, 12, 5)]);
  }
  if (n === 'tripwire_hook') { const f = [2, 1, 3, 0][st.direction & 3]; return R([plate(OPP[f], 2, 2, 12, 6)]); }
  if (n === 'vine') {
    const bits = st.vine_direction_bits | 0;
    const b = [];
    // 1=南 2=西 4=北 8=東
    if (bits & 1) b.push(plate(2, 1)); if (bits & 2) b.push(plate(1, 1));
    if (bits & 4) b.push(plate(3, 1)); if (bits & 8) b.push(plate(0, 1));
    if (!b.length) b.push(box(0, 15, 0, 16, 16, 16));
    return R(b);
  }
  if (/(item_frame|glow_frame|^frame)$/.test(n)) { const f = FD[st.facing_direction]; return f === undefined ? R([box(2, 0, 2, 14, 1, 14)]) : R([plate(OPP[f], 1, 2, 14, 2)]); }
  // ---- 植物
  if (FLOWERS.test(n)) return { kind: K_CROSS, layer, crossH: 11 };
  if (PLANTS_FULL.test(n)) return { kind: K_CROSS, layer, crossH: 16 };
  if (PLANTS.test(n)) return { kind: K_CROSS, layer, crossH: /^(short_grass|tallgrass|fern)$/.test(n) ? 13 : 12 };
  if (n === 'fire' || n === 'soul_fire') return { kind: K_CROSS, layer, crossH: 16 };
  // ---- 其餘：完整方塊
  return { kind: K_CUBE, layer };
}

/** 依連接狀態產生動態外型（缺 state 的舊柵欄/玻璃板/牆）。c = [e,w,s,n]（0/1） */
export function dynBoxes(dyn, c) {
  if (dyn === 'fence') return fenceBoxes(c);
  if (dyn === 'pane') return paneBoxes(c);
  return wallBoxes(c.map((v) => (v ? 1 : 0)), !(c[0] && c[1] && !c[2] && !c[3]) && !(c[2] && c[3] && !c[0] && !c[1]));
}
