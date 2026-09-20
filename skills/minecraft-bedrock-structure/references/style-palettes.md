# 風格調色盤

每個風格給一組「主材（3 種漸層）／次材／點綴／屋頂／窗／門／燈／地面／景觀」。這不是硬性規定，而是讓你起手時就有 12–25 種方塊可用，並在任務書裡寫成本次的調色盤。挑好後用 `block_catalog.py states` 核對每個 ID 與 state 都存在。

方塊 ID 省略 `minecraft:`；`<木>` 表示可替換木種。所有 ID 都經 v1.26.50 官方表核對；命名例外見 `block-catalog.md` 第 1 節。

目錄：日式和風｜中式廟宇／園林｜歐洲中世紀（木桁架）｜歐洲中世紀（石堡）｜哥德教堂｜地中海｜北歐木屋｜沙漠／中東｜熱帶／海島｜現代簡約｜工業／蒸汽龐克｜科幻基地｜鐵道設施｜漸層配方表

---

## 日式和風（町屋、神社、茶室）
辨識特徵：深色木構架露在外、白牆、大屋簷、低矮、格柵、庭園有石燈籠與枯山水。
- 主材（牆）：`white_concrete` 5 / `smooth_quartz` 3 / `white_terracotta` 2（白灰泥）；木構架 `dark_oak_log`、`dark_oak_planks`、`stripped_dark_oak_log`
- 次材：`spruce_planks`、`stripped_spruce_log`（地板、內牆）
- 點綴：`dark_oak_fence`、`dark_oak_trapdoor`（格柵窗）、`bamboo_block`、`bamboo_mosaic`
- 屋頂：`deepslate_tile_stairs` + `deepslate_tile_slab`（黑瓦）或 `dark_oak_stairs` + `dark_oak_slab`（木瓦）；屋脊 `deepslate_tile_slab top`，簷口倒置 `dark_oak_stairs`
- 窗：`dark_oak_trapdoor`（開啟）＋ `white_stained_glass_pane` 或 `glass_pane` 後退一格；紙門用 `birch_trapdoor` 或 `white_concrete` 與 `dark_oak_fence` 交錯
- 門：`dark_oak_door`、`spruce_door`
- 燈：`lantern`（吊）、石燈籠 = `stone_brick_wall` + `andesite` + `glowstone` + `stone_brick_slab`
- 地面：`grass_path`、`gravel`、`andesite`、`stone_brick_slab` 踏石、`sand` + `smooth_sandstone_slab`（枯山水）
- 景觀：`cherry_leaves`、`cherry_log`、`bamboo`、`azalea`、`moss_block`、`moss_carpet`、`water` + `waterlily`、`pink_petals`

## 中式廟宇／園林
辨識特徵：紅柱、金脊、重簷翹角、斗拱、白石台基、灰瓦、石獅與香爐。
- 主材：台基 `smooth_quartz` / `polished_andesite` / `stone_bricks`；牆 `red_terracotta` 5 / `red_concrete` 3 / `white_terracotta` 2
- 柱：`red_concrete`（柱身）+ `smooth_quartz`（柱礎）+ `gold_block`（柱頭）
- 點綴：`gold_block`、`chiseled_stone_bricks`、`polished_blackstone_bricks`、`dark_oak_fence`、`red_stained_glass_pane`
- 屋頂：`deepslate_tile_stairs` + `deepslate_tile_slab`；脊 `gold_block` + `polished_blackstone_brick_slab`；翹角用 `deepslate_tile_slab` 逐格上升＋ `lightning_rod` 尖
- 窗：`dark_oak_fence`（欞窗）、`red_stained_glass_pane`
- 門：`dark_oak_door`，門洞用 `red_concrete` 框
- 燈：`lantern`、紅燈籠 = `shroomlight` 四周 `red_stained_glass_pane` + `dark_oak_slab` + `iron_chain`
- 地面：`smooth_stone`、`polished_andesite`、`stone_bricks` 拼格、`red_carpet` 走道
- 景觀：`cherry_leaves`、`spruce_leaves`、`water` + `waterlily` + `pink_petals`、`cut_copper` 香爐、`stone_brick_wall` 欄杆

## 歐洲中世紀（木桁架民宅、村莊）
辨識特徵：一樓石砌、二樓白牆黑木桁架、出挑上層、陡屋頂、小窗、煙囪。
- 主材（石基）：`cobblestone` 5 / `stone_bricks` 3 / `mossy_cobblestone` 1 / `andesite` 1；（上層牆）`white_terracotta` 4 / `birch_planks` 3 / `mud_bricks` 2 / `packed_mud` 1
- 桁架：`dark_oak_log`（`pillar_axis` 依向）、`dark_oak_planks`、`spruce_log`
- 點綴：`dark_oak_stairs`（出挑支撐）、`spruce_trapdoor`、`barrel`、`hay_block`
- 屋頂：`dark_oak_stairs` + `dark_oak_slab` 或 `spruce_stairs`；茅草 `hay_block`；煙囪 `cobblestone_wall` + `campfire`
- 窗：`glass_pane` 2×2、`spruce_trapdoor` 百葉、窗台 `spruce_stairs upside_down`
- 門：`spruce_door`、`dark_oak_door`
- 燈：`lantern` 掛 `dark_oak_fence` + `iron_chain`、室內 `torch`
- 地面：`grass_path` 5 / `gravel` 3 / `coarse_dirt` 2 小徑；`cobblestone` + `stone_brick_slab` 廣場
- 景觀：`oak_leaves`、`oak_log` 樹、`oak_fence` 圍籬、`farmland` + `wheat`、`composter`、`water` 井

## 歐洲中世紀（石堡、城牆）
辨識特徵：厚重石牆、雉堞、圓塔、箭孔、吊橋、旗幟。
- 主材：`stone_bricks` 5 / `cobblestone` 2 / `cracked_stone_bricks` 1 / `mossy_stone_bricks` 1 / `andesite` 1；深色版 `deepslate_bricks` / `cobbled_deepslate` / `polished_deepslate` / `deepslate_tiles`
- 次材：`chiseled_stone_bricks`（腰線）、`polished_andesite`（窗框）、`stone_brick_wall`（雉堞）
- 點綴：`dark_oak_planks`（吊橋、地板）、`iron_bars`（窗）、`standing_banner`、`iron_chain`
- 屋頂：塔頂 `deepslate_tile_stairs` 圓錐或 `dark_oak_stairs`；平頂用 `stone_brick_slab` + `stone_brick_wall`
- 窗：箭孔 = 1 格 `air` 或 `iron_bars`；大廳 `glass_pane` 高窗
- 門：`dark_oak_door`、`iron_door`；城門 `dark_oak_planks` + `iron_bars`
- 燈：`torch`、`lantern`、`campfire`（火盆 = `cauldron` + `campfire` 上方）
- 地面：`stone_bricks`、`cobblestone`、`gravel`
- 景觀：護城河 `water`、`oak_leaves`、`spruce_leaves`、`dark_oak_fence` 練兵場

## 哥德教堂
辨識特徵：高聳、尖拱、飛扶壁、彩繪玻璃、尖塔、垂直線條。
- 主材：`stone_bricks` 4 / `polished_andesite` 3 / `andesite` 2 / `smooth_stone` 1；淺色版 `diorite` / `polished_diorite` / `calcite` / `quartz_bricks`
- 次材：`chiseled_stone_bricks`、`stone_brick_wall`（飛扶壁、尖塔）、`andesite_wall`
- 點綴：`gold_block`、`polished_blackstone_bricks`、`iron_bars`、`end_rod`（尖頂）
- 屋頂：`deepslate_tile_stairs` 陡坡、`polished_blackstone_brick_slab`
- 窗：`<色>_stained_glass_pane` 拼花（`blue`、`red`、`yellow`、`purple`），拱頂用倒置 `stone_brick_stairs`
- 門：`dark_oak_door` 雙開，門洞多層退縮 `stone_brick_stairs`
- 燈：`lantern` + `iron_chain` 吊燈、`white_candle` 祭壇
- 地面：`polished_andesite` + `polished_blackstone` 棋盤、`red_carpet`
- 景觀：`spruce_leaves` 修剪樹、`stone_brick_wall` 圍牆

## 地中海（希臘、義大利海岸）
辨識特徵：白牆、藍門窗、平頂或緩坡紅瓦、拱廊、階梯巷弄。
- 主材：`white_concrete` 4 / `smooth_quartz` 3 / `white_terracotta` 2 / `calcite` 1
- 次材：`sandstone`、`smooth_sandstone`、`cut_sandstone`（台階、牆基）
- 點綴：`blue_concrete`、`light_blue_concrete`、`cyan_terracotta`（門窗框）、陶盆用 `flower_pot`
- 屋頂：`brick_stairs` + `brick_slab`（紅瓦）或 `orange_terracotta` 平頂 + `sandstone_wall` 女兒牆
- 窗：`blue_stained_glass_pane`、`light_blue_stained_glass_pane`、`birch_trapdoor` 白百葉
- 門：`birch_door`（漆白）、`acacia_door`
- 燈：`lantern`、`sea_lantern`（藏於柱內）
- 地面：`smooth_sandstone` + `cut_sandstone_slab` 階梯、`stone_brick_slab`
- 景觀：`oak_leaves`（橄欖）、`azalea_leaves_flowered`、`cactus`、`water` 泳池 + `prismarine_bricks` 底

## 北歐木屋
辨識特徵：整棟原木、陡屋頂、深色、雪、小窗、石基。
- 主材：`spruce_log`（橫放 `pillar_axis=x/z`）5 / `stripped_spruce_log` 3 / `spruce_planks` 2
- 次材：`cobblestone`、`stone_bricks`、`cobbled_deepslate`（石基）
- 點綴：`dark_oak_planks`、`spruce_trapdoor`、`spruce_fence`
- 屋頂：`spruce_stairs` + `spruce_slab`；草皮頂 `moss_block` + `grass_block`；積雪 `snow_layer height=1–3`
- 窗：`glass_pane` 小窗、`spruce_trapdoor` 百葉
- 門：`spruce_door`
- 燈：`lantern`、`campfire` 壁爐、`shroomlight` 室內暖光
- 地面：`grass_path`、`gravel`、`spruce_planks` 平台
- 景觀：`spruce_leaves` 針葉樹（高瘦）、`snow`、`packed_ice`、`spruce_fence` 圍籬、`barrel`

## 沙漠／中東
辨識特徵：厚土牆、平頂、圓拱與穹頂、小窗、庭院噴泉、幾何紋樣。
- 主材：`sandstone` 4 / `smooth_sandstone` 3 / `cut_sandstone` 2 / `mud_bricks` 1；暖色版 `red_sandstone` 系、`orange_terracotta`、`hardened_clay`
- 次材：`chiseled_sandstone`、`packed_mud`、`hardened_clay`
- 點綴：`gold_block`、`cyan_terracotta`、`blue_glazed_terracotta`、`cyan_glazed_terracotta`（幾何紋）、`lapis_block`
- 屋頂：平頂 `sandstone_slab` + `sandstone_wall` 女兒牆；穹頂 `smooth_sandstone_stairs` 圓弧或 `cyan_terracotta`
- 窗：`sandstone_wall` 格柵、`iron_bars`、`orange_stained_glass_pane`
- 門：`acacia_door`、`jungle_door`；拱門 `smooth_sandstone_stairs` 倒置
- 燈：`lantern`、`torch`、`end_rod`
- 地面：`sand`、`smooth_sandstone`、`cut_sandstone_slab`、`<色>_glazed_terracotta` 拼花
- 景觀：`cactus`、`deadbush`、`jungle_leaves`（棕櫚冠）+ `jungle_log`、`water` 水池 + `prismarine_bricks`、`hay_block`

## 熱帶／海島
辨識特徵：高腳屋、茅草頂、竹木、開放式、鮮豔色。
- 主材：`jungle_planks` 4 / `bamboo_planks` 3 / `stripped_jungle_log` 2 / `acacia_planks` 1
- 次材：`bamboo_block`、`bamboo_mosaic`、`jungle_fence`（高腳、欄杆）
- 點綴：`cyan_terracotta`、`lime_concrete`、`orange_wool`
- 屋頂：`hay_block` + `jungle_slab`（茅草）或 `jungle_stairs` + `jungle_slab`
- 窗：開放無玻璃、`bamboo_trapdoor`、`jungle_trapdoor`
- 門：`jungle_door`、`bamboo_door`
- 燈：`lantern`、`torch`、`campfire`
- 地面：`sand`、`grass_block`、`jungle_planks` 棧道
- 景觀：`jungle_leaves` + `jungle_log` 棕櫚、`bamboo`、`melon_block`、`water` + `sand` + `tube_coral_block`、`sea_pickle`

## 現代簡約
辨識特徵：平頂、大面玻璃、懸挑、白灰黑三色、水平線條、極少裝飾。
- 主材：`white_concrete` 5 / `smooth_quartz` 2 / `light_gray_concrete` 2 / `quartz_block` 1
- 次材：`gray_concrete`、`black_concrete`、`polished_deepslate`、`smooth_stone`、`polished_andesite`
- 點綴：`stripped_oak_log`、`stripped_birch_log`（木格柵）、`iron_block`、`polished_blackstone`
- 屋頂：平頂 `smooth_quartz_slab` 或 `polished_deepslate_slab`；懸挑用 `white_concrete` 外伸 2–3 格
- 窗：`glass`（整面，但用 `smooth_stone_slab` 或 `quartz_slab` 分層）、`tinted_glass`、`light_gray_stained_glass`
- 門：`iron_door`、`birch_door`；玻璃門 `glass_pane` + `iron_trapdoor`
- 燈：`sea_lantern` 嵌入天花板、`end_rod` 燈管、`light_block_15` 隱藏
- 地面：`polished_andesite`、`smooth_stone`、`quartz_block`、`birch_planks`
- 景觀：`grass_block` 平整、`azalea_leaves` 修剪方塊、`water` 無邊際池 + `dark_prismarine` 底、`stone_brick_slab` 步道

## 工業／蒸汽龐克
辨識特徵：磚與鐵、銅管、齒輪、煙囪、外露結構、鉚釘。
- 主材：`brick_block` 4 / `mud_bricks` 2 / `polished_blackstone_bricks` 2 / `iron_block` 1 / `cracked_stone_bricks` 1
- 次材：`waxed_copper`、`waxed_exposed_copper`、`waxed_weathered_copper`（管線與鍋爐）、`cut_copper`、`iron_trapdoor`
- 點綴：`iron_bars`、`iron_chain`、`lightning_rod`（管）、`copper_grate`、`anvil`、`grindstone`、`cauldron`、`lever`、`stonecutter_block`
- 屋頂：`iron_trapdoor` 鐵皮、`waxed_oxidized_cut_copper_stairs`、`polished_blackstone_brick_slab`
- 窗：`iron_bars`、`glass_pane`、`gray_stained_glass_pane`
- 門：`iron_door`、`copper_door`
- 燈：`redstone_lamp`（造型）、`copper_bulb lit=True`、`lantern`、`campfire` 煙囪
- 地面：`polished_andesite`、`smooth_stone`、`iron_block` 格柵 `iron_trapdoor`
- 景觀：`coarse_dirt`、`gravel`、`barrel`、`hopper`、`rail`

## 科幻基地／太空
辨識特徵：白色曲面、發光線條、氣閘、六角/圓窗、對比色警示線。
- 主材：`white_concrete` 4 / `light_gray_concrete` 3 / `iron_block` 2 / `smooth_quartz` 1；深色版 `black_concrete` / `polished_deepslate` / `gray_concrete`
- 次材：`quartz_pillar`、`polished_andesite`、`cyan_concrete`、`light_blue_concrete`
- 點綴：`sea_lantern`、`end_rod`、`light_blue_stained_glass`、`cyan_stained_glass`、`yellow_concrete`（警示條）、`black_concrete`（接縫）、`iron_trapdoor`、`observer`（面板）、`lightning_rod`（天線）
- 屋頂／外殼：`smooth_quartz_stairs` 曲面、`light_gray_concrete` 分段
- 窗：`light_blue_stained_glass_pane`、`tinted_glass`、`glass` 圓窗（用倒置 `quartz_stairs` 收邊）
- 門：`iron_door`、氣閘 = 兩道 `iron_door` + `iron_trapdoor`
- 燈：`sea_lantern`、`end_rod`、`light_block_15`、`verdant_froglight`
- 地面：`polished_andesite`、`iron_block`、`light_gray_concrete`、`cyan_concrete` 導引線
- 景觀：`gray_concrete_powder`（月面）、`basalt`、`tuff`、`end_stone`

## 鐵道設施（本專案常用）
辨識特徵：月台、站棚、軌道床、號誌、隧道拱。
- 主材：`stone_bricks` 4 / `polished_andesite` 3 / `smooth_stone` 2 / `polished_deepslate` 1
- 次材：`spruce_planks`、`stripped_spruce_log`、`spruce_slab`（站棚）；現代站 `smooth_quartz`、`quartz_pillar`
- 點綴：`yellow_terracotta`（月台警示線）、`iron_trapdoor`、`iron_bars`、`waxed_exposed_cut_copper`、`chiseled_stone_bricks`
- 屋頂：`spruce_stairs` + `spruce_slab`、`mud_brick_slab`、`smooth_quartz_slab`、`waxed_oxidized_cut_copper_slab`
- 窗：`glass_pane`、`spruce_trapdoor`
- 燈：`sea_lantern`（嵌月台邊）、`lantern` + `iron_chain`、`dark_oak_fence` 燈柱 + `spruce_slab`
- 軌道床：`gravel`、`andesite`、`redstone_block`（動力）、`rail` / `golden_rail`
- 景觀：`azalea_leaves`、`spruce_leaves`、`brick_block` 花台、`moss_block`

---

## 漸層配方表

漸層的用法：把一面牆的每個方塊用加權隨機（固定 seed）從配方中抽，或按高度分層（下深上淺）。比例是「常見比例」不是規定。

| 用途 | 配方（比例） |
|---|---|
| 灰石牆 | `stone_bricks` 5 / `cobblestone` 2 / `cracked_stone_bricks` 1 / `mossy_stone_bricks` 1 / `andesite` 1 |
| 老化石牆（下濕上乾） | 下 3 格 `mossy_cobblestone` 3 / `cobblestone` 3 / `mossy_stone_bricks` 2；上方改 `stone_bricks` 5 / `cobblestone` 2 |
| 深灰石牆 | `deepslate_bricks` 4 / `cobbled_deepslate` 3 / `polished_deepslate` 2 / `cracked_deepslate_bricks` 1 |
| 白灰泥 | `white_concrete` 4 / `white_terracotta` 3 / `smooth_quartz` 2 / `calcite` 1 |
| 淺石 | `diorite` 3 / `polished_diorite` 3 / `calcite` 2 / `quartz_bricks` 1 |
| 砂岩 | `sandstone` 4 / `smooth_sandstone` 3 / `cut_sandstone` 2 / `chiseled_sandstone` 1 |
| 紅磚 | `brick_block` 6 / `mud_bricks` 2 / `red_terracotta` 1 / `cracked_nether_bricks` 1 |
| 暗木牆 | `spruce_planks` 4 / `dark_oak_planks` 3 / `stripped_spruce_log` 2 |
| 亮木牆 | `oak_planks` 4 / `birch_planks` 3 / `stripped_oak_log` 2 |
| 原木牆 | `spruce_log`（橫放）5 / `stripped_spruce_log` 2 |
| 銅綠 | `waxed_oxidized_copper` 4 / `waxed_weathered_copper` 3 / `waxed_exposed_copper` 1 |
| 地面小徑 | `grass_path` 5 / `gravel` 3 / `coarse_dirt` 2 / `andesite` 1 |
| 石板廣場 | `stone_bricks` 3 / `polished_andesite` 3 / `andesite` 2 / `smooth_stone` 2 |
| 草地 | `grass_block` 8 / `moss_block` 2，上方零星 `short_grass`、`fern`、`wildflowers` |
| 屋頂黑瓦 | `deepslate_tile_stairs` 7 / `polished_blackstone_brick_stairs` 2 / `cobbled_deepslate_stairs` 1 |
| 屋頂木瓦 | `dark_oak_stairs` 6 / `spruce_stairs` 3 / `mangrove_stairs` 1 |
| 現代白 | `white_concrete` 6 / `smooth_quartz` 3 / `light_gray_concrete` 1（只在陰影面） |
| 科幻深色 | `black_concrete` 4 / `polished_deepslate` 3 / `gray_concrete` 2 / `polished_blackstone` 1 |
