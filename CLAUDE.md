# Minecraft 建築

這是一個給 AI 產出 Minecraft 基岩版建築的資料夾。

## 規範

- 建築生成請使用本專案的 `minecraft-bedrock-structure` skill（位於 `.claude/skills/minecraft-bedrock-structure/`，原始碼同步在 `skills/`）。先寫 `work/<專案>/build_plan.md` 任務書再開工。
- 每個建築放在 `structures/<建築名稱>/`，內含 `.mcpack` 與繁體中文使用說明 `.txt`。
- 使用繁體中文與使用者溝通。
- 不要提交暫存或 db 檔案。

## 紅石機器

- 只要需求涉及紅石（紅石機器、機關、顯示器、計數器、農場、門、任何含中繼器／比較器／活塞／漏斗的設計），開工前必須先完整閱讀 `docs/紅石犯錯紀錄.md`，並依其中的檢查清單執行。
- 特別注意：玩家視角的左右（顯示器曾左右顛倒）、基岩版中繼器/比較器 `cardinal_direction` 指向輸入端、紅石粉斜向串線、以及先估算體積並壓縮線路。
- 新發現的紅石錯誤，完成工作時要補寫進 `docs/紅石犯錯紀錄.md`。

## Git 規則

- 每次完成一項工作後，必須完整提交並推送：`git add -A` → `git commit` → `git push`。
- 不可留下未提交的變更就結束工作；commit 訊息用繁體中文簡述做了什麼。
