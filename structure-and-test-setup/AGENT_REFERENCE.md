# AGENT REFERENCE — 每次工作前必須先讀這份

> 你在這個專案做任何「結構整理」或「測試」相關工作前，**必須先讀這份文件**。
> 這是總控制文件，`01`/`02`/`03` 是執行細節。

---

## 0. 資料夾結構與歸位規則

```
structure-and-test-setup/
├── AGENT_REFERENCE.md              ← 你正在讀的（總入口）
├── 01-structure-cleanup.md         ← 建立階段 Step 1：結構整理
├── 02-test-discovery.md            ← 建立階段 Step 2：後端/整合測試
├── 03-ui-auto-explore.md           ← 建立階段 Step 3：UI 自動探索測試
├── test-script/                    ← 後端/整合測試程式碼
├── db-script/                      ← 建立/重置測試 DB 的 script
├── test-ui/                        ← Playwright spec 與 config
└── test-logs/
    ├── test-screen/
    │   └── <YYYY-MM-DD>/           ← 每日截圖
    ├── iteration-<N>-summary.md    ← 每輪 loop 的進度報告
    └── .pytest_tmp*/               ← pytest 暫存（gitignored）
```

**硬規則（違反即錯）：**
- 後端/整合測試程式碼 → `test-script/`
- DB 建立/重置 script → `db-script/`
- Playwright spec / config → `test-ui/`
- 截圖/影片 → `test-logs/test-screen/<YYYY-MM-DD>/`
- 每輪 loop 報告 → `test-logs/iteration-<N>-summary.md`
- 測試 DB、log、暫存檔 → **不進 repo source 目錄、不 commit**

---

## 1. 兩階段設計（核心概念）

### 建立階段（Setup Phase）— 不 loop，一次備齊

**目標：把該建的都建好，且能被執行。不要求全綠，只要求跑得起來。**

執行順序（不可更改）：

```
Step 0 — 先建安全網 smoke test（最小一組能跑的）
         ↓ 記錄 baseline 到 test-logs/
Step 1 — 依 01-structure-cleanup.md 整理結構
         ↓ 每批移動後重跑 smoke test 比對 baseline
Step 2 — 依 02-test-discovery.md 後段補完整後端/整合測試
         ↓ 確認所有 test-script/ 裡的測試可執行
Step 3 — 依 03-ui-auto-explore.md 建立 UI 探索測試
         ↓ 安裝 Playwright（找不到就裝）、建好 spec、確認能啟動
```

**建立階段退出條件（ALL 成立才進入 loop）：**
- [ ] Smoke test baseline 已記錄（綠或有書面說明哪些原本就紅）
- [ ] `test-script/` 裡有至少一個可執行的後端 smoke test
- [ ] `db-script/` 裡有建立/重置測試 DB 的 script
- [ ] `test-ui/` 裡有 Playwright spec，且 `npx playwright test --list` 能列出 test
- [ ] 截圖輸出設定指向 `test-logs/test-screen/<YYYY-MM-DD>/`
- [ ] 測試 DB 與 production DB 完全隔離，不碰生產資料

> ⚠️ 建立階段如果 test 跑起來有紅燈，**記錄下來但繼續建其餘的**。
> 不要在建立階段就開始修 app bug——那是 loop 階段的工作。

---

### Loop 階段（Run-to-Green Phase）— 反覆跑到全綠

**目標：反覆執行全部測試，依下面的分級修到「全綠」定義達成為止。**

#### 每一輪（iteration）必須做：
1. 執行後端測試：`python -m pytest test-script/ -q --basetemp=test-logs/.pytest_tmp_<timestamp>`
2. 執行 UI 探索測試：`cd test-ui && npx playwright test`
3. 確認截圖已存到 `test-logs/test-screen/<今日日期>/`
4. 執行 `git status --short`，確認 log/截圖/測試 DB 沒被誤 stage
5. 對照完成條件逐項勾選
6. 寫 `test-logs/iteration-<N>-summary.md`（這輪做了什麼、哪些已達成、哪些還沒、下一輪計劃）

#### 測試分級（決定什麼是「紅」什麼是「可接受」）：

**致命級 — 必須修到綠，會擋 loop 完成：**
- App 開不起來
- 白屏 / ErrorBoundary / 未捕捉 JS exception
- 核心啟動端點回 404 / 500
- 點擊任何 UI 元素導致整個 hang（超過設定 timeout）
- 後端 smoke test 失敗
- 資料隔離被破壞（B session 看到 A 的資料）

**警告級 — 記錄到 log，不擋 loop 完成：**
- Console warning（非 error）
- 預期內的受控錯誤（如 disabled 模式回的 503）
- 非核心端點的雜訊
- 探索式填表引發的 validation error（預期行為）

#### Loop 完成條件（ALL 成立才停止）：
- [ ] 所有後端 smoke / integration test 通過
- [ ] UI 探索掃描無致命級問題
- [ ] 所有警告級問題已記錄在最新 iteration summary
- [ ] 所有 P0 端點有對應測試且通過
- [ ] `README` 與 `docs/architecture/project-structure.md` 反映真實結構
- [ ] `git status` 乾淨：source 在預期位置，產物/log/測試 DB 未被 staged

#### 強制停止條件（達到任一就停，輸出「卡住報告」）：
- **最大迭代次數 = 8**
- **連續 2 輪沒有進展**（致命級問題數量沒減少）
- **任何破壞性動作不確定**（見第 3 節）

> 不要為了讓 loop 看起來完成而刪測試、放寬斷言、或把紅的標 skip。
> 寧可如實回報未完成，也不要假裝完成。

---

## 2. Windows / WSL 注意事項

- 測試 DB 與暫存目錄明確指定在**單一檔案系統**，不跨 `/mnt/c/`
- pytest 暫存：`--basetemp=test-logs/.pytest_tmp_<timestamp>`
- 跑完測試確保所有起來的 server process 已關閉
- Playwright 在 WSL 下若遇到 browser 路徑問題，先嘗試 `npx playwright install --with-deps`

---

## 3. 安全規則

- **絕不刪使用者工作檔**。不確定就移到 `docs/archive/`。
- **只刪 generated/產物檔**，且要在報告列出刪了什麼。
- **來路不明的執行中 server → 只可打唯讀 health/status，絕不寫入。**
- 測試一律用全新暫存 DB，絕不碰 production 資料。
- 移動任何檔案前確認 import/build 路徑會一起更新；不確定就不搬。
- 環境限制（裝不了依賴、沒網路、port 被占）→ 記錄成 gap，降級成手動 checklist。
- **絕不擅自往專案塞大型 framework**（如 e2e 框架），除非 `03` 明確指示。

---

## 4. 防幻覺規則

- 每個聲稱存在的 endpoint / workflow / 檔案，**必須附來源檔案（最好附行號）**。
- 找不到證據就寫「未確認」，不要編造。
- 不確定的結構決定列入報告「需人工決定」區，不要自己拍板。
