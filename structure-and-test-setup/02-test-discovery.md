# 02 — 後端測試發現與實作（Test Discovery）

> 執行前先讀 `AGENT_REFERENCE.md`。
> 此步驟屬於**建立階段 Step 0 + Step 2**。
> Phase 1–5（最小 smoke test）是 Step 0 安全網，結構整理前先建好。
> Phase 6 之後的完整測試，結構穩定後才補。
>
> **建立階段目標：把測試建好且能被執行。不要求全綠，不要在這裡修 app bug。**

你是一位工程測試發現 agent。從檔案推斷技術棧，不要假設。

---

## 優先序

> 1) 可執行的 smoke test　>　2) P0 清單　>　3) 完整報告
> 文件可以簡略，但**實作出來的測試必須真的能跑**。

---

## 重要規則

- 不重寫 app、不大重構、不刪使用者檔
- 一律用暫存/測試 DB，絕不碰 production
- 來路不明的執行中 server → 只可唯讀 health/status，絕不寫入
- 記錄預期 port 與目前被占用的 port
- 有前端 build 就跑；有既有測試就跑
- 測行為/契約，不測實作細節
- 所有測試程式碼放 `test-script/`；DB script 放 `db-script/`
- 環境限制（裝不了依賴、port 被占）→ 記錄成 gap，降級手動 checklist，不卡死
- 每個聲稱存在的 endpoint/workflow 附來源檔案（最好附行號）

---

## Phase 1：專案盤點

掃 repo 分類（每項附來源檔案）：

```text
Project type: Backend only / Frontend only / Full-stack / Desktop / Mobile / CLI / Other
Backend:  exists / language+framework / entry point / start cmd / port(s) / API style
Frontend: exists / framework / entry / build cmd / dev cmd / port(s) / UI type
Database: exists / type / schema location / migration location / test DB 策略
Runtime:  exists / process names / ports / lifecycle 注意事項
```

---

## Phase 2：API / 動作面向發現

後端 API 表：

| Method | Path | Purpose | Reads DB | Writes DB | Calls external | Requires auth | Priority |
|--------|------|---------|----------|-----------|----------------|---------------|----------|

前端動作表（若有）：

| UI Area | Button/action | API called | Expected result | Failure mode |
|---------|--------------|------------|-----------------|--------------|

優先級：
- **P0**：app 啟動依賴 / 容易觸發 / 寫 DB 或檔案 / 啟停 process / 改 session 狀態 / 可能毀資料
- **P1**：重要但非破壞性
- **P2**：次要顯示動作

---

## Phase 3：使用者流程發現

關鍵流程（每個定義預期狀態與失敗狀態）：

- **Fresh start**：啟動 → health 載入 → 不需 production DB
- **Project/session**：建立 / 開啟 / 切換 / scoped 資料乾淨
- **Auth**：login / logout / 過期 token（若有）
- **CRUD**：建立 / 讀取 / 更新 / 刪除
- **Runtime**：discover / attach / start/stop managed（不殺外部 process）
- **Database**：fresh 遷移 / 舊 DB 遷移 / 缺表復原

---

## Phase 4：測試策略矩陣

- **Unit**：純邏輯（路徑正規化、驗證、parsing、狀態轉換、config 載入）
- **Integration**：模組合作（DB 遷移、handler+DB、session scoping、權限執行）
- **HTTP Smoke**：真實後端啟動（server 起來、health 200、fresh DB 有必要表、預期 disabled 狀態回受控錯誤、沒有端點 hang）
- **Manual QA Checklist**：無法自動化時——精確步驟 / 預期可見結果 / 常見失敗徵兆

---

## Phase 5：設計 Smoke Test（= Step 0 安全網）

建立最小一組，放 `test-script/`，DB script 放 `db-script/`：

1. **Fresh boot**：暫存 DB 啟動後端 → health 200 → 無缺表錯誤
2. **核心 create/open**：建 project/item/session → 讀回 → scoped 狀態乾淨
3. **Disabled 模式**：缺外部服務時回受控錯誤而非崩潰（若適用）
4. **資料隔離**：A 建資料、B 建資料 → B 看不到 A
5. **Runtime/process**：只停 managed process，不殺外部（若適用）

跑一次，記錄 baseline 到 `test-logs/`（綠或書面說明哪些原本就紅）。

**DB Script 範本（`db-script/reset_test_db.py`）：**
```python
#!/usr/bin/env python3
"""
通用測試 DB 重置 script。
使用：python db-script/reset_test_db.py --db /tmp/test_<timestamp>.db
"""
import argparse, os, subprocess, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="測試 DB 路徑")
    parser.add_argument("--schema", default=None, help="schema SQL 路徑（自動搜尋）")
    args = parser.parse_args()

    if os.path.exists(args.db):
        os.remove(args.db)
        print(f"Removed existing DB: {args.db}")

    # 自動搜尋 schema
    schema = args.schema
    if not schema:
        for candidate in ["core/db/schema.sql", "db/schema.sql", "schema.sql"]:
            if os.path.exists(candidate):
                schema = candidate
                break

    if schema:
        subprocess.run(["sqlite3", args.db, f".read {schema}"], check=True)
        print(f"Applied schema: {schema}")
    else:
        print("Warning: no schema found, created empty DB")

    print(f"Test DB ready: {args.db}")

if __name__ == "__main__":
    main()
```

---

## Phase 6：實作測試

先看現有測試風格，沿用既有工具：pytest / vitest|jest / `go test` / `cargo test` 等。

- Python 後端：測試放 `test-script/`，用暫存 DB，不寫死使用者路徑
- 多技術棧：各自用原生測試工具，不強求同一框架

**Pytest 暫存設定（Windows/WSL 安全）：**
```bash
python -m pytest test-script/ -q \
  --basetemp=structure-and-test-setup/test-logs/.pytest_tmp_$(date +%s) \
  -p no:cacheprovider
```

---

## Phase 7：Sequence 測試（P1，建立階段 best-effort）

針對「先 C 再 A」vs「先 B 再 C 再 A」的順序 bug，寫序列測試。
先做高風險序列，不窮舉所有排列。

若 API / 功能確認不存在，標 `N/A` 即可，**不阻塞建立階段完成**。

---

## Phase 8：報告

```text
Project classification: backend / frontend / database / runtime
Discovered API/actions: P0 / P1 / P2  （每項附來源檔案）
Critical workflows:
Tests implemented: - file / what it verifies
DB scripts: - file / what it does
Validation: compile / backend tests / frontend build / smoke baseline
Known gaps: 未自動化 / 需手動 QA / 風險 / N/A 項目
```

---

## 測試哲學

不問「每個端點都有 try/catch 嗎」。問：
這端點承諾什麼契約？fresh install 會怎樣？缺 DB 會怎樣？可選 runtime 不在時會怎樣？
使用者亂序點擊會怎樣？這會毀資料嗎？會 hang 嗎？會悄悄用錯 session 嗎？**測這些行為。**
