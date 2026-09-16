# Minecraft 建築

這是一個給 AI 產出 Minecraft 基岩版建築的資料夾。

## 規範

- 建築生成請使用 `anthropic-skills:minecraft-bedrock-structure` skill。
- 每個建築放在 `structures/<建築名稱>/`，內含 `.mcpack` 與繁體中文使用說明 `.txt`。
- 使用繁體中文與使用者溝通。
- 不要提交暫存或 db 檔案。

## Git 規則

- 每次完成一項工作後，必須完整提交並推送：`git add -A` → `git commit` → `git push`。
- 不可留下未提交的變更就結束工作；commit 訊息用繁體中文簡述做了什麼。
