# 任務書：哈利法塔（Burj Khalifa）與杜拜噴泉湖區

## 1. 需求摘要
- 使用者：「還原哈利法塔」。還原杜拜哈利法塔：Y 形三翼平面、逐層螺旋退縮的翼樓、頂部尖塔，含周邊哈利法塔公園、哈利法湖與杜拜噴泉、杜拜購物中心、巴哈爾市集（Souk Al Bahar）。
- 實高 828 m 超過基岩版世界高度 384 格 → 縮放 **1 格 = 2.25 m（1:2.25）**，塔高 368 格（地面層 y=4 到尖塔頂 y=372）。
- 名稱：哈利法塔；namespace `burjkhalifa_261118`；分件 id `p_X_Z`。

## 2. 尺寸與原點
- 256（X）× 376（Y）× 256（Z），4×4 分件，每件 64×?×64。塔所在 4 件（X 0–127、Z 0–127）高 376，其他 12 件高 40。
- 原點 = 西北下角。北 = −Z。y=0–2 地基，y=3 地面，y=4 起建築。
- 載入要求：超平坦世界、站在地面（腳 y=−60）執行 → 塔頂 y=312，低於 320 上限。

## 3. 拆解決策
單一生成器、一個陣列建完、存檔切 16 件。pass：塔身骨架（平面遮罩）→ 帷幕牆細節（鰭片、機電層、退台）→ 室內（大廳、核心筒、觀景台、餐廳、一般樓層）→ 景觀（公園、湖、噴泉、商場、市集、道路、棕櫚）。

## 4. 模組與座標
| 模組 | 範圍 | 備註 |
|---|---|---|
| 塔身 | 中心 (84,84)，三翼方向 北/東南/西南，基部翼長 38、半寬 8.5 | 退台 y=40+8k，33 次，翼 k%3 輪流內縮（螺旋） |
| 核心筒 | x80–88 z80–88 | 氣泡柱電梯 (82,82) 到 148 樓觀景台、梯子 (87,82) |
| 樓板 | 每 4 格一層（≈2.25 個真實樓層） | 大廳 y4–11 挑高 |
| 機電層 | 樓板 36/76/132/192/236 | 深色百葉帶 |
| 122 樓 At.mosphere 餐廳 | 樓板 200 | |
| 124/125 樓 At the Top | 樓板 208/212 | 208 有戶外退台 |
| 148 樓 At the Top SKY | 樓板 252 | 氣泡柱電梯終點 |
| 152–154 樓 Lounge | 樓板 256/260 | 屋頂 264 |
| 頂部塔冠 | y264–299 | 玻璃延續、繼續退台 |
| 尖塔 | y300–372 | 鋼構漸縮、避雷針頂 |
| 入口雨庇 | 三翼尖端 | |
| 公園 Y 形水道 | 沿三翼軸線延伸 | |
| 哈利法湖 | 橢圓 中心 (150,168) rx92 rz40 | 噴泉以白/淡藍玻璃靜態水柱表示 |
| 杜拜購物中心 | x164–252 z20–118 高 ~23 | 水族館大水箱 |
| 巴哈爾市集 | x24–112 z214–250 | 阿拉伯風、風塔 |
| 步行橋 | x70–73 z144–192 | |
| 道路 | 北 z0–9、西 x0–9 | |

## 5. 調色盤
帷幕玻璃 light_blue_stained_glass / light_gray_stained_glass；鋁鰭 polished_diorite；退台屋頂 smooth_quartz；機電層 tinted_glass + polished_deepslate；核心 white_concrete / light_gray_concrete；樓板 smooth_stone、quartz_block；燈 sea_lantern、lantern、end_rod；尖塔 iron_block、light_gray_concrete、iron_bars、lightning_rod；地面 smooth_sandstone、sandstone、cut_sandstone、grass_block；水 water、bubble_column、soul_sand；棕櫚 jungle_log + jungle_leaves；市集 chiseled_sandstone、sandstone_stairs；家具 bed、stairs、fence、carpet、flowering_azalea、bookshelf。

## 6. 細節清單
- [x] 三翼退台呈螺旋（逆時針）
- [x] 垂直鰭片節奏
- [x] 機電層深色帶
- [x] 退台屋頂與玻璃欄杆
- [x] 尖塔漸縮
- [x] 大廳、觀景台、餐廳室內
- [x] 公園水道、湖、噴泉、商場、市集、棕櫚

## 7. 驗收
- NBT 重新解析逐格比對；方塊與 state 對照 1.26.60 官方表；塔頂不超過 y=372。
- 氣泡柱四周不漏水（水平鄰格皆非空氣）；湖與水道水面鄰格封閉。

## 8. 進度記錄
- 2026-11-18 開工。
- 2026-11-18 完成：塔身、室內、地景、16 分件、渲染、打包、放置台報到。重跑：`cd work/哈利法塔 && python3 export.py`（需同目錄 mojang-blocks.json v1.26.60.5），再跑 register_pack.py 與 building_placer/build.py。
