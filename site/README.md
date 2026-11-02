# 方塊建築館（網站）

把 `structures/` 裡每個 Minecraft 基岩版建築做成可 3D 互動檢視、可下載的靜態網站。
建置時自動掃描所有 `.mcpack`，所以**新增建築只要放進 `structures/<建築名稱>/` 再 push**，Vercel 重新建置後就會出現在網站上，不需要改任何清單。

## 本機預覽

需要 Node.js 20.9 以上（不需要 Python）。

```bash
npm install        # 安裝 three.js 與 sharp（sharp 裝不起來也能建置）
npm run build      # 產生 site/dist/（約 10～20 秒）
npm run preview    # 開 http://localhost:4173/
```

`site/dist/` 是建置產物，已加入 `.gitignore`，不要提交。

## 部署到 Vercel

1. 到 [vercel.com](https://vercel.com) 用 GitHub 登入 →「Add New… → Project」→ 匯入 `eason3436/minecraft-building`。
2. Framework Preset 選 **Other**。其餘設定（安裝指令、`npm run build`、輸出目錄 `site/dist`、快取與下載標頭）都寫在根目錄的 `vercel.json`，不用手動填。
3. 按 Deploy。之後每次 push 到 GitHub，Vercel 都會自動重新建置部署（非 production 分支會產生預覽網址）。

網址採 hash 路由（`/#/b/<建築>/<版本>/<模型>`），純靜態託管，不需要 rewrite 設定。

## 新增建築的規則

建置腳本 `site/build.mjs` 會遞迴找出 `structures/` 下所有 `.mcpack`：

- `structures/` 底下第一層資料夾 = 一棟建築（首頁一張卡片）。同一棟建築底下的多個 `.mcpack`（例如 `聖彼得大教堂/初版/`、`霍格華茲島/分區成果/P01_P08/v003/`）是不同版本，進頁面後切換。
- 與 `.mcpack` 同一層的 `*_使用說明.txt` 會顯示全文並提供下載；`*_整體渲染.png`、`*_內部剖視.png` 是主要渲染圖；同層不含 `.mcpack` 的子資料夾（例如 `預覽圖/`）裡的圖片會放進圖庫。
- 分件組裝方式（自動判斷）：
  1. 包內 `functions/**/*.mcfunction` 有 `structure load <id> <x> <y> <z>`（可含 `execute … run`、`~` 相對座標或絕對座標）→ 依座標組裝。每個檔案一組；只有一行的檔案（`load_00`…`load_29`、`slow/step_0`…）依檔名前綴合併成一組。相同配置去重，被其他組完整包含的子集合（只放車站、單列）略過，所以可能得到多組（例如霜翎軍港的「船」與「港口」）。
  2. 沒有 function 但結構名稱是 `part_<i>_<j>`、`tile_x<i>_z<j>`、`p01_p02_<i>_<j>` 這類 → 偏移 `(i×64, 0, j×64)`。
  3. 其他多結構包（鐵道模組等）→ 每個結構是獨立模組，可在檢視器切換。
- 預設版本是方塊數最多的那個；首頁依結構命名空間結尾的日期（例如 `_261029`）由新到舊排序；分類依名稱關鍵字（建築／鐵道／載具／紅石／橋梁）。

## 目錄

```
package.json            三個指令：build / preview；依賴 three（固定版本）、sharp（選用）
vercel.json             Vercel 建置設定與 HTTP 標頭
site/build.mjs          建置腳本（Node，零額外依賴解析 ZIP 與 NBT）
site/serve.mjs          本機預覽用的小型靜態伺服器
site/lib/mcpack.mjs     ZIP（central directory + inflateRaw）、little-endian NBT、structure load 指令解析
site/data/block-colors.json  方塊顏色表（提交進 git，建置直接使用）
site/tools/gen_block_colors.py 重新產生方塊顏色表的工具
site/src/               前端：index.html、styles.css、app.js（路由與頁面）、viewer.js（three.js）、
                        worker.js（Web Worker）、mesher.js（網格化）、blocks.js（方塊外型分類）
```

## 輸出資料格式（site/dist）

| 路徑 | 內容 |
|---|---|
| `catalog.json` | 所有建築 → 版本 → 模型。版本含 manifest 名稱／簡介／版本、方塊數、下載檔（`files.mcpack/txt`，含原始中文檔名供 `download` 屬性還原）、圖片（`thumb` 縮圖、`large` 大圖、`full` 原始 PNG）、結構清單（ID、尺寸 [X,Y,Z]、方塊數、組裝偏移）。模型含 `kind`（assembly／part／module／single）、尺寸、方塊數、`parts[]`（體素檔 URL、偏移、尺寸）。 |
| `data/v/<雜湊>.bin` | 每個不重複的 `.mcstructure` 一個檔（內容雜湊命名，可永久快取），gzip 壓縮。解開後：`"MCV1"`、`u16 X, Y, Z`、`u16 調色盤數`、`u32 調色盤 JSON 長度`、`u32 run 數`、調色盤 JSON（`[[名稱, states?], …]`，補齊到 4 位元組）、`u16 值[run 數]`（補齊到 4 位元組）、`u16 長度[run 數]`。值 `0xFFFF` 是空；順序 y → z → x（x 最快）。空氣、屏障、結構空位、光源方塊視為空；含水方塊的次層只在主層是空的時候畫成水。 |
| `data/colors.json` | 用到的方塊 → `[頂 r,g,b, 側 r,g,b, 底 r,g,b, alpha×255]`。 |
| `img/<雜湊>-720.webp`、`-1800.webp` | sharp 產生的縮圖與大圖；沒有 sharp 時改用原圖。 |
| `files/<建築>/<版本>/…` | `.mcpack`、使用說明 `.txt`、渲染圖原始 PNG（ASCII 檔名）。 |
| `vendor/` | three.js（npm 套件複製過來，OrbitControls 改成相對路徑 import，不需要 import map 或 CDN）。 |

## 3D 檢視器

- 下載與網格化都在 Web Worker：分件組裝成一個體積（Uint16 調色盤索引，外圍留 1 格），每 64×32×64 一塊網格化，只產生外露面；完整方塊做 greedy 合併（同方塊且四角 AO 相同才合併）並計算每頂點環境光遮蔽。頂點屬性：位置 Int16（1/16 格）、法線 Int8、顏色 Uint8×4；網格上傳 GPU 後即釋放 JS 陣列。
- 外型：半磚、樓梯、柵欄／柵欄門、牆、玻璃板／鐵欄杆（依 `minecraft:connection_*`／`wall_connection_type_*`，缺 state 時看鄰居）、地毯／壓力板／雪層／鐵軌／紅石粉、門、活板門、燈籠、火把（含牆上火把）、蠟燭、鎖鏈／避雷針／末地燭、床、箱子、梯子、告示牌、按鈕、拉桿、藤蔓、花草作物（十字面）等；其餘畫成完整方塊。
- 半透明（玻璃、水、冰…）用頂點 alpha；光源方塊用不受光照的材質（微發光）。著色器加上每格微小明暗差與方塊格線，陰影貼圖只在幾何改變時重算。
- 剖切：只重新網格化剖切高度所在的那一層分塊（切面會產生頂面），上方分塊隱藏。

## 重新產生方塊顏色表

`site/data/block-colors.json` 涵蓋官方方塊表 1466 個方塊（另加舊名 `minecraft:chain`），格式：

```json
{ "minecraft:oak_planks": { "top": [162,131,79], "side": [162,131,79], "bottom": [162,131,79], "alpha": 1.0 } }
```

四個欄位一定都有；`alpha` 0 表示看不見的方塊。顏色是 Mojang 官方 bedrock-samples（`v1.26.60.5`）`resource_pack/blocks.json` → `terrain_texture.json` → `textures/blocks/*.png|tga` 的 alpha 加權平均色；草、樹葉、藤蔓、水等灰階材質套用生態域染色，花取花瓣顏色，對不到材質的用名稱關鍵字推測。要更新到新版方塊表時：

```bash
python3 -I site/tools/gen_block_colors.py --tag v1.26.60.5 --blocks work/mojang-blocks.json
```

（需要 Pillow 與 numpy；材質只下載到暫存快取資料夾，不會進倉庫。）

## 已知限制

- 顏色是材質平均色，沒有貼圖；樓梯轉角形狀（inner／outer）、開啟中的門、告示牌文字、旗幟圖案、方塊實體（箱子內容、盔甲座…）都簡化或省略。
- 剖切以整層分塊為單位重新網格化，大型模型（聖彼得大教堂）每次約 0.1～0.3 秒。
- 需要支援 WebGL 2 的瀏覽器（近年的 Chrome、Edge、Firefox、Safari 15+）。
