#!/usr/bin/env python3
"""產生 site/data/block-colors.json：每個官方方塊的頂／側／底平均色與透明度。

資料來源：Mojang 官方 bedrock-samples（預設 tag v1.26.60.5）
  resource_pack/blocks.json                  方塊 → 各面材質 key
  resource_pack/textures/terrain_texture.json 材質 key → textures/blocks/*.png|tga
  metadata/vanilladata_modules/mojang-blocks.json 官方方塊名稱表

只抓材質圖計算 alpha 加權平均色，材質圖本身只放在快取資料夾（預設系統暫存），
不會放進倉庫或網站。灰階需要染色的材質（草、樹葉、藤蔓、水…）套用生態域染色；
對不到材質的方塊用名稱關鍵字推測。

用法：
  python3 -I site/tools/gen_block_colors.py \
      [--tag v1.26.60.5] [--cache /tmp/mc-textures] [--blocks work/mojang-blocks.json] \
      [--out site/data/block-colors.json]

需要 Pillow 與 numpy。輸出格式：
  { "minecraft:xxx": {"top":[r,g,b], "side":[r,g,b], "bottom":[r,g,b], "alpha":1.0}, ... }
四個欄位都一定存在（方便其他程式直接取用）；alpha 0 表示看不見的方塊（空氣、屏障、光源方塊…）。
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

RAW = "https://raw.githubusercontent.com/Mojang/bedrock-samples/{tag}/{path}"

# ---------------------------------------------------------------- 染色設定
GRASS = (0x79, 0xC0, 0x5A)      # 草方塊頂、草、蕨、甘蔗
FOLIAGE = (0x48, 0xB5, 0x18)    # 橡木／叢林／相思／深色橡木葉、藤蔓
SPRUCE = (0x61, 0x99, 0x61)
BIRCH = (0x80, 0xA7, 0x55)
MANGROVE = (0x8D, 0xB1, 0x27)
WATER = (0x3F, 0x76, 0xE4)
LILY = (0x20, 0x80, 0x30)
STEM = (0x8C, 0xA0, 0x3A)

# texture 檔名（basename）→ 染色色
TINT_BY_TEXTURE = {
    "grass_top": GRASS, "grass_side": GRASS, "tallgrass": GRASS, "fern": GRASS,
    "double_plant_grass_top": GRASS, "double_plant_grass_bottom": GRASS,
    "double_plant_fern_top": GRASS, "double_plant_fern_bottom": GRASS,
    "leaves_oak": FOLIAGE, "leaves_jungle": FOLIAGE, "leaves_acacia": FOLIAGE,
    "leaves_big_oak": FOLIAGE, "vine": FOLIAGE, "leaves_spruce": SPRUCE,
    "leaves_birch": BIRCH, "mangrove_leaves": MANGROVE,
    "water_still_grey": WATER, "water_flow_grey": WATER, "waterlily": LILY,
    "melon_stem_disconnected": STEM, "melon_stem_connected": STEM,
    "pumpkin_stem_disconnected": STEM, "pumpkin_stem_connected": STEM,
    "bush": GRASS,
}
# 染色時以這張材質的亮度當基準，讓「基準材質」染色後剛好等於染色色
TINT_REFERENCE = {GRASS: "grass_top", FOLIAGE: "leaves_oak", SPRUCE: "leaves_spruce",
                  BIRCH: "leaves_birch", MANGROVE: "mangrove_leaves", WATER: "water_still_grey",
                  LILY: "waterlily", STEM: "melon_stem_disconnected"}

# 官方名稱 → blocks.json key（名稱不同的）
ALIASES = {
    "grass_block": "grass", "sea_lantern": "seaLantern", "iron_chain": "chain",
    "piston_arm_collision": "pistonArmCollision",
    "sticky_piston_arm_collision": "stickyPistonArmCollision",
    "trip_wire": "tripWire", "hard_glass": "glass", "hard_glass_pane": "glass_pane",
    "underwater_torch": "torch", "underwater_tnt": "tnt",
    "colored_torch_blue": "torch", "colored_torch_green": "torch",
    "colored_torch_purple": "torch", "colored_torch_red": "torch",
}

INVISIBLE = re.compile(r"^(air|barrier|structure_void|light_block(_\d+)?|moving_block|movingBlock|"
                       r"piston_arm_collision|sticky_piston_arm_collision|unknown|"
                       r"bubble_column|end_gateway|portal|end_portal|invisible_bedrock|info_update2?|"
                       r"reserved6|deny|allow|border_block|camera|client_request_placeholder_block)$")

DYES = {
    "white": (233, 236, 236), "orange": (240, 118, 19), "magenta": (189, 68, 179),
    "light_blue": (58, 175, 217), "yellow": (248, 197, 39), "lime": (112, 185, 25),
    "pink": (237, 141, 172), "gray": (62, 68, 71), "light_gray": (142, 142, 134),
    "silver": (142, 142, 134), "cyan": (21, 137, 145), "purple": (121, 42, 172),
    "blue": (53, 57, 157), "brown": (114, 71, 40), "green": (84, 109, 27),
    "red": (161, 39, 34), "black": (20, 21, 25),
}
WOODS = {
    "pale_oak": (226, 214, 211), "dark_oak": (66, 43, 20), "oak": (162, 130, 78),
    "spruce": (114, 84, 48), "birch": (192, 175, 121), "jungle": (160, 115, 80),
    "acacia": (168, 90, 50), "mangrove": (117, 54, 48), "cherry": (226, 178, 172),
    "bamboo": (193, 173, 80), "crimson": (101, 48, 70), "warped": (43, 104, 99),
    "poplar": (186, 168, 128),
}
KEYWORDS = [
    ("deepslate", (80, 80, 82)), ("blackstone", (42, 36, 41)), ("basalt", (73, 72, 77)),
    ("andesite", (136, 136, 137)), ("diorite", (188, 188, 188)), ("granite", (149, 103, 85)),
    ("tuff", (108, 109, 102)), ("calcite", (223, 224, 220)), ("sandstone", (216, 203, 155)),
    ("red_sand", (190, 102, 33)), ("sand", (219, 207, 163)), ("gravel", (131, 127, 126)),
    ("prismarine", (99, 156, 151)), ("purpur", (169, 125, 169)), ("quartz", (235, 229, 222)),
    ("nether_brick", (44, 21, 26)), ("netherrack", (97, 38, 38)), ("end_stone", (219, 222, 158)),
    ("mud_brick", (137, 103, 79)), ("mud", (60, 57, 60)), ("brick", (150, 97, 83)),
    ("copper", (192, 107, 79)), ("iron", (220, 220, 220)), ("gold", (246, 208, 61)),
    ("diamond", (98, 237, 228)), ("emerald", (42, 203, 87)), ("lapis", (31, 67, 140)),
    ("redstone", (175, 24, 5)), ("obsidian", (15, 10, 24)), ("glass", (200, 220, 230)),
    ("ice", (145, 183, 253)), ("snow", (249, 254, 254)), ("terracotta", (152, 94, 67)),
    ("concrete", (180, 180, 180)), ("wool", (220, 220, 220)), ("cinnabar", (170, 50, 40)),
    ("sulfur", (214, 200, 70)), ("resin", (217, 99, 25)), ("moss", (89, 109, 45)),
    ("leaves", FOLIAGE), ("coral", (200, 80, 120)), ("stone", (125, 125, 125)),
    ("cobble", (122, 122, 122)), ("dirt", (134, 96, 67)), ("log", (110, 85, 50)),
    ("planks", (162, 130, 78)), ("wood", (110, 85, 50)),
]
COPPER_STAGES = [("oxidized", (82, 162, 132)), ("weathered", (108, 153, 110)),
                 ("exposed", (161, 125, 103))]

# 半透明方塊的 alpha（其他預設 1.0）
def alpha_for(name: str) -> float:
    if INVISIBLE.match(name):
        return 0.0
    if name in ("water", "flowing_water"):
        return 0.62
    if name == "tinted_glass":
        return 0.82
    if "stained_glass" in name:
        return 0.55
    if name in ("glass", "glass_pane", "hard_glass", "hard_glass_pane"):
        return 0.32
    if name in ("ice", "frosted_ice"):
        return 0.72
    if name in ("slime", "honey_block"):
        return 0.78
    if name.endswith("leaves") or "leaves" in name:
        return 0.92
    return 1.0


def strip_comments(text: str) -> str:
    return "\n".join(l for l in text.split("\n") if not l.strip().startswith("//"))


def fetch(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()
    except Exception:
        return None


def load_json(tag: str, path: str, cache: Path, local: Path | None = None):
    if local and local.exists():
        return json.loads(strip_comments(local.read_text(encoding="utf-8")))
    f = cache / path.replace("/", "_")
    if not f.exists():
        data = fetch(RAW.format(tag=tag, path=path))
        if data is None:
            sys.exit(f"無法下載 {path}")
        f.write_bytes(data)
    return json.loads(strip_comments(f.read_text(encoding="utf-8")))


def tex_file(cache: Path, path: str) -> Path | None:
    base = cache / "tex" / path.replace("/", "_")
    for ext in (".png", ".tga"):
        p = Path(str(base) + ext)
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def download_textures(tag: str, cache: Path, paths: set[str]) -> None:
    (cache / "tex").mkdir(parents=True, exist_ok=True)

    def one(path: str):
        if tex_file(cache, path):
            return
        for ext in (".png", ".tga"):
            data = fetch(RAW.format(tag=tag, path=f"resource_pack/{path}{ext}"))
            if data:
                (cache / "tex" / (path.replace("/", "_") + ext)).write_bytes(data)
                return

    todo = [p for p in paths if not tex_file(cache, p)]
    if todo:
        print(f"下載 {len(todo)} 張材質…", file=sys.stderr)
    with cf.ThreadPoolExecutor(24) as ex:
        list(ex.map(one, todo))


_stats_cache: dict[str, tuple] = {}

# 花：平均色會被綠色莖葉拉暗，改取「非綠色」像素（花瓣）的平均
FLOWER_TEXTURES = re.compile(r"^(flower_|double_plant_(sunflower_front|syringa_top|rose_top|paeonia_top)|"
                             r"torchflower|pitcher|open_eyeblossom|closed_eyeblossom|cactus_flower|wither_rose)")


def tex_stats(cache: Path, path: str, overlay: tuple | None = None):
    """回傳 (rgb 0..255 np.array, coverage 0..1, luminance 0..1) 或 None。"""
    key = path + repr(overlay)
    if key in _stats_cache:
        return _stats_cache[key]
    f = tex_file(cache, path)
    if f is None:
        _stats_cache[key] = None
        return None
    im = Image.open(f).convert("RGBA")
    a = np.asarray(im).astype(np.float64) / 255.0
    base = os.path.basename(path)
    if base == "grass_side" or overlay is not None:
        # 基岩版 grass_side.tga：alpha 是染色遮罩（不透明處要染色，透明處是泥土）
        tint = np.array(overlay or GRASS) / 255.0
        mask = a[..., 3] > 0.5
        rgb = a[..., :3].copy()
        ref = tex_stats(cache, "textures/blocks/grass_top")
        scale = 1.0 / max(ref[2], 1e-6) if ref else 1.0
        rgb[mask] = np.clip(rgb[mask] * tint * scale, 0, 1)
        res = (rgb.reshape(-1, 3).mean(0) * 255, 1.0, float(rgb.mean()))
        _stats_cache[key] = res
        return res
    al = a[..., 3]
    if FLOWER_TEXTURES.match(base):
        g = a[..., 1]
        petal = (al > 0.5) & ~((g > a[..., 0] * 1.05) & (g > a[..., 2] * 1.05))
        if petal.sum() >= 4:
            al = al * petal
    w = al.sum()
    if w < 1e-6:
        _stats_cache[key] = None
        return None
    rgb = (a[..., :3] * al[..., None]).sum((0, 1)) / w
    lum = float(rgb.mean())
    res = (rgb * 255, float(al.mean()), lum)
    _stats_cache[key] = res
    return res


def tokens(name: str) -> list[str]:
    t = name.split("_")
    out = list(t)
    for i in range(len(t) - 1):
        out.append(t[i] + "_" + t[i + 1])
    if name.startswith("wooden_") or name.startswith("oak_"):
        out += ["wood", "oak"]
    return out


def pick_variant(entries: list, block: str):
    """terrain_texture 的 list（舊 data value 變體）依方塊名稱挑最像的一張。"""
    if len(entries) == 1:
        return entries[0]
    toks = tokens(block)

    def path_of(e):
        return e if isinstance(e, str) else e.get("path", "")

    best, best_score = entries[0], -1
    for i, e in enumerate(entries):
        b = os.path.basename(path_of(e))
        score = sum(len(t) for t in toks if t in b)
        if b.endswith("_opaque") or b.endswith("_carried"):
            score -= 1
        if score > best_score:
            best, best_score = e, score
    return best


def resolve_texture(tt: dict, key: str, block: str):
    """材質 key → (path, overlay_color | None, tint_color | None)。"""
    ent = tt.get(key)
    if ent is None:
        return None
    tx = ent["textures"]
    if isinstance(tx, list):
        tx = pick_variant(tx, block)
    if isinstance(tx, str):
        return tx, None, None
    if isinstance(tx, dict):
        if "variations" in tx and "path" not in tx:
            tx = tx["variations"][0]
        ov = tx.get("overlay_color")
        tc = tx.get("tint_color")
        hx = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) if s else None
        return tx.get("path"), hx(ov), hx(tc)
    return None


def face_keys(textures) -> dict[str, str]:
    if isinstance(textures, str):
        return {"top": textures, "side": textures, "bottom": textures}
    if not isinstance(textures, dict):
        return {}
    side = textures.get("side")
    if side is None:
        dirs = [textures.get(d) for d in ("north", "south", "east", "west") if textures.get(d)]
        if dirs:
            side = max(dirs, key=lambda k: (dirs.count(k), -dirs.index(k)))
    top = textures.get("up", side)
    bottom = textures.get("down", side)
    if side == "sunflower_additional":  # 雙高植物：側面材質是向日葵花瓣，改用上半部
        side = top
    side = side or top or bottom
    return {"top": top or side, "side": side, "bottom": bottom or side}


def apply_tint(cache: Path, path: str, rgb, lum, explicit_tint):
    base = os.path.basename(path)
    tint = explicit_tint or TINT_BY_TEXTURE.get(base)
    if tint is None or base == "grass_side":
        return rgb
    sat = (rgb.max() - rgb.min()) / max(rgb.max(), 1e-6)
    if sat > 0.18:  # 已經是彩色材質，不再染色
        return rgb
    ref_name = TINT_REFERENCE.get(tint)
    ref = tex_stats(cache, f"textures/blocks/{ref_name}") if ref_name else None
    ref_lum = ref[2] if ref else 0.58
    k = lum / max(ref_lum, 1e-6)
    return np.clip(np.array(tint, dtype=float) * k, 0, 255)


def guess_color(name: str):
    n = name
    for stage, c in COPPER_STAGES:
        if stage in n and "copper" in n:
            return c
    for dye in sorted(DYES, key=len, reverse=True):
        if n.startswith(dye + "_") or f"_{dye}_" in n or n.endswith("_" + dye):
            return DYES[dye]
    for wood in sorted(WOODS, key=len, reverse=True):
        if n.startswith(wood + "_") or f"_{wood}_" in n:
            return WOODS[wood]
    for kw, c in KEYWORDS:
        if kw in n:
            return c
    if n.startswith("element_"):
        return (210, 210, 220)
    return (150, 150, 150)


# 結果覆寫：平均色不能代表外觀的方塊（多半是方塊實體或特殊模型）
OVERRIDES = {
    "bed": {"top": (178, 38, 38), "side": (150, 110, 70), "bottom": (120, 90, 60)},
    "chest": {"top": (162, 115, 48), "side": (150, 105, 45), "bottom": (140, 98, 42)},
    "trapped_chest": {"top": (162, 115, 48), "side": (150, 105, 45), "bottom": (140, 98, 42)},
    "ender_chest": {"top": (40, 55, 55), "side": (35, 48, 48), "bottom": (30, 40, 40)},
    "redstone_wire": {"top": (170, 20, 10)},
    "water": {"top": WATER, "side": WATER, "bottom": WATER},
    "flowing_water": {"top": WATER, "side": WATER, "bottom": WATER},
    "lava": {"top": (230, 110, 20)}, "flowing_lava": {"top": (230, 110, 20)},
    "standing_banner": {"top": (230, 230, 230)}, "wall_banner": {"top": (230, 230, 230)},
    "skull": {"top": (200, 200, 190)},
    "fire": {"top": (240, 150, 40)}, "soul_fire": {"top": (60, 200, 210)},
    "end_portal_frame": {"top": (60, 105, 90), "side": (220, 222, 160)},
    "colored_torch_blue": {"top": (60, 90, 230)}, "colored_torch_green": {"top": (60, 200, 70)},
    "colored_torch_purple": {"top": (170, 60, 220)}, "colored_torch_red": {"top": (230, 50, 40)},
    "glass": {"top": (205, 228, 232)}, "glass_pane": {"top": (205, 228, 232)},
    "hard_glass": {"top": (205, 228, 232)}, "hard_glass_pane": {"top": (205, 228, 232)},
    "unknown": {"top": (200, 0, 200)},
    # 光源：材質平均色多半是暗色外框，改成點亮後看起來的顏色
    "lantern": {"top": (214, 162, 88)}, "soul_lantern": {"top": (96, 176, 196)},
    "torch": {"top": (222, 176, 92)}, "underwater_torch": {"top": (222, 176, 92)},
    "soul_torch": {"top": (100, 190, 205)}, "redstone_torch": {"top": (205, 62, 34)},
    "copper_torch": {"top": (150, 215, 120)},
    "sunflower": {"top": (236, 192, 44), "side": (236, 192, 44), "bottom": (70, 128, 40)},
}

# 結構檔裡出現、但官方方塊表已改名的舊名稱
LEGACY = {"chain": "iron_chain"}


def main():
    here = Path(__file__).resolve().parent
    repo = here.parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1.26.60.5")
    ap.add_argument("--cache", type=Path, default=Path(tempfile.gettempdir()) / "mc-bedrock-textures")
    ap.add_argument("--blocks", type=Path, default=repo / "work" / "mojang-blocks.json")
    ap.add_argument("--out", type=Path, default=repo / "site" / "data" / "block-colors.json")
    args = ap.parse_args()
    cache: Path = args.cache
    cache.mkdir(parents=True, exist_ok=True)

    official = load_json(args.tag, "metadata/vanilladata_modules/mojang-blocks.json", cache, args.blocks)
    names = sorted({i["name"].split(":", 1)[1] for i in official["data_items"]})
    blocks = load_json(args.tag, "resource_pack/blocks.json", cache)
    tt = load_json(args.tag, "resource_pack/textures/terrain_texture.json", cache)["texture_data"]

    # 先列出所有要下載的材質
    paths: set[str] = set()

    def collect(e):
        if isinstance(e, str):
            paths.add(e)
        elif isinstance(e, dict):
            if "path" in e:
                paths.add(e["path"])
            for v in e.get("variations", []):
                collect(v)
        elif isinstance(e, list):
            for x in e:
                collect(x)

    for v in tt.values():
        collect(v["textures"])
    download_textures(args.tag, cache, paths)

    out: dict[str, dict] = {}
    stats = {"texture": 0, "guess": 0, "invisible": 0}
    for name in names:
        alpha = alpha_for(name)
        entry: dict[str, list] = {}
        if alpha == 0.0:
            c = [0, 0, 0]
            out["minecraft:" + name] = {"top": c, "side": c, "bottom": c, "alpha": 0.0}
            stats["invisible"] += 1
            continue
        key = ALIASES.get(name, name)
        if key not in blocks and name.startswith("hard_") and name[5:] in blocks:
            key = name[5:]
        faces = face_keys(blocks.get(key, {}).get("textures")) if key in blocks else {}
        for face, tkey in faces.items():
            r = resolve_texture(tt, tkey, name) if tkey else None
            if not r or not r[0]:
                continue
            path, ov, tint = r
            st = tex_stats(cache, path, ov)
            if st is None:
                continue
            rgb, cov, lum = st
            rgb = apply_tint(cache, path, np.array(rgb, dtype=float), lum, tint)
            entry[face] = [int(round(v)) for v in rgb]
        if entry:
            stats["texture"] += 1
        else:
            stats["guess"] += 1
            g = list(guess_color(name))
            entry = {"top": g, "side": g, "bottom": g}
        side = entry.get("side") or entry.get("top") or entry.get("bottom")
        entry.setdefault("side", side)
        entry.setdefault("top", side)
        entry.setdefault("bottom", side)
        ov = OVERRIDES.get(name)
        if ov:
            for f in ("top", "side", "bottom"):
                if f in ov:
                    entry[f] = list(ov[f])
            if "side" not in ov and "top" in ov:
                entry["side"] = list(ov["top"])
                if "bottom" not in ov:
                    entry["bottom"] = list(ov["top"])
        out["minecraft:" + name] = {"top": entry["top"], "side": entry["side"],
                                    "bottom": entry["bottom"], "alpha": alpha}

    for old, new in LEGACY.items():
        if "minecraft:" + new in out and "minecraft:" + old not in out:
            out["minecraft:" + old] = dict(out["minecraft:" + new])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["{"]
    items = list(out.items())
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        lines.append(f'  {json.dumps(k)}: {json.dumps(v, separators=(",", ":"))}{comma}')
    lines.append("}")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"寫入 {args.out}：{len(out)} 個方塊（材質 {stats['texture']}、推測 {stats['guess']}、"
          f"不可見 {stats['invisible']}）", file=sys.stderr)


if __name__ == "__main__":
    main()
