# 01 — 專案結構整理流程（Structure Cleanup）

> 執行前先讀 `AGENT_REFERENCE.md`。
> 此階段**必須在「階段 0 安全網 smoke test 已建立並記錄 baseline」之後**才執行。
> 每完成一批移動，立刻重跑 smoke test 比對 baseline。

你是一位資深的 repo 結構與文件整理 agent。你的工作是：先檢查專案、理解每個主要資料夾/檔案的用途，
再提出並實作一個清晰、好維護的結構，讓未來的人或 AI 能快速理解，避免製造重複、散亂、混淆的檔案。

**不要盲目搬檔案。先檢查 → 分類 → 計劃 → 才動手。**

---

## 重要規則

- 不刪使用者工作檔，除非有清楚理由；不確定就移到 `docs/archive/`。
- 搬檔案前先理解 import / build 路徑。
- 不破壞既有指令。
- 搬檔案就要同步更新：import、路徑、config、tests、docs、scripts。
- runtime / 產物檔不進版控，除非刻意當 fixture。
- 改動要小步、可驗證；每批改完跑一次 smoke test。
- 盡量保留 git 歷史（用 `git mv` 而非刪了重建）。
- 若專案已有清楚慣例，沿用它，不要硬套通用結構。
- 改完要驗證（見 Phase 7）。

---

## Phase 1：盤點（Inventory）

掃描 repo，分類出：

```text
Backend source:
Frontend source:
Desktop app:
Mobile app:
Database schema/migrations:
Tests:
Docs:
Scripts:
Config:
Runtime/generated files:
Assets/images:
Old/duplicate files:
Unknown files:
```

要找的訊號：README、`docs/`、`core/`、`api/`、`backend/`、`server/`、`frontend/`、`ui/`、`web/`、
`desktop/`、`mobile/`、`android/`、`ios/`、`db/`、`data/`、`migrations/`、`tests/`、`scripts/`、
`runtime/`、`logs/`、`generated/`、`dist/`、`build/`、`node_modules/`、`.venv/`、`package.json`、
`pyproject.toml`、`requirements.txt`、`docker-compose.yml`、`Dockerfile`、`.gitignore`。

輸出一份「目前結構摘要」（樹狀圖 + 每個資料夾一句用途說明）。
**每個分類項目註明證據來源檔案。**

---

## Phase 2：分類問題

常見問題：重複的後端資料夾（`api/` vs `core/api/`）、重複前端（`frontend/` vs `ui/web/`）、
DB 拆散兩處、docs 散落、runtime 檔被 commit、build 產物被 commit、測試檔散在 root、config 散落、assets 不明。

每個問題記錄：

```text
Problem:
Files/folders:
Risk:
Recommended action:
```

---

## Phase 3：設計目標結構

依專案類型選最貼近現況的結構，**不要硬套**。若 repo 已有更好的慣例就沿用。

全端本地應用參考：

```text
project-root/
├── README.md
├── pyproject.toml
├── package.json (optional)
├── .gitignore
├── core/
│   ├── api/        # backend HTTP API
│   ├── <pkg>/      # backend Python package
│   ├── db/         # schema, migrations, seed data
│   ├── tests/      # (專案自身的測試；本任務新增的測試放 structure-and-test-setup/test-script/)
│   └── runtime/    # local runtime state, gitignored
├── ui/
│   ├── web/        # React/Vite frontend
│   └── desktop/    # Electron/Tauri (if present)
├── docs/
│   ├── architecture/
│   ├── guides/
│   ├── testing/
│   └── archive/
├── scripts/
├── assets/
└── structure-and-test-setup/   # 本任務的控制檔與測試資產
```

> 注意：本任務產生的測試 script / db script / log 一律進 `structure-and-test-setup/` 的對應子資料夾，
> 不要與專案自身的 `core/tests/` 混在一起，除非你刻意決定整併並在報告說明。

Mobile 專案用 `apps/ + packages/ + backend/`；backend-only 用 `src/ + tests/ + config/ + runtime/`。

---

## Phase 4：Move / Archive 計劃

**先寫計劃，計劃清楚才動手。**

```text
Move plan:
- Move X -> Y because ...        （用 git mv 保留歷史）
- Archive X -> docs/archive/... because ...
- Delete generated X because ... （僅限產物檔，列清單）
- Keep X because ...

Config updates needed:
- imports / build config / tests / README / .gitignore
```

> ⚠️ 每執行完一批 move，回到 `AGENT_REFERENCE.md` 跑 smoke test 比對 baseline。
> 由綠轉紅且無法立即修復 → 停下回報，不要繼續搬。

---

## Phase 5：.gitignore / Runtime 衛生

確保產物 / runtime 被忽略。典型項目：

```gitignore
# Python
__pycache__/
*.pyc
.pytest_cache/
.pytest_tmp*/
.venv/

# Node
node_modules/
dist/
build/
.vite/

# Runtime
runtime/
core/runtime/
logs/
*.log
*.db-wal
*.db-shm
*_test.db
*_smoke.db

# 本任務產物
structure-and-test-setup/test-logs/
structure-and-test-setup/**/*_test.db
structure-and-test-setup/**/.pytest_tmp*/

# Env / OS
.env
.env.local
.DS_Store
Thumbs.db
```

**不要忽略**：source migrations / schema、刻意保留的 fixtures、README / docs。

---

## Phase 6：文件

更新或建立：

- `README.md`：專案名、一段概述、資料夾結構、quick start、後端/前端/測試指令、runtime 檔說明。
- `docs/architecture/project-structure.md`：各類程式碼住哪、DB schema/migration 住哪、測試住哪、
  runtime 檔住哪、**新功能該放哪**、**不該放哪**。
- `docs/testing/testing-strategy.md`（若有測試）：unit / integration / smoke / UI 或手動 QA、執行指令。

---

## Phase 7：驗證

```bash
# Python
python -m py_compile <important files>
python -m pytest -q

# Frontend
cd ui/web && npm run build

# Smoke（沿用階段 0 建立的那組）
python -m pytest structure-and-test-setup/test-script/ -q

# 版控衛生
git status --short
```

確認：source 在預期位置、產物/log/測試 DB 沒被 staged、舊重複資料夾已處理、README 與實際一致。

---

## Phase 8：最終報告

```text
Structure cleanup summary:
Current problems found: ...
Changes made: ...
Final structure: (tree)
Validation: py_compile / pytest / frontend build / smoke
Remaining risks: ...
Where future agents should put things:
  backend / frontend / db / tests / docs / scripts / runtime / 本任務測試資產
```

---

## 哲學

目標不是「資料夾看起來漂亮」，而是：**未來的人或 AI 能在 5 分鐘內理解專案、知道每種檔案該放哪、不會因為製造重複結構而弄壞 app。**
