---
name: minecraft-bedrock-structure
description: 讓 AI 依使用者需求從零設計、生成或修改任何類型的 Minecraft 基岩版建築（住宅、城堡、商店、圖書館、寺廟、科幻基地、橋梁、鐵道、建築群、機關設施），也包括「照這張圖片蓋」「拆成可拼接的模組合集」「這棟太單調幫我加細節」「換風格或材質」這類要求。流程是任務書驅動：先寫 build_plan.md 決定拆解方式、模組、調色盤與檢查清單，再分 pass 建模（骨架→細節→室內→景觀），用官方方塊表查詢可用方塊與 state，序列化成 mcstructure、渲染檢視、打包行為包，最後交付 .mcpack、繁體中文使用說明 .txt、整體渲染 PNG 與內部剖視 PNG，不交付或覆蓋 db。使用者要 AI 蓋建築、做可匯入 MC 基岩版的結構、修改既有結構、或提供參考圖要求復刻時都要用；Java schematic 與單純遊戲問答不適用。
---

# 基岩版建築結構製作

把需求做成實際可載入的原版方塊建築。終點是使用者匯入行為包、啟用、用結構方塊放置，不是規劃書或示意圖。

這份 SKILL.md 是流程骨架；細節放在 `references/`，每個階段會說明何時讀哪一份：

| 檔案 | 何時讀 |
|---|---|
| `references/task-decomposition.md` | 階段 0 寫任務書、階段 2 決定拆不拆、上下文溢出後續跑 |
| `references/image-reference-workflow.md` | 使用者給了參考圖片 |
| `references/block-catalog.md` | 階段 4 選方塊、查 state 含義、遇到「這個方塊叫什麼」 |
| `references/style-palettes.md` | 階段 4 依風格挑調色盤與漸層配方 |
| `references/detailing-techniques.md` | 階段 5 細節 pass、階段 6 自檢、使用者說「太單調」 |
| `references/format-and-pitfalls.md` | 階段 4–7 序列化、驗證、打包時的規格與已知坑 |

## 通用建築與自由命名

每次先按需求設計空間、功能和風格，再選生成方法；寺廟只是範例，沒有固定類型、尺寸或名稱。

- 名稱由使用者指定；沒指定就依主題取名，不為命名停下來問。顯示名稱可以是中文；檔名避開系統不允許的字元。
- 技術載入名稱是本次的 `namespace:id`，例如 `starport:research_station`。使用者給合法 ID 就用它；中文或不合法的保留為顯示名稱，另產生合法 ID 並在說明寫清對應。用獨特 namespace（可含日期）避免與世界內舊結構同名。
- 不沿用先前對話、範例或來源的名稱當預設。從零建立是正常入口，只在修改既有建築時讀來源。

## 交付契約

交付目錄只放四個檔案：`<建築名稱>.mcpack`、`<建築名稱>_使用說明.txt`、`<建築名稱>_整體渲染.png`、`<建築名稱>_內部剖視.png`。渲染圖是正式附件。`.mcstructure`、生成器原始碼、任務書、方塊表、驗證 JSON 留在 `work/<專案>/`。不另打 ZIP、不交付 db、不修改使用者的遊戲世界。來源是 db ZIP 也只在工作副本讀，最後仍以行為包發佈。

## 階段 0：建立任務書（先做這件事）

大建築失敗的原因通常不是不會蓋，而是中途上下文用完、模組互相打架、或反覆回頭問小事。所以第一輪就在 `work/<專案>/build_plan.md` 寫任務書，範本在 `references/task-decomposition.md` 第 3 節。內容：需求摘要、風格關鍵字、尺寸與原點、拆解決策、模組表（範圍／接口／函式／勾選）、調色盤、細節檢查清單、驗收條件、參考圖觀察清單、進度記錄。

任務書寫好後**自主連續執行到交付**。自己能決定的（命名、材質、房間配置、樹的位置、渲染角度）就決定並寫進任務書；只有尺寸超限無法分件、來源損毀、需求矛盾這幾種才停下來問，而且一次問完並附預設選項。每完成一個模組就更新勾選；上下文溢出或新開對話時，先讀任務書和 `work/` 現況再從第一個未勾選項續跑，不重頭來、不改 namespace/id。

## 階段 1：理解需求與來源

- 讀對話確認基岩版、風格、名稱、功能、尺寸。寬=X、深=Z、高=Y；使用者說 61×61×35（寬深高），NBT `size` 是 `[61,35,61]`。
- 單一結構 X/Z 各不超過 64；更大就分件＋偏移載入，不默默縮小。
- **有參考圖片**：讀 `references/image-reference-workflow.md`，先寫觀察清單、估比例、做材質對應表，填進任務書第 8 節，之後每個 pass 都拿渲染圖回頭比對。
- 來源檔：`.mcstructure` 讀未壓縮 little-endian NBT 檢查尺寸、palette、states、version；ZIP 先列內容與解壓大小，拒絕絕對路徑與 `..`，只解到 `work/`；db 在副本用 `amulet-leveldb` 找 `structuretemplate_<namespace>:<id>` 鍵，只讀不寫，不開啟運行中的遊戲資料庫。

## 階段 2：拆解決策

讀 `references/task-decomposition.md` 第 1 節，看**耦合度**而不是大小：

- 模組之間只靠數字約定（軌道高度、道路寬、接縫）就能各自成立 → 拆成模組，各自函式或檔案、各自 id，先寫接口表再各自建，最後組裝。鐵路合集、車站群、村莊、城牆段都是。
- 室內與外殼互相牽動（民宅、教堂、太空梭、塔） → 同一個生成器，但分「骨架 → 細節 → 室內 → 景觀照明」四個 pass，每個 pass 一個函式。
- 機制優先（刷怪塔、農場、紅石） → 先做最小單元驗證，再複製，最後包外殼。
- 超過 64×64 的單體 → 一個陣列建完整模型，存檔時切分件。

把結論與模組表寫進任務書。模型能力越弱越該拆細，不確定就拆。

## 階段 3：座標規劃

以座標範圍分配每個模組：外框、入口面向、樓梯、庭院、植栽、照明，決定原點、面向、地基高度。每個模組寫「範圍、入口方向、與鄰接模組的接口」。各區留通行與頭部空間（門 2 高、室內淨高 3–4、樓梯出口上方 2 格）。依類型決定功能配置：住宅有起居與臥室、圖書館有書架閱讀區與樓梯、城堡有城牆門樓大廳、科幻基地有氣閘控制室設備區、建築群有道路與公共空間。不要直接縮放離散座標。

## 階段 4：選方塊（決定作品上限的一步）

單一方塊大面積是「看起來像 AI 蓋的」最主要原因。開工前：

1. 讀 `references/style-palettes.md` 找最接近的風格，取其主材／次材／點綴／屋頂／窗／門／燈／地面／景觀，再依需求調整；需要更多選擇時翻 `references/block-catalog.md`（按用途分族，含 state 對照表與基岩版命名例外）。
2. 在任務書第 5 節列出 **12–25 種方塊的調色盤**，每個附用途與關鍵 state。
3. 用官方表核對每個 ID 與 state 都存在，不要猜名字（`chain`→`iron_chain`、`oak_trapdoor`→`trapdoor`、`bricks`→`brick_block` 這類例外很多）：
   ```
   python <skill>/scripts/block_catalog.py --metadata <mojang-blocks.json> search <關鍵字...>
   python <skill>/scripts/block_catalog.py --metadata <mojang-blocks.json> states <方塊>
   python <skill>/scripts/block_catalog.py --metadata <mojang-blocks.json> families
   ```
   生成器內也可用 `M.search('copper','stairs')`、`M.describe('spruce_stairs')`。

底線（除非使用者要極簡風）：主要牆面至少 3 種同色系方塊漸層；坡屋頂用樓梯＋半磚不用整塊；窗有框且不是整片玻璃；每個立面至少一種凹凸層次；每個房間至少家具＋光源＋小物。

環境：需要 `amulet-nbt`、`numpy`（建模）、`Pillow`（渲染）；優先用已有預編譯 wheel 的 Python，套件放工作區或虛擬環境，不升級全域。方塊表用目標版本的 Mojang 官方 `mojang-blocks.json`（連結在 `references/format-and-pitfalls.md`），記錄版本；套件與資料表不打進行為包。

## 階段 5：建模與序列化

用 `scripts/structure_builder.py` 的 `StructureBuilder`：依尺寸建陣列，`block/put/box` 放方塊，`auto_connect()` 補玻璃板與牆的連接，`stats()` 自檢，`save()` 存未壓縮 little-endian `.mcstructure`。生成器由你為本次建築編寫，工具不預設外觀；重複元件（燈柱、窗、樹、欄杆）寫成小函式共用，同一種東西全區長一樣。

按 pass 做，每個 pass 一個函式、做完渲染一次：

1. **骨架**：台基、量體、屋頂剪影、開口位置。只放主材，先確認比例對。
2. **細節**：翻 `references/detailing-techniques.md` 逐條套用——牆面漸層、凹凸、腰線簷口、窗框窗台、屋脊收頭、柱梁、地面拼花。
3. **室內**：家具、光源、小物、樓梯、隔間。
4. **景觀與照明**：非正方形的樹、灌木、小徑、水景、燈柱、雜物、地形融合。

存檔前跑 `M.stats()`：小建築 distinct_blocks ≥ 12、中大型 ≥ 20；最大單一方塊占比 > 60%（地基與地形除外）就回去補漸層。

規格：`bool→ByteTag`、`int→IntTag`、`string→StringTag`；樹葉 `persistent_bit=True`；樓梯 `weirdo_direction` 高側朝屋脊；門與床兩格；水池有底有邊；花與蠟燭有支承。NBT 必備 `format_version=1`、`size`、`structure.block_indices` 兩層、`entities` Compound List、`palette.default.block_palette` 與 `block_position_data`、`structure_world_origin`；索引 `x*(Y*Z)+y*Z+z`；主要層 `air` 會清空原地形、`-1` 保留。箱子內容、告示文字、旗幟圖案要寫 `block_position_data`。完整規格與坑見 `references/format-and-pitfalls.md`。

只有需求是寺廟且適合時才複製 `scripts/temple_example.py` 修改；其他建築可借它的 put/box/ring、柱梁、屋頂函式另寫生成器。

## 階段 6：檢查與修正

1. 重新解析 NBT：尺寸、索引數量與範圍、palette/state 型別與名稱、原點、block_position_data 索引、屋脊最高點未越界。
2. 渲染整體圖與內部剖視圖（`scripts/render_example.py` 只適用寺廟範例的檔案格式，其他建築自行調整畫布、相機、標題、剖切高度）。**打開圖看**，修屋頂空洞、浮空方塊、穿模、入口堵塞、植栽侵入走道。
3. **對照任務書**：逐條核對第 6 節細節清單與第 7 節驗收條件；有參考圖就把渲染圖與參考圖並排，依 `image-reference-workflow.md` 第 6 節列差異表，修一輪再渲染。
4. 不用「超過兩萬方塊」之類門檻衡量品質；不用 AI 概念圖冒充方塊成果；無法遊戲實測就寫「格式驗證通過，尚未在遊戲內實測」。

### 渲染圖交付要求
- 整體圖等角或斜俯視，完整呈現建築、屋頂、景觀；淺色乾淨背景，標本次名稱與尺寸。
- 內部圖移除屋頂或在合適高度剖切，呈現房間、家具、通道；切面依建築選，不固定 Y=10。無室內的建築（橋、軌道）改交同檔名的結構細節圖並在圖上說明。
- 兩圖依最終輸出的方塊、palette、states 繪製；改了建築就重渲染，不沿用舊圖。
- 圖上註明「依方塊資料繪製，非遊戲截圖」與簡化之處。長邊 ≥ 1600 px，文字可讀，建築不裁切。實際打開看過再打包；最後回覆嵌入整體圖並給兩張圖連結。

## 階段 7：打包與交付

```
python <skill>/scripts/package_structure.py --structure <work/…/本次ID.mcstructure> --output-dir <交付目錄> --name <建築名稱> --namespace <namespace> --id <id> --min-engine-version <已核實版本> --preview <work/整體.png> --interior <work/剖視.png>
```

- 打包器處理單一結構；合集或分件時在 work 複製並擴充它，讓同一個 mcpack 含多個各自驗證過的 mcstructure，仍只交一個包、一份含偏移與載入順序的說明、兩張整組渲染圖。不逐件交多個包，不略過尺寸驗證。
- `manifest.json` 在包根，header/modules UUID 各自合法且不同，`modules.type=data`，結構路徑 `structures/<namespace>/<id>.mcstructure`，載入名 `<namespace>:<id>`；不多包一層資料夾。同一包更新保留 UUID 並加版本，新包用新 UUID。
- 說明檔寫：尺寸（寬深高與 X/Y/Z）、特色、匯入與啟用行為包、`/give @s structure_block`、切載入模式、完整 ID、`/structure load` 範例、空間與原點與面向、空氣覆蓋規則、測試狀態；多分件寫載入順序與偏移；有參考圖寫「復刻辨識特徵、已簡化之處」。讓不懂 db 的人也能完成。
- 最後檢查 ZIP CRC、manifest、內嵌結構位元組、路徑與 identifier 一致，交付目錄恰好四個檔案，兩張 PNG 可解碼且對應最終建築。回覆四個可點擊的絕對路徑、整體圖預覽、最短載入提示，並更新任務書進度為完成。
