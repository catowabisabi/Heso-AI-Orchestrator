# AGENT REFERENCE — 每次工作前先讀這份

> 你（AI agent）在這個專案做任何「結構整理」或「測試」相關工作前，**必須先讀這份文件**，
> 然後依照下面指定的順序與規則執行。這份是總控制文件；另外兩份是執行細節。

---

## 0. 這個資料夾是什麼

```
structure-and-test-setup/
├── AGENT_REFERENCE.md        ← 你正在讀的這份（總入口 / loop 控制 / 規則）
├── 01-structure-cleanup.md   ← 階段一：檔案結構整理流程
├── 02-test-discovery.md      ← 階段二：測試發現與實作流程
├── test-script/              ← 所有測試程式碼放這裡
├── db-script/                ← 所有「建立 / 重置測試 DB」的 script 放這裡
└── test-logs/                ← 每次跑測試的輸出 log 放這裡（檔名帶時間戳）
```

**檔案歸位硬規則（違反就是錯）：**
- 測試程式碼 → 一律放 `structure-and-test-setup/test-script/`，不要散在 repo 各處。
- 建立或重置測試資料庫的 script → 一律放 `structure-and-test-setup/db-script/`。
- 測試輸出 / log → 一律寫到 `structure-and-test-setup/test-logs/`，檔名格式 `YYYYMMDD-HHMMSS-<描述>.log`。
- 不要把測試 DB、log、暫存檔放進 repo 的 source 目錄。

---

## 1. 執行順序（不可更改）

> ⚠️ 重要：**先建安全網，再重構，最後補完整測試。**
> 不要在沒有任何測試的情況下先大改檔案結構——那等於沒有護欄就拆承重牆。

1. **階段 0｜建立安全網（最小 smoke test）**
   - 在動任何檔案結構之前，先依 `02-test-discovery.md` 的 Phase 1–2，
     建立**最小一組能跑起來的 smoke test**（後端能啟動 / health 端點 200 / fresh DB 有必要的表 / 前端能 build）。
   - 把這組 smoke test 跑一次，記錄 baseline 結果到 `test-logs/`。
   - **這組 baseline 必須全綠，或你必須明確記錄哪些原本就紅、為什麼。** 重構後要拿這個 baseline 來比對。

2. **階段 1｜結構整理**
   - 依 `01-structure-cleanup.md` 執行。
   - **每完成一批移動 / 改 import / 改 config 後，立刻重跑階段 0 的 smoke test**，確認沒有把東西改壞。
   - 任何一步讓 baseline 由綠轉紅且你無法立即修好 → **停下來，回報，不要繼續搬**。

3. **階段 2｜完整測試**
   - 結構穩定、smoke test 仍綠之後，再依 `02-test-discovery.md` 的後段補上
     整合測試、workflow / sequence 測試、或手動 QA checklist。

4. **階段 3｜更新文件**
   - 更新 `README`、`docs/architecture/project-structure.md`、`docs/testing/testing-strategy.md`。
   - 確認文件描述的結構與實際 repo 一致。

---

## 2. Loop 行為與退出條件（關鍵）

你會被要求「重複執行直到完成」。**「完成」不是由你主觀判斷，而是由下面的客觀條件決定。**

### 每一輪（iteration）你必須做：
1. 跑一次完整 smoke test，輸出寫到 `test-logs/`。
2. 跑 `git status --short`，確認沒有把 log / 測試 DB / build 產物誤加進版控。
3. 對照下面的「完成條件」逐項打勾。
4. 在 `test-logs/` 寫一份該輪的 `iteration-<N>-summary.md`，內容包含：這輪做了什麼、哪些條件已達成、哪些還沒、下一輪打算做什麼。

### 完成條件（ALL 必須同時成立才算完成，停止 loop）：
- [ ] smoke test 全部通過（或紅的項目有明確、書面的理由，且不是因為這次改動造成）。
- [ ] 結構整理的 move plan 全部執行完，或剩下的項目已明確標為「需人工決定」。
- [ ] 所有 P0 端點 / 動作都有對應測試，且通過。
- [ ] `README` 與 `docs/architecture/project-structure.md` 反映真實結構。
- [ ] `git status` 乾淨：source 在預期位置、產物 / log / 測試 DB 沒被 staged。
- [ ] 既有測試仍通過，或紅的項目有書面說明。

### 強制停止條件（達到任一就停，不要再 loop）：
- **最大迭代次數 = 8**。到第 8 輪仍未滿足完成條件 → 停止，輸出一份「卡住報告」說明還差什麼、為什麼、你建議人工怎麼介入。
- **連續 2 輪沒有進展**（達成的條件數量沒增加）→ 停止並回報，不要原地打轉。
- **任何破壞性動作的不確定**（見第 3 節）→ 停止並詢問。

> 不要為了「讓 loop 看起來完成」而刪測試、放寬斷言、或把紅的測試標 skip。
> 寧可如實回報未完成，也不要假裝完成。

---

## 3. 安全 / 破壞性動作規則

- **絕不刪除使用者的工作檔**。不確定就移到 `docs/archive/` 而不是刪除。
- **只刪 generated / 產物檔**（build 輸出、`__pycache__`、暫存 DB、log），且要在報告裡列出刪了什麼。
- **絕不對「已經在執行中、來路不明的 server」做寫入操作**。只可以打唯讀的 health / status 端點。
  測試一律用全新的暫存 DB / 測試 DB，絕不碰 production 資料。
- 移動任何檔案前，先確認它的 import / build 路徑會被一起更新；不確定就先別搬。
- 環境限制（如裝不了依賴、沒網路、port 被占）→ **記錄成 gap，降級成手動 checklist**，不要卡死，也不要擅自大改專案（例如硬塞一套新的 e2e 框架）。

---

## 4. Windows / WSL 注意事項

此專案在 Windows + WSL 混合環境下運作，請特別注意：
- 測試 DB 與暫存目錄要明確指定在**單一檔案系統**上（不要跨 `/mnt/c/`），避免鎖定與效能問題。
- pytest 暫存若在 Windows 上清理失敗，使用唯一 basetemp，例如：
  `python -m pytest -q --basetemp=structure-and-test-setup/test-logs/.pytest_tmp_<unique>`
- 跑完測試確保所有起來的 server process 都已關閉，避免目錄被鎖。

---

## 5. 防幻覺規則

- 你聲稱存在的每一個 endpoint / workflow / 檔案，**必須註明是從哪個檔案（最好附行號）推斷出來的**。
- 找不到證據就寫「未確認」，不要編造。
- 不確定的結構決定，列入報告的「需人工決定」區，不要自己拍板搬動。
