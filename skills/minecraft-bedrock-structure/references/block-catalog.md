# 基岩版方塊目錄（按用途分類）

依據 Mojang 官方 `mojang-blocks.json` v1.26.50 整理（1463 種方塊、157 種 state）。目的不是列完所有方塊，而是讓你在選材時**看得到整個可用範圍**，而不是每次都回到 `stone_bricks` / `oak_planks` / `glass`。所有 ID 省略 `minecraft:` 前綴；`StructureBuilder.block()` 會自動補上。

不確定某個方塊或 state 是否存在時，直接查表，不要猜：

```
python scripts/block_catalog.py --metadata <mojang-blocks.json> search <關鍵字...>   # AND 搜尋
python scripts/block_catalog.py --metadata <mojang-blocks.json> states <方塊>          # 列 state 與預設值
python scripts/block_catalog.py --metadata <mojang-blocks.json> families              # 哪些材質有 stairs/slab/wall…
python scripts/block_catalog.py --metadata <mojang-blocks.json> material <字根>        # 某材質的全部變體
```

目錄：
1. 基岩版特有命名（從 Java 帶來的錯誤名）
2. 結構主材（石、磚、木、混凝土/陶瓦、銅、其他）
3. 形狀變體（樓梯/半磚/牆/柵欄/活板門/門/按鈕/壓力板）
4. 開口與玻璃
5. 屋頂材
6. 燈光
7. 細節小方塊與家具用方塊
8. 植栽與景觀
9. 功能、紅石與軌道
10. 常用 state 對照表
11. 需要成對/多格放置的方塊

---

## 1. 基岩版特有命名（先看這段）

| 你可能想寫的 | 基岩版實際 ID | 備註 |
|---|---|---|
| `oak_trapdoor` / `oak_door` / `oak_button` / `oak_pressure_plate` / `oak_fence_gate` | `trapdoor` / `wooden_door` / `wooden_button` / `wooden_pressure_plate` / `fence_gate` | 橡木是舊版無前綴命名；其他木種正常（`spruce_trapdoor`…） |
| `oak_sign` | `standing_sign` / `wall_sign` / `oak_hanging_sign` | 深色橡木立牌是 `darkoak_standing_sign`（無底線） |
| `bricks` / `nether_bricks` / `red_nether_bricks` / `end_stone_bricks` | `brick_block` / `nether_brick` / `red_nether_brick` / `end_bricks` | 但 `stone_bricks`、`deepslate_bricks`、`mud_bricks`、`tuff_bricks`、`resin_bricks` 是複數 |
| `cobblestone_stairs` / `stone_stairs` / `stone_slab` | `stone_stairs`（＝鵝卵石樓梯）/ `normal_stone_stairs`（＝石頭樓梯）/ `normal_stone_slab` | 歷史包袱，最容易放錯 |
| `terracotta`（無色） | `hardened_clay` | 有色是 `white_terracotta` 等 16 色 |
| `chain` | `iron_chain` | 26.x 起改名；另有 `copper_chain` 系列 |
| `sugar_cane` / `dead_bush` / `grass` / `tall_grass`(矮) / `rooted_dirt` / `dirt_path` | `reeds` / `deadbush` / `short_grass` / `tall_grass`(雙格高) / `dirt_with_roots` / `grass_path` | |
| `note_block` / `skull` / `small_dripleaf` / `stonecutter` | `noteblock` / `skeleton_skull`、`player_head`… / `small_dripleaf_block` / `stonecutter_block` | |
| `glass_pane` 各色 | `white_stained_glass_pane`… | 另有 `hard_*_stained_glass_pane`（教育版硬化玻璃，一般不用） |
| `light` | `light_block_0` … `light_block_15` | 隱形光源，數字就是亮度，無 state |

## 2. 結構主材

每個「族」至少列出可做漸層的 3–4 種近色方塊。做牆面時，從同一族挑 3 種按 5:3:2 左右隨機混用，比單一方塊自然得多。

### 石材
- 灰石系：`stone`、`cobblestone`、`mossy_cobblestone`、`stone_bricks`、`mossy_stone_bricks`、`cracked_stone_bricks`、`chiseled_stone_bricks`、`smooth_stone`、`andesite`、`polished_andesite`
- 白/淺色：`diorite`、`polished_diorite`、`calcite`、`quartz_block`、`smooth_quartz`、`quartz_bricks`、`chiseled_quartz_block`、`quartz_pillar`、`white_concrete`、`bone_block`、`snow`、`packed_ice`
- 暖色：`granite`、`polished_granite`、`sandstone`、`cut_sandstone`、`chiseled_sandstone`、`smooth_sandstone`、`red_sandstone`（同四種變體）、`brick_block`、`mud_bricks`、`packed_mud`、`resin_block`、`resin_bricks`、`chiseled_resin_bricks`、`cinnabar`、`polished_cinnabar`、`cinnabar_bricks`
- 深色：`deepslate`、`cobbled_deepslate`、`polished_deepslate`、`deepslate_bricks`、`cracked_deepslate_bricks`、`deepslate_tiles`、`cracked_deepslate_tiles`、`chiseled_deepslate`、`blackstone`、`polished_blackstone`、`polished_blackstone_bricks`、`cracked_polished_blackstone_bricks`、`chiseled_polished_blackstone`、`gilded_blackstone`、`basalt`、`polished_basalt`、`smooth_basalt`、`black_concrete`、`obsidian`
- 灰褐：`tuff`、`polished_tuff`、`tuff_bricks`、`chiseled_tuff`、`mud`、`sulfur`、`polished_sulfur`、`sulfur_bricks`
- 地獄/暗紅：`nether_brick`、`red_nether_brick`、`cracked_nether_bricks`、`chiseled_nether_bricks`、`crimson_nylium`、`nether_wart_block`
- 末地/紫：`end_stone`、`end_bricks`、`purpur_block`、`purpur_pillar`
- 海洋：`prismarine`、`prismarine_bricks`、`dark_prismarine`、`sea_lantern`

### 木材（每種都有完整形狀變體，見第 3 節）
`oak`、`spruce`、`birch`、`jungle`、`acacia`、`dark_oak`、`mangrove`、`cherry`、`pale_oak`、`poplar`、`bamboo`、`crimson`、`warped`

- 每種有 `<木>_planks`、`<木>_log`、`stripped_<木>_log`、`<木>_wood`（六面樹皮）、`stripped_<木>_wood`；下界菌類是 `crimson_stem` / `warped_stem` / `stripped_*_stem`、`crimson_hyphae`；竹子是 `bamboo_block` / `stripped_bamboo_block` / `bamboo_planks` / `bamboo_mosaic`
- 顏色順序（淺→深）：`birch` < `bamboo` < `oak` < `poplar` < `jungle` < `acacia`(橘) < `cherry`(粉) < `spruce` < `mangrove`(紅) < `dark_oak` < `pale_oak`(灰白) ；`crimson` 紫紅、`warped` 青綠
- 木材漸層常用組合：`spruce_planks` + `stripped_spruce_log` + `dark_oak_planks`；`oak_planks` + `stripped_oak_log` + `birch_planks`

### 混凝土、陶瓦、羊毛（16 色，色名固定）
色名：`white light_gray gray black brown red orange yellow lime green cyan light_blue blue purple magenta pink`
- `<色>_concrete`（純色平面、現代/科幻）、`<色>_concrete_powder`（有顆粒，適合做沙/雪/髒污）
- `<色>_terracotta`（低飽和，適合屋頂、地中海、沙漠）、`<色>_glazed_terracotta`（有花紋，地磚點綴；淺灰例外是 `silver_glazed_terracotta`，沒有 `light_gray_glazed_terracotta`）、`hardened_clay`
- `<色>_wool`（有 stairs/slab 變體，做屋頂與軟裝）、`<色>_carpet`

### 銅（四個氧化階段 × 是否上蠟；建築上用 `waxed_` 版本才不會繼續氧化）
氧化階段前綴：無 → `exposed_` → `weathered_` → `oxidized_`；上蠟前綴 `waxed_`（可疊加，如 `waxed_oxidized_cut_copper`；注意原色上蠟塊是 `waxed_copper` 而不是 `waxed_copper_block`）
- 塊：`copper_block`、`cut_copper`、`chiseled_copper`、`copper_grate`（鏤空）
- 形狀：`cut_copper_stairs`、`cut_copper_slab`、`copper_door`、`copper_trapdoor`、`copper_bars`、`copper_chain`、`copper_lantern`、`copper_bulb`（可發光，`lit`）、`copper_torch`、`copper_chest`、`copper_golem_statue`
- 銅綠漸層：`waxed_copper` → `waxed_exposed_copper` → `waxed_weathered_copper` → `waxed_oxidized_copper`，屋頂用 `waxed_oxidized_cut_copper_stairs` + `waxed_oxidized_cut_copper_slab` 是最像真實銅屋頂的做法

### 金屬與其他
`iron_block`、`gold_block`、`netherite_block`、`lapis_block`、`emerald_block`、`diamond_block`、`amethyst_block`、`crying_obsidian`、`honeycomb_block`、`hay_block`、`dried_kelp_block`、`sponge`、`bookshelf`、`mushroom_stem`、`brown_mushroom_block`、`red_mushroom_block`

## 3. 形狀變體

`families` 指令可列出每個材質族有哪些形狀。常用整理：

| 形狀 | 有的材質 | 關鍵 state |
|---|---|---|
| `_stairs` | 全部木種；`stone`(=cobble)、`normal_stone`、`stone_brick`、`mossy_stone_brick`、`mossy_cobblestone`、`andesite`、`polished_andesite`、`diorite`、`polished_diorite`、`granite`、`polished_granite`、`sandstone`、`smooth_sandstone`、`red_sandstone`、`smooth_red_sandstone`、`brick`、`mud_brick`、`nether_brick`、`red_nether_brick`、`end_brick`、`quartz`、`smooth_quartz`、`purpur`、`prismarine`、`prismarine_bricks`、`dark_prismarine`、`deepslate_brick`、`deepslate_tile`、`polished_deepslate`、`cobbled_deepslate`、`blackstone`、`polished_blackstone`、`polished_blackstone_brick`、`tuff`、`polished_tuff`、`tuff_brick`、`resin_brick`、`cinnabar`、`polished_cinnabar`、`cinnabar_brick`、`sulfur`、`polished_sulfur`、`sulfur_brick`、`cut_copper`(含氧化/上蠟)、`bamboo_mosaic`、16 色 `_concrete`、16 色 `_wool` | `weirdo_direction`、`upside_down_bit`、`minecraft:corner` |
| `_slab` | 上述幾乎都有，另有 `cobblestone_slab`、`smooth_stone_slab`、`normal_stone_slab`、`cut_sandstone_slab`、`end_stone_brick_slab`、`petrified_oak_slab` | `minecraft:vertical_half` |
| `_wall` | `cobblestone`、`mossy_cobblestone`、`stone_brick`、`mossy_stone_brick`、`andesite`、`diorite`、`granite`、`sandstone`、`red_sandstone`、`brick`、`mud_brick`、`nether_brick`、`red_nether_brick`、`end_stone_brick`、`prismarine`、`deepslate_brick`、`deepslate_tile`、`polished_deepslate`、`cobbled_deepslate`、`blackstone`、`polished_blackstone`、`polished_blackstone_brick`、`tuff`、`polished_tuff`、`tuff_brick`、`resin_brick`、`cinnabar`…、`sulfur`… | `wall_connection_type_<方向>`、`wall_post_bit` |
| `_fence` / `_fence_gate` | 全部木種（橡木是 `oak_fence` / `fence_gate`）、`nether_brick_fence` | 柵欄無 state（自動連接）；門：`minecraft:cardinal_direction`、`open_bit`、`in_wall_bit` |
| `_trapdoor` | 全部木種（橡木是 `trapdoor`）、`iron_trapdoor`、`copper_trapdoor` 系列 | `direction`、`open_bit`、`upside_down_bit` |
| `_door` | 全部木種（橡木是 `wooden_door`）、`iron_door`、`copper_door` 系列 | 兩格：`upper_block_bit`；`minecraft:cardinal_direction`、`door_hinge_bit`、`open_bit` |
| `_button` | 全部木種（橡木 `wooden_button`）、`stone_button`、`polished_blackstone_button` | `facing_direction`、`button_pressed_bit` |
| `_pressure_plate` | 全部木種（橡木 `wooden_pressure_plate`）、`stone_pressure_plate`、`polished_blackstone_pressure_plate`、`light_weighted_pressure_plate`(金)、`heavy_weighted_pressure_plate`(鐵) | `redstone_signal` |
| `_shelf` | 全部木種（`oak_shelf`…，26.x 新增的可放物品層架） | `minecraft:cardinal_direction` |
| 標誌 | `<木>_standing_sign` / `<木>_wall_sign` / `<木>_hanging_sign` | 文字要另寫 block_position_data |

## 4. 開口與玻璃
- `glass`、`tinted_glass`（不透光、深色，適合現代/科幻）、`<色>_stained_glass`
- `glass_pane`、`<色>_stained_glass_pane`、`iron_bars`、`copper_bars`（含氧化）、`copper_grate`
- 木格柵用 `<木>_trapdoor`（開啟狀態貼牆）、`<木>_fence`、`<木>_shelf`；石格柵用 `<石>_wall`
- 玻璃板、鐵欄、銅欄、牆的連接 state 要自己填（見第 10 節），或用 `StructureBuilder.auto_connect()` 在存檔前自動補

## 5. 屋頂材
- 木瓦：`<木>_stairs` + `<木>_slab`（最通用；深色用 `dark_oak` / `spruce`，淺色用 `birch` / `oak`）
- 石板瓦：`deepslate_tile_stairs` + `deepslate_tile_slab`（黑灰）、`stone_brick_stairs`、`cobbled_deepslate_stairs`、`polished_blackstone_brick_stairs`
- 陶瓦/紅瓦：`brick_stairs` + `brick_slab`、`mud_brick_stairs`、`red_sandstone_stairs`、`<色>_concrete_stairs`、`<色>_wool_stairs`；陶瓦沒有樓梯，用 `<色>_terracotta` 整塊做平屋頂或搭配 `<色>_wool_stairs` 做坡頂
- 銅瓦：`waxed_oxidized_cut_copper_stairs` + slab（青綠）、`waxed_cut_copper_stairs`（新銅）
- 海晶/紫珀：`prismarine_bricks_stairs`、`dark_prismarine_stairs`、`purpur_stairs`
- 茅草：`hay_block`（`pillar_axis`）、`<木>_slab` 疊層
- 屋脊與收邊：對應材質的 `_slab`（上半 `top`）、倒置樓梯（`upside_down_bit=True`）、`<石>_wall` 當女兒牆、`iron_chain` / `lightning_rod` 當避雷針、`end_rod` 當尖頂

## 6. 燈光
| 方塊 | 亮度 | 用法 |
|---|---|---|
| `lantern` / `soul_lantern`（`hanging`） | 15 / 10 | 吊燈、燈柱；靈魂燈是藍色 |
| `copper_lantern` 系列 | 15 | 26.x 新增，四種氧化色 |
| `sea_lantern` | 15 | 現代/海洋；不要整排排，會像 LED 燈管 |
| `glowstone` | 15 | 藏在方塊後面或地板下 |
| `shroomlight` | 15 | 橘色暖光，適合紅色/木質空間 |
| `end_rod`（`facing_direction`） | 14 | 細柱狀，科幻燈管、尖頂 |
| `<色>_candle` / `candle`（`candles` 0–3 = 1–4 支，`lit`） | 3/支 | 桌上、祭壇、窗台 |
| `torch` / `soul_torch` / `copper_torch` / `redstone_torch`（`torch_facing_direction`） | 14/10 | 牆面火把用 `west/east/north/south`，地面用 `top` |
| `campfire` / `soul_campfire` | 15 | 壁爐、營地、煙囪頂 |
| `copper_bulb` 系列（`lit=True`） | 15 | 26.x，可通電開關 |
| `redstone_lamp` | 15 | 需通電；結構載入後不亮 |
| `ochre_froglight` / `verdant_froglight` / `pearlescent_froglight` | 15 | 柔和黃/綠/紫，`pillar_axis` |
| `light_block_1`…`light_block_15` | 1–15 | 隱形光源；放在空氣位置照亮室內而不露出燈具 |
| `magma`、`crying_obsidian`、`amethyst_cluster`、`glow_lichen`、`sea_pickle` | 3–7 | 微光點綴 |

## 7. 細節小方塊與家具用方塊
- 細柱/懸吊：`iron_chain`、`copper_chain`、`lightning_rod`、`end_rod`、`<木>_fence`、`<石>_wall`、`iron_bars`
- 桌椅床櫃：`<木>_stairs`（椅）、`<木>_trapdoor`（桌面、扶手、櫃門）、`<木>_pressure_plate`（桌面、盤子）、`<木>_slab`、`bed`（`direction` + `head_piece_bit` 兩格）、`chest` / `trapped_chest` / `ender_chest` / `copper_chest`、`barrel`、`<色>_shulker_box`
- 書與工作：`bookshelf`、`chiseled_bookshelf`（`books_stored`）、`<木>_shelf`、`lectern`、`enchanting_table`、`brewing_stand`、`cartography_table`、`smithing_table`、`fletching_table`、`loom`、`stonecutter_block`、`grindstone`（`attachment`）、`anvil` / `chipped_anvil` / `damaged_anvil`
- 廚房與火：`furnace`、`smoker`、`blast_furnace`、`cauldron`（`fill_level`）、`campfire`、`composter`、`cake`、`candle_cake`
- 裝飾：`flower_pot`（盆栽內容需 block_position_data）、`decorated_pot`、`frame` / `glow_frame`（物品框）、`standing_banner` / `wall_banner`（顏色圖案需 block_position_data）、`skeleton_skull` / `player_head` / `creeper_head`…、`bell`（`attachment`、`direction`）、`<色>_carpet`、`moss_carpet`、`pale_moss_carpet`、`snow_layer`（`height`）、`jukebox`、`noteblock`、`beacon`、`conduit`、`lodestone`、`respawn_anchor`、`dragon_egg`、`end_portal_frame`
- 蜂與農：`bee_nest`、`beehive`、`hay_block`、`farmland`、`wheat`、`carrots`、`potatoes`、`beetroot`、`melon_block`、`pumpkin`、`carved_pumpkin`、`lit_pumpkin`
- 梯與架：`ladder`、`scaffolding`、`<木>_trapdoor`（開啟疊放可當梯）

## 8. 植栽與景觀
- 地面：`grass_block`、`dirt`、`coarse_dirt`、`podzol`、`mycelium`、`dirt_with_roots`、`grass_path`、`mud`、`gravel`、`sand`、`red_sand`、`moss_block`、`pale_moss_block`、`clay`、`farmland`
- 樹葉（一律 `persistent_bit=True`，Builder 已預設）：`oak_leaves`、`spruce_leaves`、`birch_leaves`、`jungle_leaves`、`acacia_leaves`、`dark_oak_leaves`、`mangrove_leaves`、`cherry_leaves`（粉）、`pale_oak_leaves`、`azalea_leaves`、`azalea_leaves_flowered`、`yellow_poplar_leaves` / `orange_poplar_leaves` / `red_poplar_leaves`（秋色）
- 灌木：`azalea`、`flowering_azalea`、`bush`、`firefly_bush`、`deadbush`、`mangrove_propagule`、`<木>_sapling`（下界是 `crimson_fungus` / `warped_fungus`）
- 草花：`short_grass`、`fern`、`tall_grass` / `large_fern`（兩格）、`poppy`、`dandelion`、`blue_orchid`、`allium`、`azure_bluet`、`red_tulip` / `orange_tulip` / `white_tulip` / `pink_tulip`、`oxeye_daisy`、`cornflower`、`lily_of_the_valley`、`wither_rose`、`torchflower`、`cactus_flower`、`pink_petals`、`wildflowers`、`leaf_litter`（`growth` 控制數量）、`sunflower` / `lilac` / `rose_bush` / `peony` / `pitcher_plant`（兩格）、`short_dry_grass` / `tall_dry_grass`
- 攀藤與吊掛：`vine`、`glow_lichen`、`hanging_roots`、`pale_hanging_moss`、`weeping_vines`、`twisting_vines`、`cave_vines`、`spore_blossom`（天花板）、`big_dripleaf`、`small_dripleaf_block`、`pointed_dripstone`（`hanging`、`dripstone_thickness`）
- 水景：`water`（`liquid_depth=0` 為源頭）、`lava`、`waterlily`、`seagrass`、`kelp`、`sea_pickle`、`reeds`、`bamboo`、`cactus`、`ice`、`packed_ice`、`blue_ice`、`snow`、珊瑚 `<種>_coral_block` / `<種>_coral` / `<種>_coral_fan`（種：`tube brain bubble fire horn`，`dead_` 前綴為灰色）
- 洞穴/奇幻：`dripstone_block`、`calcite`、`amethyst_block`、`budding_amethyst`、`amethyst_cluster`、`sculk`、`sculk_vein`、`chorus_plant`、`chorus_flower`、`creaking_heart`、`mushroom_stem`、`brown_mushroom_block`（`huge_mushroom_bits`：14 全帽面、15 全莖面、0 全孔面）、`shroomlight`、`warped_wart_block`

## 9. 功能、紅石與軌道
- 軌道：`rail`、`golden_rail`（`rail_data_bit` 通電）、`detector_rail`、`activator_rail`；`rail_direction`：0 南北、1 東西、2 上坡向東、3 上坡向西、4 上坡向北、5 上坡向南、6–9 轉彎（僅 `rail`）
- 容器與傳輸：`chest`、`barrel`、`hopper`（`facing_direction`）、`dropper`、`dispenser`、`copper_chest`
- 紅石：`redstone_block`、`redstone_wire`、`unpowered_repeater`、`unpowered_comparator`、`redstone_torch`、`lever`、`observer`、`piston`、`sticky_piston`、`daylight_detector`、`target`、`tripwire_hook`、`sculk_sensor`、`calibrated_sculk_sensor`、`copper_bulb`
- 特殊：`structure_void`（載入時保留原方塊）、`barrier`（隱形牆）、`air`（清空）

## 10. 常用 state 對照表

| state | 值 | 含義 |
|---|---|---|
| `weirdo_direction`（樓梯） | 0 / 1 / 2 / 3 | 樓梯高側朝 +X(東) / −X(西) / +Z(南) / −Z(北)。屋頂左緣（−X 側）樓梯用 0 讓高側朝屋脊 |
| `upside_down_bit`（樓梯/活板門） | bool | True 為倒置；倒置樓梯做簷口、腰線、拱頂 |
| `minecraft:corner`（樓梯，26.x 新增） | `none` / `inner_left` / `inner_right` / `outer_left` / `outer_right` | 轉角形狀；用預設 `none`，遊戲載入後通常會依鄰接重算 |
| `minecraft:vertical_half`（半磚） | `bottom` / `top` | 上半磚做天花板收邊、屋脊 |
| `pillar_axis`（原木、柱、乾草、骨塊、玄武岩、石英柱、蛙明燈） | `y` / `x` / `z` | 橫梁沿 X 用 `x`、沿 Z 用 `z` |
| `persistent_bit`（樹葉） | bool | True 才不會自然消失；Builder 預設 True |
| `facing_direction`（按鈕、避雷針、末地燭、漏斗、發射器、活塞、梯子、壁掛標誌、旗幟、物品框） | 0 下 / 1 上 / 2 北(−Z) / 3 南(+Z) / 4 西(−X) / 5 東(+X) | 方塊「朝向」的方向；貼在西牆上的按鈕面朝東＝5 |
| `minecraft:cardinal_direction`（門、柵欄門、箱子、熔爐、講台、營火、鐵砧、層架、花瓣、單向紅石） | `south` / `west` / `north` / `east` | 方塊正面朝向 |
| `direction`（活板門、床、鐘、砂輪、織布機、雕紋書架、飾紋陶罐） | 0 / 1 / 2 / 3 | 活板門 0 東 1 西 2 南 3 北；床 0 南 1 西 2 北 3 東。同一面牆用同一值即可保持一致 |
| `open_bit`（門、活板門、柵欄門） | bool | 活板門 True＝直立貼牆，是做百葉窗、桌面側板的關鍵 |
| `door_hinge_bit` / `upper_block_bit`（門） | bool | 門要放兩格：下格 `upper_block_bit=False`，上格 True；鉸鏈左右 |
| `hanging`（燈籠、鐘乳石、吊掛標誌） | bool | True 為吊掛 |
| `attachment`（鐘、砂輪） | `standing` / `hanging` / `side` / `multiple` | |
| `candles` / `lit`（蠟燭） | 0–3 / bool | candles=n 表示 n+1 支 |
| `liquid_depth`（水、熔岩） | 0–15 | 0 為源頭，池子全用 0 |
| `wall_connection_type_east/west/north/south`（牆） | `none` / `short` / `tall` | 與鄰接方塊連接；`wall_post_bit=True` 為柱狀 |
| `minecraft:connection_east/west/north/south`（玻璃板、鐵欄、銅欄） | bool | 與鄰接連接 |
| `growth`（花瓣、落葉） | 0–7 | 數量密度 |
| `height`（雪層） | 0–7 | 厚度，做積雪或台階 |
| `huge_mushroom_bits`（蘑菇塊） | 0–15 | 14 全帽、15 全莖、0 全孔 |
| `torch_facing_direction`（火把） | `top` / `west` / `east` / `north` / `south` | 火把貼的方向（值是火把所在牆面的方向反向，貼西牆用 `east`） |
| `minecraft:block_face`（部分附著方塊） | `down` / `up` / `north` / `south` / `west` / `east` | 附著面 |
| `rail_direction` | 0–9 | 見第 9 節 |
| `books_stored`（雕紋書架） | 0–63 | 位元遮罩，63 為六格全滿 |
| `fill_level`（釜） | 0–6 | 6 為滿 |

**連接類 state 的注意事項**：柵欄沒有 state，遊戲會自動連接；但牆、玻璃板、鐵欄、銅欄的連接是 state，結構載入時不一定會重算。要嘛在放置時依鄰接自己填，要嘛在 `save()` 前呼叫 `StructureBuilder.auto_connect()` 讓它掃一次鄰接方塊補上；否則整面玻璃板會變成孤立的十字。

## 11. 需要成對/多格放置的方塊
- 門：下格 + 上格（`upper_block_bit`），兩格朝向與鉸鏈相同
- 床：腳 + 頭（`head_piece_bit`），`direction` 相同，頭在 direction 指向的那格
- 雙格植物：`tall_grass`、`large_fern`、`sunflower`、`lilac`、`rose_bush`、`peony`、`pitcher_plant`、`small_dripleaf_block`（`upper_block_bit`）
- 吊掛/附著：`lantern hanging=True` 上方要有方塊或鏈；`vine`、`glow_lichen`、`wall_sign`、`wall_banner`、按鈕、火把要有附著面
- 支承：地毯、壓力板、花、花盆、蠟燭、雪層、花瓣、落葉下方要有實心方塊；`waterlily` 下方要是水
- 水池：底與四邊必須有實心方塊，否則載入後水會流出
