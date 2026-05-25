# 03 — UI 自動探索測試（UI Auto-Explore）

> 執行前先讀 `AGENT_REFERENCE.md`。
> 此步驟屬於**建立階段 Step 3**：把 UI 測試建好、能被執行。
> **建立階段不要求全綠，不要在這裡修 app bug。**
> Loop 階段才負責跑到全綠。

你是一位 UI 自動探索測試 agent。你的工作是：
1. 找到或安裝 Playwright
2. 探索 UI 上的每個可互動元素——自己推斷該輸入什麼、填了、操作
3. 全程監看 console + network（F12 等效），抓 error 並分級記錄
4. 偵測卡死（hang / timeout）
5. 把截圖按日期存好

**不要重設計 UI。不要重構 component，除非是讓測試能跑的最小修改。**

---

## 致命 vs 警告 分級（Loop 階段決定「紅燈」的標準）

**致命級（必須修到綠）：**
- App 開不起來 / 白屏 / ErrorBoundary / 未捕捉 JS exception
- 核心啟動端點（health、初始資料載入）回 404 / 500
- 點擊任何 UI 元素導致 hang（超過 `ACTION_TIMEOUT`）
- Page crash / renderer process 死掉

**警告級（記錄到 log，不擋完成）：**
- Console warning（非 error）
- 預期內的受控錯誤（如 disabled 模式、validation error）
- 探索式填表引發的業務邏輯錯誤（填了奇怪資料被 reject，這是預期的）
- 非核心端點的雜訊

---

## Phase 1：發現專案設定

**在寫任何測試前，先填滿這張表。每格附來源檔案（最好附行號）。填不出來標 `未確認`，不准猜。**

```text
Frontend framework:         （React / Vue / Svelte / Angular / 其他）
Frontend source path:
Build command:
Dev / static serve command:
Backend start command:
Backend health endpoint:    （用來輪詢確認 ready）
Test DB strategy:           （暫存 DB 路徑 / 環境變數名稱）
Disabled / degraded mode:   （是否有 --no-xxx flag 或類似機制）
Core panels / pages:        （app 載入後預期可見的主要區塊，從 route/component 推斷）
External services:          （是否有外部 process / socket 概念，port 是多少）
Existing UI test framework: （Playwright / Cypress / 無）
Playwright config path:     （若已存在）
```

---

## Phase 2：安裝 / 確認 Playwright

```bash
# 1. 檢查是否已安裝
npx playwright --version 2>/dev/null && echo "found" || echo "not found"

# 2. 若不存在，在前端目錄安裝
cd <frontend_path>
npm install --save-dev @playwright/test
npx playwright install --with-deps chromium

# 3. WSL 下若遇到 browser 路徑問題
npx playwright install --with-deps
```

建立或確認 Playwright config，**截圖 / 影片輸出必須指向：**
`structure-and-test-setup/test-logs/test-screen/<YYYY-MM-DD>/`

```typescript
// test-ui/playwright.config.ts
import { defineConfig } from '@playwright/test';
import { format } from 'date-fns';  // 或用 new Date() 自己格式化

const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD

export default defineConfig({
  testDir: './test-ui',
  timeout: 30_000,
  use: {
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    outputDir: `../structure-and-test-setup/test-logs/test-screen/${today}`,
  },
  reporter: [
    ['list'],
    ['json', { outputFile: `../structure-and-test-setup/test-logs/test-screen/${today}/report.json` }],
  ],
});
```

---

## Phase 3：測試環境設定

**強制隔離規則（任何情況都不例外）：**
- 用全新暫存測試 DB（每次跑前重置，用 `db-script/reset_test_db.py`）
- 後端跑在獨立測試 port（動態選擇，不寫死）
- 跑完後停掉所有由測試啟動的 process

**動態 port 選擇：**
```typescript
import * as net from 'net';

async function getFreePort(): Promise<number> {
  return new Promise((resolve) => {
    const srv = net.createServer();
    srv.listen(0, () => {
      const port = (srv.address() as net.AddressInfo).port;
      srv.close(() => resolve(port));
    });
  });
}
```

**Backend ready 輪詢（防 race condition）：**
```typescript
async function waitForBackend(url: string, timeoutMs = 30_000): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) return;
    } catch {}
    await new Promise(r => setTimeout(r, 500));
  }
  throw new Error(`Backend not ready after ${timeoutMs}ms: ${url}`);
}
```

**External service（若有）：**
若設定表裡標明有 external service 概念，啟動一個 dummy listener 在對應 port，讓測試不依賴環境裡剛好有什麼：
```typescript
// 在 test-ui/fixtures/dummy-external.ts
import * as http from 'http';

export function startDummyExternal(port: number): http.Server {
  const srv = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', role: 'external' }));
  });
  srv.listen(port);
  return srv;
}
```

---

## Phase 4：Spec 1 — App 開啟 Smoke

```typescript
// test-ui/01-app-opens.spec.ts
test('app opens without crashing', async ({ page }) => {
  const consoleErrors: string[] = [];
  const networkFails: string[] = [];

  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('response', res => {
    // 核心啟動端點（health、初始資料）才算致命
    if (res.status() >= 500 && isCoreEndpoint(res.url())) {
      networkFails.push(`${res.status()} ${res.url()}`);
    }
  });

  await page.goto(`http://127.0.0.1:${TEST_PORT}`);
  await page.waitForLoadState('networkidle', { timeout: 15_000 });

  // 截圖（無論成敗）
  await page.screenshot({
    path: `${SCREENSHOT_DIR}/01-app-opens.png`,
    fullPage: true,
  });

  // 檢查核心面板（從設定表的 core_panels 推斷）
  for (const panel of CORE_PANELS) {
    await expect(page.getByText(panel, { exact: false })).toBeVisible({ timeout: 5_000 });
  }

  // 無致命 console error
  expect(consoleErrors.filter(isFatal)).toHaveLength(0);
  // 無核心端點 500
  expect(networkFails).toHaveLength(0);
  // 無 ErrorBoundary
  await expect(page.getByText(/something went wrong|error boundary/i)).not.toBeVisible();
});
```

---

## Phase 5：Spec 2 — 全元素探索掃描

**這是探索式 smoke，目標是「發現崩潰」，不是「驗業務邏輯」。**

```typescript
// test-ui/02-element-explore.spec.ts
const ACTION_TIMEOUT = 5_000; // 超過就算 hang

test('explore all interactive elements', async ({ page }) => {
  const issues: { type: 'fatal' | 'warning'; msg: string }[] = [];

  page.on('pageerror', err => {
    issues.push({ type: 'fatal', msg: `[PAGE ERROR] ${err.message}` });
  });
  page.on('console', msg => {
    if (msg.type() === 'error') {
      issues.push({ type: 'fatal', msg: `[CONSOLE ERROR] ${msg.text()}` });
    } else if (msg.type() === 'warning') {
      issues.push({ type: 'warning', msg: `[CONSOLE WARN] ${msg.text()}` });
    }
  });
  page.on('response', res => {
    if (res.status() >= 500) {
      issues.push({ type: 'warning', msg: `[NET ${res.status()}] ${res.url()}` });
    }
  });

  await page.goto(`http://127.0.0.1:${TEST_PORT}`);
  await page.waitForLoadState('networkidle');

  // 找出所有可互動元素
  const interactables = await page.$$('button, [role="button"], input, select, textarea, a[href]');

  for (const el of interactables) {
    const tag = await el.evaluate(e => e.tagName.toLowerCase());
    const label = await el.evaluate(e =>
      e.getAttribute('aria-label') || e.textContent?.trim() || e.getAttribute('placeholder') || e.getAttribute('name') || 'unknown'
    );

    try {
      if (tag === 'input' || tag === 'textarea') {
        // 推斷合理的填充值
        const inputType = await el.getAttribute('type') || 'text';
        const placeholder = await el.getAttribute('placeholder') || '';
        const name = (await el.getAttribute('name') || '').toLowerCase();
        const value = inferInputValue(inputType, placeholder, name);
        await el.fill(value, { timeout: ACTION_TIMEOUT });
      } else if (tag === 'select') {
        const options = await el.$$('option');
        if (options.length > 1) await el.selectOption({ index: 1 }, { timeout: ACTION_TIMEOUT });
      } else {
        // button / link — 點擊但不導航離開主頁面
        await el.click({ timeout: ACTION_TIMEOUT, force: false });
        await page.waitForTimeout(300); // 等 UI 反應
        // 若跳走了就回來
        if (!page.url().includes(`127.0.0.1:${TEST_PORT}`)) {
          await page.goBack();
          await page.waitForLoadState('networkidle');
        }
      }
    } catch (e: any) {
      if (e.message?.includes('timeout')) {
        issues.push({ type: 'fatal', msg: `[HANG] ${tag} "${label}" timed out after ${ACTION_TIMEOUT}ms` });
      } else {
        issues.push({ type: 'warning', msg: `[SKIP] ${tag} "${label}": ${e.message}` });
      }
    }

    // 每次操作後截圖（只在有 fatal 時）
    const hasFatal = issues.some(i => i.type === 'fatal');
    if (hasFatal) {
      await page.screenshot({
        path: `${SCREENSHOT_DIR}/02-explore-fatal-${Date.now()}.png`,
        fullPage: true,
      });
    }
  }

  // 寫 log
  writeIssueLog(issues, `${LOG_DIR}/02-explore-issues.json`);

  // 只有致命級才讓測試紅燈
  const fatals = issues.filter(i => i.type === 'fatal');
  expect(fatals, `Fatal issues found:\n${fatals.map(i => i.msg).join('\n')}`).toHaveLength(0);
});

// 推斷輸入值的 helper
function inferInputValue(type: string, placeholder: string, name: string): string {
  if (type === 'email' || name.includes('email')) return 'test@example.com';
  if (type === 'password' || name.includes('password')) return 'Test1234!';
  if (type === 'number' || name.includes('port')) return '8080';
  if (type === 'url' || name.includes('url')) return 'http://localhost';
  if (name.includes('name') || placeholder.toLowerCase().includes('name')) return 'Test Name';
  if (name.includes('path') || placeholder.toLowerCase().includes('path')) return '/tmp/test-path';
  return 'test-value';
}
```

---

## Phase 6：Spec 3 — 功能開啟不卡死

```typescript
// test-ui/03-feature-hang.spec.ts
test('opening features does not hang', async ({ page }) => {
  await page.goto(`http://127.0.0.1:${TEST_PORT}`);
  await page.waitForLoadState('networkidle');

  // 找所有可能開啟新功能/頁面的按鈕（add, new, create, open, discover）
  const triggers = await page.$$('button, [role="button"]');

  for (const trigger of triggers) {
    const text = (await trigger.textContent() || '').toLowerCase();
    if (!/(add|new|create|open|discover|start|launch|connect)/i.test(text)) continue;

    const beforeUrl = page.url();
    const startTime = Date.now();

    try {
      await trigger.click({ timeout: ACTION_TIMEOUT });
      // 等待任何 modal/panel/navigation 出現或穩定
      await page.waitForLoadState('networkidle', { timeout: ACTION_TIMEOUT });

      const elapsed = Date.now() - startTime;
      if (elapsed > ACTION_TIMEOUT * 0.8) {
        // 接近超時，記為警告
        console.warn(`[SLOW] "${text}" took ${elapsed}ms`);
      }

      // 截圖
      await page.screenshot({
        path: `${SCREENSHOT_DIR}/03-feature-${text.replace(/\s+/g, '-')}-${Date.now()}.png`,
      });

      // 嘗試關閉（Escape / Cancel）
      await page.keyboard.press('Escape');
      await page.waitForTimeout(200);

    } catch (e: any) {
      if (e.message?.includes('timeout')) {
        throw new Error(`[HANG] Button "${text}" caused a hang`);
      }
    }
  }
});
```

---

## Phase 7：Spec 4 — Console / Network 完整記錄

```typescript
// test-ui/04-network-monitor.spec.ts
test('record all console and network activity', async ({ page }) => {
  const log: object[] = [];

  page.on('console', msg => log.push({ type: 'console', level: msg.type(), text: msg.text() }));
  page.on('request', req => log.push({ type: 'request', method: req.method(), url: req.url() }));
  page.on('response', res => log.push({ type: 'response', status: res.status(), url: res.url() }));
  page.on('pageerror', err => log.push({ type: 'pageerror', message: err.message, stack: err.stack }));

  await page.goto(`http://127.0.0.1:${TEST_PORT}`);
  await page.waitForLoadState('networkidle');

  // 做幾個基本互動讓 log 豐富一些
  await page.waitForTimeout(2_000);

  const today = new Date().toISOString().slice(0, 10);
  const fs = require('fs');
  fs.mkdirSync(`${LOG_DIR}`, { recursive: true });
  fs.writeFileSync(`${LOG_DIR}/04-network-log-${Date.now()}.json`, JSON.stringify(log, null, 2));

  await page.screenshot({ path: `${SCREENSHOT_DIR}/04-network-monitor.png`, fullPage: true });

  // 致命：核心端點 5xx
  const core5xx = log.filter((e: any) => e.type === 'response' && e.status >= 500 && isCoreEndpoint(e.url));
  expect(core5xx, `Core endpoints returned 5xx:\n${JSON.stringify(core5xx, null, 2)}`).toHaveLength(0);
});
```

---

## Phase 8：加入 package.json scripts

在前端的 `package.json` 加入（若尚未存在）：

```json
{
  "scripts": {
    "test:ui": "playwright test --config=structure-and-test-setup/test-ui/playwright.config.ts",
    "test:ui:headed": "playwright test --headed --config=structure-and-test-setup/test-ui/playwright.config.ts"
  }
}
```

---

## Phase 9：文件

建立 `docs/testing/ui-tests.md`：

```markdown
# UI 自動探索測試

## 執行方式
npm run test:ui           # headless
npm run test:ui:headed    # 有頭（debug 用）

## 覆蓋範圍
- App 開啟 smoke（無崩潰、主面板可見）
- 全元素探索（每個按鈕/輸入框都試一遍）
- 功能開啟不卡死
- Console / Network 完整記錄

## 截圖位置
structure-and-test-setup/test-logs/test-screen/<YYYY-MM-DD>/

## 測試 DB 設定
見 db-script/reset_test_db.py

## 致命 vs 警告 分級
見 AGENT_REFERENCE.md

## 已知限制
- 探索式填表可能觸發 validation error（預期，記為警告）
- 業務邏輯正確性不在此測試範圍，見 02-test-discovery.md
```

---

## Phase 10：建立階段驗證

```bash
# 確認 Playwright 安裝
npx playwright --version

# 確認 spec 可被列出
npx playwright test --list --config=structure-and-test-setup/test-ui/playwright.config.ts

# 確認截圖目錄可寫入
mkdir -p structure-and-test-setup/test-logs/test-screen/$(date +%Y-%m-%d)

# 試跑（建立階段只要跑得起來，不要求全綠）
npm run test:ui 2>&1 | tee structure-and-test-setup/test-logs/ui-setup-run.log
```

---

## 建立階段完成條件

- [ ] Playwright 已安裝且 `npx playwright --version` 有輸出
- [ ] `test-ui/` 裡有 4 個 spec 且 `--list` 能列出
- [ ] Playwright config 截圖輸出指向 `test-logs/test-screen/<YYYY-MM-DD>/`
- [ ] `docs/testing/ui-tests.md` 已建立
- [ ] `package.json` 有 `test:ui` script
- [ ] 測試環境與 production 完全隔離

> 此步驟完成後，進入 Loop 階段（見 `AGENT_REFERENCE.md`），反覆跑到致命級問題全清。
