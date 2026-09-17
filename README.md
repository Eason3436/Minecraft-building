# Minecraft 建築

用 AI 設計與生成 Minecraft 基岩版建築的工作資料夾。

## 內容

- `structures/` — 生成的建築檔（`.mcpack`）、渲染圖與繁體中文使用說明，一個建築一個資料夾
- `docs/` — 建築需求、風格與尺寸的筆記

## 建築清單

| 建築 | 行為包名稱（世界設定中啟用） | 版本 |
|---|---|---|
| 金門赤灣大橋 | 金門赤灣大橋 | 1.0.0 |
| 亞特蘭提斯太空梭 | 亞特蘭提斯太空梭 | 1.0.0 |
| 晴空之塔 | 晴空之塔 | 1.0.0 |
| 聖彼得大教堂 | 聖彼得大教堂 | 初版 1.0.0、完整精修版 2.0.0、車站雙線鐵路版 3.0.0（同一個包的三個版本，只啟用其中一個） |
| 綠蔭雙軌鐵路系統合集 | 綠蔭雙軌鐵路系統合集 | 1.0.0，合併包，內含 10 個結構（預覽圖在 `預覽圖/`） |
| 夜幕六型主動刷怪塔 | 夜幕六型主動刷怪塔 | 1.0.0，模擬距離 4；格式與靜態配置已檢查，尚未遊戲實測 |

每個資料夾內含：`<名稱>.mcpack`、`<名稱>_使用說明.txt`、`<名稱>_整體渲染.png`、`<名稱>_內部剖視.png`

## 結構 ID 與放置指令

**拿結構方塊的指令（所有建築共用）：**
```
/give @s structure_block
```

共通步驟：
1. 雙擊 `.mcpack` 匯入 → 世界設定啟用行為包 → 創造模式、開啟作弊
2. 輸入上面的指令拿到結構方塊，放下後切到「載入」，輸入下表的結構 ID（旋轉 0、無鏡像、完整性 100%）
3. 或者不用結構方塊，直接輸入各建築的 `/structure load` 或 `/function` 指令

範例座標 `100 64 100` 請換成自己的空地；原點是包圍盒最小 X/Y/Z 角。

### 金門赤灣大橋

- 結構方塊 ID：`redbay_260915:part_1`、`part_2`、`part_3`、`part_4`（沿 +X 各偏移 64）
- 一鍵放置（三步，原點自訂，兩行座標要一致）：
  ```
  /execute positioned 100 40 100 run function redbay_260915/prepare
  /execute positioned 100 40 100 run function redbay_260915/build
  /function redbay_260915/cleanup
  ```
- 逐段：`/structure load redbay_260915:part_1 100 40 100`、`part_2 164 40 100`、`part_3 228 40 100`、`part_4 292 40 100`
- 尺寸 256 × 31 × 100；橋面在原點 Y+27，示例原點 Y=40 適合海面 Y=63

### 亞特蘭提斯太空梭

- 結構方塊 ID：`shuttle_260915:atlantis`（單一結構）
- 一鍵放置：`/structure load shuttle_260915:atlantis 100 64 100`
- 尺寸 61 × 53 × 172；建議原點 Y=64，最高點 Y=235

### 晴空之塔

- 結構方塊 ID：`sky_260915:skytower`（單一結構）
- 一鍵放置：`/structure load sky_260915:skytower 100 64 100`

### 聖彼得大教堂

三個版本共用結構 ID 前綴 `vatican_260915:part_<X列>_<Z列>`，每件 64 × 168 × 64，偏移 = (X列×64, 0, Z列×64)。

| 版本 | 分件數 | 一鍵放置（固定在主世界，不是玩家腳下） | 施工範圍 |
|---|---|---|---|
| 初版 | 12（`part_0_0`～`part_2_3`） | `/function vatican_260915/place` | X 100..291、Y 64..231、Z 100..355 |
| 完整精修版 | 30（`part_0_0`～`part_4_5`） | `/function vatican_260915/place` | X 100..419、Y 64..231、Z 100..483 |
| 車站雙線鐵路版 | 40（`part_0_0`～`part_4_7`） | 全部：`/function vatican_260915/place`<br>已有精修版只加車站：`/function vatican_260915/station` | X 100..419、Y 64..231、Z -28..483 |

- 自訂原點（初版）：`/execute positioned X Y Z run function vatican_260915/prepare` → 同座標 `.../build` → `/function vatican_260915/cleanup`
- 中止／清理：`/function vatican_260915/cancel`、`/function vatican_260915/cleanup`
- 逐件範例：`/structure load vatican_260915:part_0_0 100 64 100`，完整座標表見各版本的使用說明

### 綠蔭雙軌鐵路系統合集

沒有 function，全部用 `/structure load`。直線 29 × 56、轉彎 56 × 56；直線接續每段 Z +56，旋轉 90° 向東每段 X +56。

| 系列 | 結構方塊 ID | 原點 Y（平地 Y=64） |
|---|---|---|
| 地面綠蔭鐵路 | `verdant_rail_260916:straight`、`verdant_rail_260916:curve` | 62 |
| 地下鐵路 | `metro_rail_260916:straight`、`metro_rail_260916:curve` | 48 |
| 綠蔭高架鐵路 | `verdant_viaduct_260916:straight`、`verdant_viaduct_260916:curve` | 62 |
| 高架鐵路（簡潔版） | `viaduct_rail_260916:straight`、`viaduct_rail_260916:curve` | 62 |
| 車站（接地面綠蔭） | `verdant_station_260916:suburban`（郊區站）、`verdant_station_260916:central`（中央站） | 62 |

拼接範例（直線 → 轉彎 → 向東直線）：
```
/structure load verdant_rail_260916:straight 100 62 100
/structure load verdant_rail_260916:curve 100 62 156
/structure load verdant_rail_260916:straight 156 62 184 90_degrees
```
車站範例：直線原點 X=a 時，郊區站 X=a-8、中央站 X=a-16；例如 `/structure load verdant_station_260916:suburban 92 62 156`。

### 夜幕六型主動刷怪塔

- 結構 ID：`nightfall_260917:active_six`，單一結構，寬 35 × 深 47 × 高 60 格。
- 六層定時沖水、168 個預裝水桶的發射器、四活塞三叉戟處理室、四路物品分類與溢流箱。
- 對照 Mojang `v1.26.50.4` 官方方塊資料，目標為基岩版 26.50–26.51，模擬距離 4。
- 在空曠海面上方放置：`/structure load nightfall_260917:active_six 100 140 100`。
- 對應掛機點：`/tp @s 116.5 154 120.5`；候選刷怪面距離約 25.02～42.52 格。
- 載入時為停機狀態，需依說明投放三叉戟並啟動各層環路。已驗證 NBT、庫存、漏斗路徑、靜態光照與距離；**尚未在遊戲內驗收紅石、水流及擊殺，不承諾產量**。
- 成品在 `structures/夜幕六型主動刷怪塔/`，含 `.mcpack`、完整使用說明、整體渲染與內部剖視。

## 工作流程

1. 在對話中描述要蓋的建築（類型、風格、尺寸）
2. AI 生成 `.mcpack` 與使用說明 `.txt`
3. 把成品放進 `structures/<建築名稱>/` 並 commit
