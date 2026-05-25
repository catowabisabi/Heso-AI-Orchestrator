# 01 — 專案結構整理（Structure Cleanup）

> 執行前先讀 `AGENT_REFERENCE.md`。
> 此步驟屬於**建立階段 Step 1**，在 Step 0 smoke test baseline 記錄完成後才執行。
> 每完成一批移動，立刻重跑 smoke test 比對 baseline。

你是一位資深 repo 結構與文件整理 agent。先檢查 → 分類 → 計劃 → 才動手。**不要盲目搬檔案。**

---

## 重要規則

- 不刪使用者工作檔；不確定就移到 `docs/archive/`
- 搬檔案前先理解 import / build 路徑；搬了就同步更新 import、config、tests、docs、scripts
- 不破壞既有指令
- 用 `git mv` 保留歷史，不要刪了重建
- Runtime / 產物檔不進版控（除非刻意當 fixture）
- 改動小步、可驗證；每批改完跑 smoke test
- 若專案已有清楚慣例，沿用它，不要硬套通用結構
- `structure-and-test-setup/` 資料夾本身**不搬、不改名**

---

## Phase 1：盤點（Inventory）

掃描 repo，分類輸出（**每項附來源檔案**）：

```text
Backend source:
Frontend source:
Desktop / Mobile app:
Database schema / migrations:
Tests:
Docs:
Scripts:
Config:
Runtime / generated files:
Assets:
Old / duplicate files:
Unknown files:
```

輸出樹狀圖 + 每個資料夾一句用途說明。

---

## Phase 2：分類問題

常見問題：重複後端資料夾、重複前端資料夾、DB 拆散兩處、docs 散落、runtime 被 commit、build 產物被 commit、測試散在 root、config 散落。

每個問題記錄：

```text
Problem:
Files/folders:
Risk:
Recommended action:
```

---

## Phase 3：設計目標結構

依專案類型選最貼近現況的結構，**不要硬套**。若 repo 已有更好慣例就沿用。

全端本地應用參考：

```text
project-root/
├── README.md
├── pyproject.toml / package.json
├── .gitignore
├── core/
│   ├── api/          # backend HTTP API
│   ├── <pkg>/        # backend Python package
│   ├── db/           # schema, migrations, seed data
│   ├── tests/        # 專案自身測試
│   └── runtime/      # gitignored
├── ui/
│   ├── web/
│   └── desktop/
├── docs/
│   ├── architecture/
│   ├── guides/
│   ├── testing/
│   └── archive/
├── scripts/
├── assets/
└── structure-and-test-setup/   # 本任務控制檔（不搬）
```

> 本任務的測試 script / db script / UI spec / log 一律進 `structure-and-test-setup/` 對應子資料夾，
> 不與專案自身的 `core/tests/` 混在一起，除非刻意整併並在報告說明。

---

## Phase 4：Move / Archive 計劃

**先寫計劃，計劃清楚才動手。**

```text
Move plan:
- Move X -> Y because ...          （git mv）
- Archive X -> docs/archive/ because ...
- Delete generated X because ...   （僅產物檔，列清單）
- Keep X because ...

Config updates needed:
- imports / build config / tests / README / .gitignore
```

> ⚠️ 每批 move 完成後立刻重跑 smoke test。由綠轉紅且無法立即修復 → 停下回報，不繼續搬。

---

## Phase 5：.gitignore 衛生

```gitignore
# Python
__pycache__/
*.pyc
.pytest_cache/
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
structure-and-test-setup/test-logs/test-screen/
structure-and-test-setup/**/*_test.db
structure-and-test-setup/**/.pytest_tmp*/
structure-and-test-setup/test-ui/test-results/
structure-and-test-setup/test-ui/playwright-report/

# Env / OS
.env
.env.local
.DS_Store
Thumbs.db
```

**不要忽略**：source migrations/schema、刻意保留的 fixtures、README/docs。

---

## Phase 6：文件更新

- **`README.md`**：專案名、概述、資料夾結構、quick start、後端/前端/測試指令、runtime 檔說明。
- **`docs/architecture/project-structure.md`**：各類程式碼住哪、DB 住哪、測試住哪、新功能該放哪、不該放哪。
- **`docs/testing/testing-strategy.md`**：unit/integration/smoke/UI 測試說明與執行指令。

---

## Phase 7：驗證

```bash
python -m py_compile <important files>
python -m pytest test-script/ -q
cd ui/web && npm run build    # 若有前端
git status --short
```

---

## Phase 8：報告

```text
Structure cleanup summary:
Current problems found:
Changes made:
Final structure: (tree)
Validation: py_compile / pytest / frontend build / smoke
Remaining risks:
Where future agents should put things:
  backend / frontend / db / tests / docs / scripts / runtime / 本任務測試資產
```
