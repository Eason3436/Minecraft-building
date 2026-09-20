# 細節技法清單

一棟建築「看起來像 AI 蓋的」幾乎都是同一批原因：整片單一方塊、平屋頂大方盒、正方形樹、沒有簷、沒有室內、燈光均勻。這份清單把對策整理成可逐項勾選的技法。建模時分成「骨架 → 細節 → 室內 → 景觀與照明」四個 pass，細節 pass 就是逐條看這份清單，挑適合本次風格的做。

方塊 ID 省略 `minecraft:`；`<木>`、`<石>` 表示依調色盤代入。

目錄：0 比例規則｜1 立面｜2 屋頂｜3 開口｜4 柱梁與結構表現｜5 地面與台基｜6 景觀｜7 室內｜8 照明｜9 常見「AI 味」與修法｜10 自檢

---

## 0. 比例規則（先定這些數字，其餘細節才有依據）
- 門高 2、門口淨寬 1–2；室內淨高 3–4（層高含樓板 4–5）；大廳可 6–8。
- 窗：底邊離地 1–2，高 2，寬 1–2；同一立面窗距 2–3，節奏一致。
- 屋簷外挑 1 格（大屋頂 2 格）；屋頂坡度：民宅 1:1（每格升 1），日式/中式 緩坡 2:1 到翹角，哥德 陡坡。
- 每 5–7 格牆面要有一個「節奏元素」：柱、窗、凹槽、腰線或材質變化；超過 8 格空白牆面就是問題。
- 建築高度 : 寬度 ≈ 1:1.5 到 1:2 看起來最穩；塔可 3:1 以上。
- 人視角高度 1.6，重要細節放在 Y=1–5（地面到二樓），屋頂細節從遠處看。

## 1. 立面
1. **凹凸一格**：柱子突出 1、窗戶內縮 1、腰線突出半格（`<石>_slab` 或倒置 `<石>_stairs`）。平牆＋凹凸 = 陰影 = 立體感。
2. **材質漸層**：牆面每個方塊從同族 3–4 種方塊加權隨機（固定 seed，避免每次跑結果不同）。比例見 `style-palettes.md` 漸層配方表。下方濕、上方乾：底 2–3 層混 `mossy_*` / `cobblestone`，上方偏 `stone_bricks`。
3. **角隅收邊**：牆角用不同材質豎條（`<木>_log`、`stripped_<木>_log`、`<石>_wall`、`chiseled_stone_bricks`、`polished_andesite`），讓量體邊緣清楚。
4. **腰線與簷口**：每層樓交界放一圈倒置 `<石>_stairs` 或 `<石>_slab top`；屋頂下方放一圈倒置 `<木>_stairs` 當簷口托架。
5. **上層出挑**：二樓比一樓外推 1 格，下方用倒置 `<木>_stairs` 或 `<木>_fence` 撐（中世紀、日式町屋）。
6. **牆面圖案**：大面白牆用 `<木>_log` / `<木>_planks` 做桁架斜撐（X 形、V 形）；石牆用 `chiseled_*` 每隔 4–6 格點一個。
7. **色彩分區**：基座深、主體中、屋頂深或對比；三段式配色比全同色好看。
8. **牆面附件**：`<木>_trapdoor`（開啟）當百葉/木板、`iron_bars` 當格柵、`lantern` 掛在 `<木>_fence` + `iron_chain`、`wall_banner`、`flower_pot` 窗台盆栽、`vine` / `glow_lichen` 爬藤（少量）。

## 2. 屋頂
1. **樓梯＋半磚**：坡面用 `<材>_stairs`（高側朝屋脊，見 `weirdo_direction`），屋脊用 `<材>_slab top` 或整塊；每隔 2–3 格插一個 `<材>_slab` 打破坡面的直線。
2. **簷口**：屋頂最外一圈比牆外挑 1 格，下方放倒置 `<木>_stairs` 或 `<木>_slab top`，正面看有厚度。
3. **屋脊**：整條 `<材>_slab top`；兩端各高一格做收頭（`<材>` 整塊 + `lightning_rod` / `end_rod` / `<石>_wall`）。
4. **翹角（中日式）**：屋角最後 2–3 格逐格升 1，用 `<材>_slab` 疊；角尖放 `lightning_rod` 或 `gold_block`。
5. **屋頂窗／老虎窗**：坡面中段做 2 寬 3 高小屋頂突出，內放 `glass_pane`。
6. **煙囪**：`cobblestone_wall` 或 `brick_block` 2×1 高出屋脊 2 格，頂 `campfire`（有煙）或 `<石>_slab`。
7. **多層簷**：大殿或塔用兩層屋頂，上層縮 3–4 格；層間留 2 格高牆（放 `<木>_fence` 欄或 `red_stained_glass_pane`）。
8. **平屋頂不留白**：女兒牆（`<石>_wall` 或 `<石>_slab`）＋ 屋頂設備（`iron_trapdoor`、`barrel`、`lightning_rod`）或屋頂花園（`grass_block` + `azalea`）。
9. **圓錐/穹頂**：逐層縮半徑，樓梯每圈一種方向；穹頂用 `smooth_sandstone_stairs`/`quartz_stairs` 從外向內逐格升。
10. **破格屋頂**：兩坡高低不一致（一坡長一坡短）比對稱屋頂更有味道。

## 3. 開口
1. **窗框**：窗洞四周用不同材質（`polished_andesite`、`stripped_<木>_log`、`<木>_planks`），窗台 `<石>_slab` 或倒置 `<木>_stairs`，窗楣 `<木>_slab top`。
2. **窗內縮 1 格**：玻璃不與牆面齊平，`glass_pane` 放在牆厚的內側。
3. **百葉／窗框**：兩側 `<木>_trapdoor open_bit=True`（`direction` 依牆面），上方 `<木>_trapdoor` 遮陽。
4. **分格**：大窗用 `glass_pane` 分格（記得 `auto_connect()`）；彩窗用 `<色>_stained_glass_pane` 十字或菱形拼。
5. **拱門**：寬 3：兩側倒置 `<石>_stairs` + 中央整塊；寬 5：兩側倒置樓梯、次外 `<石>_slab top`、中央整塊；尖拱（哥德）加高一層。
6. **門廊**：門前 2 格深小屋頂 + 兩根 `<木>_fence` 或 `<木>_log` 柱 + 台階 `<石>_stairs`。
7. **門要放兩格**：`<木>_door` 下格 `upper_block_bit=False`，上格 True，`minecraft:cardinal_direction` 一致。雙開門用 `door_hinge_bit` 左右相反。
8. **箭孔／通風口**：1 格 `air` 或 `iron_bars`，每 3–4 格一個，讓大石牆有呼吸。

## 4. 柱梁與結構表現
1. **柱**：`<木>_log`（`pillar_axis=y`）、`stripped_<木>_log`、`<石>_wall`（細柱）、`<木>_fence`（極細）、`quartz_pillar`；柱礎 `<石>` 整塊、柱頭 `<石>_slab` 或倒置 `<石>_stairs`。
2. **梁**：橫梁 `<木>_log pillar_axis=x` 或 `z`（沿梁方向），在天花板下露出；梁與柱交會處放 `<木>_stairs` 斜撐。
3. **飛扶壁／支撐**：外牆每 4–6 格一個 `<石>_wall` 或 `<石>_stairs` 斜撐到地面。
4. **桁架**：白牆 + 深色 `<木>_log` 網格（水平、垂直、斜撐）。
5. **欄杆**：`<木>_fence`、`<石>_wall`、`iron_bars`、`<木>_trapdoor`；轉角用 `<木>_fence_gate` 或整塊收頭。
6. **樓梯**：室內用 `<木>_stairs` 每格升 1，寬 2；外側 `<木>_fence` 扶手；樓梯出口留 2 格頭部空間；螺旋梯繞 `<木>_log` 中柱。

## 5. 地面與台基
1. **台基**：建築站在 1–2 格高的台基上（`<石>` 漸層），四周台階 `<石>_stairs`，比直接落地有份量。
2. **小徑**：`grass_path` / `gravel` / `coarse_dirt` / `andesite` 加權隨機，寬 2–3，邊緣不整齊。
3. **廣場拼花**：`stone_bricks` + `polished_andesite` 棋盤、對角線、外框 `chiseled_stone_bricks`；中央圓形用 `<色>_glazed_terracotta`。
4. **階差**：庭院分 2–3 個高程，用 `<石>_slab` 做半格差與矮牆 `<石>_wall`。
5. **地面不平整**：草地加 `moss_block`、`podzol`、`coarse_dirt` 斑塊，並零星放 `short_grass`、`fern`、`wildflowers`、`leaf_litter`。

## 6. 景觀
1. **樹**：樹冠不能是正方體。做法：主幹 `<木>_log` 5–7 高，主幹上部 2–3 根斜出的枝（`<木>_log pillar_axis=x/z` 或 `<木>_wood`），每根枝末端一團 3×3×2 或 5×5×3 的球形 `<木>_leaves`（`persistent_bit=True`，去掉八個角），整體剪影不對稱。針葉樹：逐層縮的環（半徑 3-2-3-2-1-1-0）。
2. **灌木**：`azalea`、`flowering_azalea`、`bush`、`<木>_leaves` 單格或 2×2 團，沿牆腳、路邊、轉角放。
3. **花圃**：`<木>_trapdoor` 或 `<石>_wall` 圍邊，內 `dirt` / `moss_block` + 花（`poppy`、`allium`、`cornflower`、`pink_petals growth=3–7`）。
4. **水景**：底與四邊實心（`prismarine_bricks`、`dark_prismarine`、`stone_bricks`），`water liquid_depth=0` 填滿，邊 `<石>_slab`，內 `waterlily`、`seagrass`，岸邊 `reeds`。噴泉：中心柱 `<石>_wall` + 頂 `water` 源。
5. **燈柱**：`<木>_fence` ×3 + `lantern hanging=True` 掛在 `<木>_slab` 下；或 `<石>_wall` ×2 + `glowstone` + 四周 `<石>_slab` + 頂 `<石>_slab`（石燈籠）。
6. **圍籬與門**：`<木>_fence` + `<木>_fence_gate`；石牆 `<石>_wall` + 每 4 格 `<石>` 整塊柱（`wall_post_bit`）。
7. **雜物**：`barrel`、`hay_block`、`composter`、`campfire`、`cauldron`、`chest`、`bell`、`decorated_pot`、`scaffolding` 放在角落與門邊，1–3 個一組。
8. **地形融合**：結構邊緣留 1–2 格草地/小徑漸變，不要建築邊界就是硬切邊。

## 7. 室內（文字配方）
- **桌**：`<木>_fence` 腳 + `<木>_pressure_plate` 桌面；長桌：`<木>_fence` 兩端 + `<木>_slab top` 桌面；圓桌：`<木>_fence` + `<木>_trapdoor` 四面開啟。
- **椅／沙發**：`<木>_stairs` 朝桌；扶手兩側 `<木>_trapdoor open_bit=True`；沙發用 `<色>_wool_stairs` 或 `<色>_wool` + `<色>_carpet`。
- **床**：`bed` 兩格（`direction` + `head_piece_bit`）；床頭 `<木>_slab` 或 `<木>_trapdoor`，床邊 `<木>_fence` + `lantern` 或 `<色>_candle` 夜燈。
- **櫃／書架**：`bookshelf`、`chiseled_bookshelf books_stored=63`、`<木>_shelf`、`barrel`、`chest`；上方 `flower_pot`、`decorated_pot`、`candle`。
- **廚房**：`furnace` / `smoker` / `blast_furnace` 一排，`cauldron fill_level=6` 水槽，`<木>_trapdoor` 櫃門，`hay_block` 或 `barrel` 儲藏，`composter`。
- **壁爐**：`brick_block` 或 `<石>` 框 3 寬 3 高，內 `campfire` 或 `soul_campfire`，上方 `<石>_slab` 爐台，煙道向上到屋頂煙囪。
- **吊燈**：天花板 `iron_chain` 1–2 格 + `lantern hanging=True`；大吊燈：`iron_chain` + `<木>_fence` 十字 + 四角 `lantern` / `candle`。
- **地毯**：`<色>_carpet` 拼圖案（兩色棋盤、外框內填）；走道 `red_carpet` 一條。
- **牆面**：`frame`（物品框）、`wall_banner`、`painting` 是實體不能放，改 `frame` 或 `<色>_glazed_terracotta` 一塊。
- **隔間**：室內用 `<木>_fence` + `<木>_trapdoor` 做半高隔屏，或 `bookshelf` 牆。
- **重點**：每個房間至少 1 件家具 + 1 個光源 + 1 個小物；空房間比沒房間更糟。

## 8. 照明
1. **隱藏光源**：地板下一格 `glowstone` / `sea_lantern`，地板用 `<色>_carpet`（透光）；天花板內 `light_block_15` 放在空氣位置（隱形）。
2. **燈具要有支架**：`lantern` 掛 `iron_chain`、`<木>_fence`、`<木>_trapdoor`；不要直接浮在牆上。
3. **不要整排 `sea_lantern`**：用 `lantern`、`<色>_candle`、`shroomlight`（藏在 `<木>_trapdoor` 後）交替。
4. **燈柱間距 6–8 格**；室內每 5×5 一個光源。
5. **牆面火把**：`torch torch_facing_direction=<方向>`（值是火把所在牆面的方向反向：貼在西牆用 `east`）。
6. **色溫分區**：室內暖光（`lantern`、`shroomlight`、`ochre_froglight`）、科幻冷光（`sea_lantern`、`end_rod`、`verdant_froglight`）、儀式空間微光（`candle`、`soul_lantern`）。

## 9. 常見「AI 味」與修法

| 症狀 | 修法 |
|---|---|
| 整面單一方塊 | 漸層配方 3–4 種加權隨機；加柱、腰線、窗 |
| 平屋頂大方盒 | 加坡屋頂或至少女兒牆 + 屋頂設備；量體拆成 2–3 個高低不同的塊 |
| 屋頂沒有簷 | 外挑 1 格 + 倒置樓梯簷口 |
| 正方形樹 | 分枝 + 不對稱球形樹冠，去角 |
| 玻璃大牆 | 用 `glass_pane` 分格、加 `<木>_trapdoor` 或 `iron_bars` 分割、每 3 格一根柱 |
| 無室內 | 每個房間至少家具 + 光源 + 小物 |
| 燈光均勻 | 隱藏光源 + 少量可見燈具 |
| 對稱到無聊 | 一側加翼樓、煙囪、陽台或樹，打破對稱 |
| 沒有台基 | 抬高 1–2 格 + 台階 |
| 牆與地面硬切 | 牆腳一圈 `<石>_slab`、灌木、小徑漸變 |
| 全部同色 | 基座 / 主體 / 屋頂三段配色 |
| 窗戶浮在牆上 | 窗框 + 窗台 + 內縮 1 格 |
| 門是一格洞 | 兩格門 + 門廊 + 台階 |
| 樓梯方向錯 | 依 `weirdo_direction`：高側朝屋脊/朝上 |
| 樹葉消失 | `persistent_bit=True`（Builder 預設） |
| 玻璃板/牆孤立十字 | `auto_connect()` |

## 10. 自檢（細節 pass 完成後跑一次）
- `M.stats()`：palette 種類 ≥ 12（小建築）/ ≥ 20（中大型）；最大單一方塊占比 ≤ 60%（地基、地形除外）。
- 每個立面：有凹凸？有腰線或簷口？空白牆面 ≤ 8 格？
- 屋頂：樓梯方向正確？有簷？有屋脊收頭？
- 開口：門兩格？窗有框？玻璃板已連接？
- 室內：每房間家具 + 光源 + 小物？樓梯出口頭部空間 2 格？
- 景觀：至少一棵非正方形樹或一組灌木？地面有變化？
- 渲染圖打開看：有沒有浮空方塊、穿模、被樹葉擋住的入口？
