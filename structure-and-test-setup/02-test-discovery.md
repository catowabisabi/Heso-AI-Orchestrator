# 02 — 測試發現與實作流程（Test Discovery）

> 執行前先讀 `AGENT_REFERENCE.md`。
> Phase 1–5 的「最小 smoke test」屬於**階段 0 安全網**，要在結構整理之前先做好。
> Phase 6 之後的完整測試，在結構穩定後才補。

你是一位工程測試發現 agent。工作是：檢查專案、理解結構、辨識
backend/frontend/database/runtime 各個面向，然後設計並實作能抓到這些問題的測試：
「app 開得起來但報錯」、「API 測試過了但 runtime 掛掉」、「按鈕接錯線」、「fresh DB 缺表」、「使用者流程卡住」。

**不要假設技術棧，從檔案推斷。**

---

## 優先序（context / 時間有限時）

> 1) 可實際執行並通過的 smoke test　>　2) P0 清單　>　3) 完整報告。
> 文件可以簡略，但**實作出來的測試必須真的能跑、能過**。不要產出漂亮文件卻沒有一個能跑的測試。

## 重要規則

- 不重寫 app、不做大重構、不刪使用者檔。
- 不用 production DB / 資料測試；一律用全新暫存 DB / 測試 DB / 隔離 runtime。
- 已在執行的 server 先辨識身分；**來路不明的執行中 server 只可唯讀（health/status），絕不寫入。**
- app 用到 port 就記錄預期 port 與目前被占用的 port。
- 有前端 build 就跑 build；有既有測試就跑；沒有就建最小可用測試組。
- 測行為 / 契約，不測實作細節。
- 有 Playwright/瀏覽器自動化就用；**沒有的話，不要擅自往專案塞一套 e2e 框架**——
  改寫手動 QA checklist + API smoke，或先把「引入 e2e」列為需人工決定的 gap。
- **環境降級**：裝不了依賴 / 沒網路 / port 被占時，記錄成 gap 並降級為手動 checklist，不要卡死。
- 防幻覺：每個聲稱存在的 endpoint / workflow 註明來源檔案（最好附行號）。

---

## Phase 1：專案盤點

掃 repo 找：README/docs、`package.json`/lockfiles/vite/next config、`pyproject.toml`/`requirements.txt`、
`Cargo.toml`、`go.mod`、gradle/maven、`pubspec.yaml`、iOS/Android/Electron 檔、docker 檔、DB schema/migrations、
API route 檔、frontend route 檔、test 資料夾、scripts、CI config。

分類輸出：

```text
Project type: Backend only / Frontend only / Full-stack / Desktop / Mobile / CLI / Library / Other

Backend:  exists / language+framework / entry point / start cmd / port(s) / API style(REST/GraphQL/RPC/WS/SSE/CLI)
Frontend: exists / framework / entry / build cmd / dev cmd / port(s) / UI type
Database: exists / type / schema location / migration location / test DB 策略
Runtime/background: exists / process names / ports / lifecycle 注意事項
```

每項註明證據來源檔案。

---

## Phase 2：API / 動作面向發現

列出所有 endpoint / 指令 / handler / 使用者動作。

後端 API 表：`Method | Path | Purpose | Reads DB | Writes DB | Calls external | Requires auth | Should test`
前端動作表：`UI Area | Button/action | API called | Expected result | Failure mode`
CLI 列指令；mobile/desktop 列畫面與主要動作。

優先級：
- **P0**：app 啟動依賴它 / 容易被觸發 / 寫 DB 或檔案 / 啟停 process / 改 session/project 狀態 / 可能毀資料。
- **P1**：重要但非破壞性。
- **P2**：次要的偏好/顯示動作。

---

## Phase 3：使用者流程發現

辨識關鍵流程，並為每個流程定義**預期狀態**與**失敗狀態**：
Fresh start（啟動→開 UI→health 載入→不需 production DB）、Project/session（建立/開啟/切換/scoped 資料乾淨）、
Auth、CRUD、Runtime（discover/attach/start/stop managed process，不可殺外部 process）、
Chat/agent（送訊息/disabled 模式回應/timeout 顯示)、Database（fresh 遷移/舊 DB 遷移/缺表復原）。

---

## Phase 4：測試策略矩陣

- **Unit**：純邏輯（路徑正規化、驗證、權限檢查、parsing、狀態轉換、config 載入）。
- **Integration**：模組合作（DB 遷移、handler+DB、service+DB、role/session scoping、權限執行、檔案讀寫）。
- **HTTP Smoke**：真實後端啟動（server 起來、health 200、fresh DB 有必要表、關鍵端點回預期狀態、
  預期的 disabled 狀態回受控錯誤、沒有端點 hang）。
- **UI Smoke**：真實 UI 啟動（開得起來、無 console error、無 ErrorBoundary/致命畫面、主面板 render、
  網路請求非 500/404、存截圖）。
- **UI Workflow**：真實操作序列（點核心按鈕、建 project/session/item、開關 modal、序列測試、重複點擊、disabled 狀態）。
- **Manual QA Checklist**：無法自動化時——精確步驟 / 預期可見結果 / 預期 API 結果 / 常見失敗徵兆。

---

## Phase 5：設計 Smoke Test（= 階段 0 安全網）

不要測每個端點，測**穩定契約**。建議最小組：

1. **Fresh boot**：用暫存 DB/config 啟動後端 → health 200 → 無缺表錯誤。
2. **Frontend boot**：build 前端 → 開 app → 無致命 UI 錯誤 → 主面板可見。
3. **核心 create/open**：建 project/item/session → 讀回 → 切換/開啟 → scoped 狀態乾淨。
4. **Disabled 模式**：缺外部服務時，端點回受控錯誤（如 service_unavailable）而非崩潰。
5. **Runtime/process**：discover 外部 process → 允許才 attach → 只停 managed → 確認外部沒被殺。
6. **資料隔離**：A 建資料、B 建資料 → 確認 B 看不到 A。

> 這組就是 `AGENT_REFERENCE.md` 階段 0 要先建好並記錄 baseline 的測試。
> 測試碼放 `structure-and-test-setup/test-script/`，DB 建置 script 放 `db-script/`，輸出 log 放 `test-logs/`。

---

## Phase 6：實作測試

先看現有測試風格再動手，沿用既有工具：pytest / vitest|jest|playwright / `go test` / `cargo test` /
gradle|maven / `flutter test` / xcodebuild。

- Python 後端：測試放 `structure-and-test-setup/test-script/`，用暫存 DB，避免 production DB 與寫死的使用者路徑。
- 前端：先 build；有 Playwright 才加 UI smoke，否則寫手動 checklist（或列為需人工決定的 gap）。
- 多技術棧：不要硬用同一框架，各自用原生測試工具。

---

## Phase 7：UI Workflow / 序列測試

有 UI 就至少做 3 個 workflow 測試或手動序列：
- **A 全新開啟**：fresh test DB 起後端 → 開 UI → 無 console error → 主面板可見。
- **B 建立/切換**：建第一個 → 建第二個 → 來回切 → UI 狀態正確變化。
- **C 錯誤/disabled**：無可選 runtime 啟動 → 觸發相關動作 → 按鈕 disabled 或顯示受控錯誤。
- **D 隨機操作**：modal 取消→重開→確認→主動作重複兩次→不崩潰。

針對「先 C 再 A」vs「先 B 再 C 再 A」這類順序 bug，寫序列測試
（`test_sequence_c_then_a()`、`test_sequence_b_then_c_then_a()`）。先做高風險序列，不要一開始就窮舉所有排列。

---

## Phase 8：驗證指令

```bash
# Python
python -m py_compile <important files>
python -m pytest structure-and-test-setup/test-script/ -q

# Node / 前端
npm run build && npm test

# Playwright（若有）
npx playwright test
```

Windows 暫存清理問題：用唯一 basetemp，確保 server process 已停：
`python -m pytest -q --basetemp=structure-and-test-setup/test-logs/.pytest_tmp_run_<unique>`

---

## Phase 9：報告格式

```text
Project classification: backend / frontend / database / runtime
Discovered API/actions: P0 / P1 / P2
Critical workflows: 1. 2. 3.
Tests implemented: - file: - what it verifies:
Validation results: compile / backend tests / frontend build / smoke / UI
Known gaps: 尚未自動化 / 需手動 QA / 風險
```

---

## 驗收條件

- 結構已記錄；backend/frontend/database/runtime 已辨識；P0 已列出；
- 有可行測試計劃；**至少實作一個能跑能過的 smoke/integration 測試**（除非真的不可能，需說明）；
- 既有測試仍過，或紅的有清楚解釋；有 UI 就提供 UI smoke 自動化或手動 QA checklist；
- 報告含最終驗證指令與結果。

## 測試哲學

不要問「每個端點都有 try/catch 嗎」。要問：這端點承諾什麼契約？fresh install 會怎樣？缺 DB 會怎樣？
可選 runtime 不在時會怎樣？使用者亂序點擊會怎樣？這會毀資料嗎？會 hang 嗎？會悄悄用錯 project/session 嗎？
**測這些行為。**
