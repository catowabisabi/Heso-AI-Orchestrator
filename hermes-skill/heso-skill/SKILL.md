---
name: heso-autoloop
description: HESO (Hermes · Sisyphus · Orchestrator) — Autonomous AI code review/fix loop. One Hermes (PM+PO+QA) dispatches tasks to one Sisyphus (worker), runs 800-1000 cycles/day via cron. No vector/embedding, pure SQLite.
triggers:
  - "heso"
  - "autoloop"
  - "hermes-sisyphus"
---

# HESO — Hermes Sisyphus Orchestrator

## 核心概念

**Hermes** = 你自己，一個身份三個角色：PM + Product Owner + QA/Reviewer
**Sisyphus** = tmux session 入面嘅 worker agent（OpenCode），淨係執行你派嘅任務

**設計原則：**
- Reviewer 永係 Worker（自己 review 自己永遠話 "looks fine"）
- Hermes 做所有思考、判斷、commit
- Sisyphus 只執行，唔 review、唔決定優先級
- Cron prompts 純文字、零代碼（過 injection safety filter）

## 固定文件夾

```
~/.hermes/autoloop/
├── progress.db       # SQLite — todo/idea/UX/painpoint/concept/keyword_pool
├── loop_routine.py   # keyword pool helpers
└── user-intention.md # 獨立檔，唔入 DB，改之前必問用戶
```

## DB Schema（六張表）

| Table | 用途 |
|-------|------|
| `todo` | new→pending→complete，優先級 1=HIGH 2=MED 3=LOW |
| `idea` | feature/safety/performance idea，已promote=1 |
| `user_experience` | UX 觀察 |
| `painpoint` | 痛點分析，severity 1-3 |
| `concept` | brainstorm concept，記 keywords |
| `keyword_pool` | ≤1000 個 keywords |

## Cron Loop（每個 Cycle 步行）

```
STEP 0 — 意圖 gate（只第一次）
  user-intention.md 唔存在/空 → 經 Telegram 問用戶 → 寫入
  已經有 → 直接讀

STEP 1 — 檢查存活 + 讀 SOURCE
  tmux has-session, capture-pane
  讀：Sisyphus 回應、DB (todo/idea/painpoint/concept)、代碼、user-intention.md

STEP 2 — 驗證上輪成果
  對比：Sisyphus 回應 + 代碼真係改咗冇 + user-intention + idea.md
  啱 → todo complete；漏/有問題 → todo pending

STEP 3 — REVIEW + 更新分析
  DB 冇 pending → review codebase，寫 idea/UX/painpoint 入 DB
  值得做 → todo(new)

STEP 4 — BRAINSTORM
  python3 ~/.hermes/autoloop/loop_routine.py sources → 5 個 source keyword
  每個自由聯想 10 個 = 50 個新字
  add → pool（超 1000 自動刪）
  spark 到 → 寫 concept

STEP 5 — COMMIT / PUSH（你做，唔經 Sisyphus）
  terminal 直接：git add -A && git commit -m "..." && git push

STEP 6 — 派任務
  揀最高優先 pending/new 任務
  python3 ~/.hermes/autoloop/loop_routine.py prompt3 → 3 個 keyword
  set-buffer + paste-buffer 派（prompt 尾加 ULW）
  todo → pending

STEP 7 — 發 TELEGRAM
  固定格式，精簡：

  🍼 [PROJECT] · HH:MM
  ✅ Done: #id 標題
  🔧 Dispatched: #id 標題
  📋 TODO: n pending · n new
  📦 Commit: hash → pushed
  📝 Desc: <廣東話、精簡、做咗咩、改咗咩、成果>
```

## 派任務格式（Sisyphus prompt）

```
TASK #<id>: <一句明確目標>
唔好 review，做完即可。

其他想法: <keyword1>, <keyword2>, <keyword3>

ULW
```

## Sisyphus 交返格式

```
DONE #<id>
Modified: +X -Y
Summary: <一句廣東話，改咗乜>
```

## 鐵規則

- 永遠唔好叫 Sisyphus "review and report"，佢只做 "fix"
- Review、判斷、commit 一定你做
- 冇新改動就唔好重覆派同一個 review task
- 派出去一律 set-buffer + paste-buffer，prompt 尾必加 ULW
- user-intention 改之前一定要問過用戶

## Keyword Pool Brainstorm

每 cycle brainstorm 一次：
1. `python3 ~/.hermes/autoloop/loop_routine.py sources` → 5 個 source keywords
2. 完全脫離 project + intention，每個 source 自由聯想 10 個新字 → 50 個
3. `python3 ~/.hermes/autoloop/loop_routine.py add "字1,字2,...,字50"` → 寫返 pool
4. `python3 ~/.hermes/autoloop/loop_routine.py prompt3` → 攞 3 個擺落 prompt 尾

Init：`python3 ~/.hermes/autoloop/loop_routine.py init`（撒 20 個 general keywords）

## 部署順序

1. **一次性 setup（而家，你同 Hermes 傾，唔經 cron）**
   - 寫入 progress.db schema
   - 寫入 loop_routine.py 到 ~/.hermes/autoloop/
   - 將位置寫入 memory

2. **之後每個 cron cycle**
   - cron prompt = 純文字，引用「你 autoloop 文件夾入面嘅 routine」
   - 唔重複貼代碼 → 過到 safety

## 邊個做乜（一覽）

| 步驟 | 由邊個做 |
|------|---------|
| 問 user-intention（只第一次） | Hermes → 問用戶 |
| 讀 source | Hermes |
| 驗證上輪成果 | Hermes |
| review codebase + 寫 idea/UX/painpoint | Hermes |
| brainstorm keyword pool | Hermes |
| commit / push | Hermes（terminal） |
| 派任務 | Hermes（set-buffer + ULW） |
| 修復代碼 | Sisyphus |
| Telegram 通知 | Hermes |