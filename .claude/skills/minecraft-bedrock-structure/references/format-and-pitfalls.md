# 來源與可重用經驗

- 官方方塊表：https://github.com/Mojang/bedrock-samples/blob/main/metadata/vanilladata_modules/mojang-blocks.json （實作時優先選對應遊戲版本的 tag，不默認 main 是使用者版本。）
- 結構格式：https://github.com/Bedrock-OSS/bedrock-wiki/blob/wiki/docs/nbt/mcstructure.md
- db 工具：https://github.com/Amulet-Team/Amulet-LevelDB （pip 1.x 的模組通常是 leveldb，其他版本可能不同；檢查實際 API。）

## 本次流程學到的修正

1. 61 寬 × 61 深 × 35 高 → NBT [61,35,61]，每層 130235 整數，兩層各自同長。
2. 來源原有 qqqq 為 5³，仍能重建成更大模板。來源有結構方塊自身的 block entity 時，不要一起複製進新寺廟造成誤存。
3. `.mcpack` 是 ZIP 容器但副檔名直接為 mcpack，manifest 在根；不是完整世界，不需 level.dat 或 db。
4. 只读 db 副本也可能更新鎖/日誌，所以不對原檔直接開庫。此 skill 不保留寫回 db 的程式碼。
5. palette version 是遊戲方塊資料版本，不等於 manifest 版本。範例沿用來源的 18168865；變更目標版本時重新確認。
6. 方塊 ID 會改名，例如 chain/iron_chain、weighted pressure plate；依正式表選擇，不用 Java 名稱硬套。不要用自動替換未知方塊為 air 來掩蓋錯誤。
7. 顏色判斷中 `air in name` 也會命中 stairs，導致階梯被畫成白色；air 需完整 ID 比較。
8. 樹葉 persistent、植栽不穿走道、樓梯出口留頭部空間、屋頂與上層牆連續。視覺檢查不能取代實際載入測試。
9. 水上 moss_carpet 與其上蠟燭可能失去支承；用可存活的睡蓮葉與有土壤支承的花瓣島嶼做蓮花意象，別聲稱原版有蓮花方塊。
10. 主要層 air 會清空包圍盒，-1 才保留原地形；次層 -1 不代表主要層也不覆蓋。
11. Empty entities list 應使用 Compound 元素型別；整數資料用 ListTag[IntTag] 而不是 IntArrayTag。
12. 新的專用 namespace 防止世界舊存檔優先於包內同名結構。說明檔需用包內實際 ID。
13. `block_version` 是遊戲版本編碼：`(major<<24)|(minor<<16)|(patch<<8)`，例如 26.50 為 `(1<<24)|(26<<16)|(50<<8)`；本專案既有生成器都用此算法，與 mojang-blocks.json 的版本要一致。
14. 26.x 起樓梯多了 `minecraft:corner` state（`none`/`inner_left`/…）。`StructureBuilder.block()` 預設取第一個值 `none`，遊戲載入後會依鄰接重算，不需要手動填。
15. `chain` 已改名 `iron_chain`，另有 `copper_chain` 系列；橡木活板門/門/按鈕/壓力板是無前綴的 `trapdoor`/`wooden_door`/`wooden_button`/`wooden_pressure_plate`。完整命名例外表在 `block-catalog.md` 第 1 節。
16. 牆、玻璃板、鐵欄、銅欄的連接是 state（`wall_connection_type_*`、`minecraft:connection_*`），結構載入時不一定重算；`save()` 前呼叫 `StructureBuilder.auto_connect()` 依鄰接補上，否則整排玻璃板會是孤立十字。柵欄沒有 state，不受影響。
17. 全域 Python 可能沒有 numpy/amulet_nbt；本專案 `work/active_mob_tower/vendor/` 有 Python 3.10 的預編譯套件，用 `PYTHONPATH=<vendor> py -3.10` 或在生成器裡 `sys.path.insert` 即可，不要對其他版本盲目編譯。

## 範例適用範圍

temple_example.py 是固定座標的可修改範例，不是任意尺寸參數化生成器。render_example.py 只適用該範例產生的 voxel/palette 檔案及標題；其他建築要調整標題、畫布與相機。花盆、鐘、告示等 block entity 的特殊內容需另外設定，範例不含告示文字。套件格式验证只能證明結構與容器一致，不能證明每版客戶端都正確顯示。
