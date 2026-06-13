/**
 * 资源管理两个页面的浏览器实测取证脚本（一次性脚本，非测试套件）
 *
 * 对真实 dev 环境的 /resource-quotas 与 /monitoring 做关键交互实测并截图。
 *
 * 运行: cd frontend && node e2e/scripts/capture-evidence.mjs
 *
 * 环境变量（均有默认值）:
 *   E2E_BASE_URL   目标环境，默认 dev ALB
 *   E2E_USERNAME   登录用户名，默认 admin
 *   E2E_PASSWORD   登录密码，默认 Admin123!
 *
 * 注意: 删除二次确认截图后会点「取消」，绝不真删 dev 数据。
 */

import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdir } from "node:fs/promises";

const __dirname = dirname(fileURLToPath(import.meta.url));

const BASE_URL =
  process.env.E2E_BASE_URL ||
  "http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com";
const USERNAME = process.env.E2E_USERNAME || "admin";
const PASSWORD = process.env.E2E_PASSWORD || "Admin123!";

// 截图输出目录: frontend/e2e/artifacts/resource-mgmt-evidence/
const ARTIFACT_DIR = join(
  __dirname,
  "..",
  "artifacts",
  "resource-mgmt-evidence",
);

/** 简单日志 */
const log = (msg) => console.log(`[capture] ${msg}`);
const warn = (msg) => console.warn(`[capture][WARN] ${msg}`);

async function shot(page, name, opts = {}) {
  const path = join(ARTIFACT_DIR, name);
  await page.screenshot({ path, ...opts });
  log(`截图已保存: ${name}`);
}

/** UI 登录: 参考 e2e/utils/auth.ts loginViaUI */
async function loginViaUI(page) {
  log(`导航到登录页并登录 (${USERNAME})`);
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });

  await page.locator("input").first().fill(USERNAME);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.getByRole("button", { name: "登录" }).click();

  await page.waitForURL((url) => !url.pathname.includes("/login"), {
    timeout: 20000,
  });
  await page.waitForLoadState("networkidle");
  log(`登录成功，当前 URL: ${page.url()}`);
}

async function main() {
  await mkdir(ARTIFACT_DIR, { recursive: true });
  log(`目标环境: ${BASE_URL}`);
  log(`截图目录: ${ARTIFACT_DIR}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // 记录页面控制台错误，便于发现真实问题
  const consoleErrors = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });
  page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));

  const findings = [];

  try {
    await loginViaUI(page);

    // ============================================================
    // 配额管理页 /resource-quotas
    // ============================================================
    log("=== 配额管理页 /resource-quotas ===");
    await page.goto(`${BASE_URL}/resource-quotas`, {
      waitUntil: "networkidle",
    });

    // 等待加载指示器消失 + 表格/空态出现
    await page
      .getByText("加载中...")
      .waitFor({ state: "hidden", timeout: 15000 })
      .catch(() => {});
    const quotaTable = page.locator("table").first();
    const quotaEmpty = page.getByText("暂无配置");
    const quotaError = page.getByText("加载失败");
    await Promise.race([
      quotaTable.waitFor({ state: "visible", timeout: 15000 }),
      quotaEmpty.waitFor({ state: "visible", timeout: 15000 }),
      quotaError.waitFor({ state: "visible", timeout: 15000 }),
    ]).catch(() => {});

    // 诊断: 行数 / 是否错误态
    const rowCount = await page.locator("table tbody tr").count();
    log(`配额列表行数: ${rowCount}`);
    if (await quotaError.isVisible().catch(() => false)) {
      findings.push("配额列表页出现「加载失败」错误态");
    }
    if (rowCount === 0) {
      findings.push("配额列表为空（0 行），删除确认截图可能无法产出");
    }

    // (1) 列表页全貌
    await shot(page, "quota-list.png", { fullPage: true });

    // (2) 新建配置 Modal 打开态
    log("点击「新建配置」打开 Modal");
    await page.getByRole("button", { name: "新建配置" }).click();
    // 等待表单 Modal 的配置名称输入框可见
    await page
      .locator('input[aria-label="配置名称"]')
      .waitFor({ state: "visible", timeout: 8000 })
      .catch(() => warn("配置名称输入框未在预期时间内出现"));
    await page.waitForTimeout(400); // 等 Modal 动画稳定
    await shot(page, "quota-create-modal.png");

    // 关闭新建 Modal（点表单内取消）
    const createModalCancel = page
      .getByRole("dialog")
      .getByRole("button", { name: "取消" })
      .first();
    await createModalCancel.click().catch(() => {});
    await page
      .locator('input[aria-label="配置名称"]')
      .waitFor({ state: "hidden", timeout: 8000 })
      .catch(() => {});

    // (3) 删除二次确认 Modal —— 截图后务必点取消，不真删
    if (rowCount > 0) {
      log("点击第一行「删除」打开确认框");
      const firstRow = page.locator("table tbody tr").first();
      // 操作列「编辑」「删除」并存，精确名匹配避免误点
      await firstRow.getByRole("button", { name: "删除" }).click();

      const deleteModal = page
        .getByRole("dialog")
        .filter({ hasText: "此操作不可撤销" });
      const deleteModalVisible = await deleteModal
        .waitFor({ state: "visible", timeout: 8000 })
        .then(() => true)
        .catch(() => false);

      if (deleteModalVisible) {
        await page.waitForTimeout(300);
        await shot(page, "quota-delete-confirm.png");
        // !!! 关键: 点取消，绝不真删 dev 数据 !!!
        log("删除确认截图完成 -> 点「取消」(不删数据)");
        await deleteModal.getByRole("button", { name: "取消" }).click();
        await deleteModal
          .waitFor({ state: "hidden", timeout: 8000 })
          .catch(() => {});
      } else {
        warn("删除确认 Modal 未出现（含「此操作不可撤销」），跳过该截图");
        findings.push(
          "删除二次确认 Modal 未按预期出现（未找到含「此操作不可撤销」的 dialog）",
        );
        // 兜底: 截当前态留证
        await shot(page, "quota-delete-confirm.png");
      }
    } else {
      warn("无数据行，无法触发删除确认；截图列表态兜底");
      await shot(page, "quota-delete-confirm.png", { fullPage: true });
    }

    // ============================================================
    // 资源监控页 /monitoring
    // ============================================================
    log("=== 资源监控页 /monitoring ===");
    await page.goto(`${BASE_URL}/monitoring`, { waitUntil: "networkidle" });

    // 等待标题 + loading 消失 + Tab/错误态
    await page
      .locator("h1")
      .filter({ hasText: "集群监控" })
      .waitFor({ state: "visible", timeout: 15000 })
      .catch(() => warn("未找到「集群监控」标题"));
    await page
      .getByText("加载中...")
      .waitFor({ state: "hidden", timeout: 25000 })
      .catch(() => {});

    const tabOverview = page.getByRole("tab", { name: "概览" });
    const monError = page.getByRole("button", { name: /重试|重新加载/ });
    await Promise.race([
      tabOverview.waitFor({ state: "visible", timeout: 15000 }),
      monError.waitFor({ state: "visible", timeout: 15000 }),
    ]).catch(() => {});

    if (await monError.isVisible().catch(() => false)) {
      findings.push("监控页出现错误态（重试按钮可见），集群数据可能未加载");
    }

    // (4) 概览 Tab —— 验证真实集群数据
    // 默认应停在概览 Tab；若不是则切过去
    if (
      (await tabOverview.getAttribute("aria-selected").catch(() => null)) !==
      "true"
    ) {
      await tabOverview.click().catch(() => {});
    }
    await page.waitForTimeout(600);

    // 诊断: 集群概览卡片是否含 ai-platform-dev-hyperpod
    const clusterCard = page
      .locator('[class*="container"]')
      .filter({ has: page.getByRole("heading", { name: "集群概览" }) });
    const clusterText = await clusterCard
      .textContent()
      .catch(() => "");
    const hasRealCluster = clusterText.includes("ai-platform-dev-hyperpod");
    log(
      `集群概览卡片文本片段: ${(clusterText || "(空)").slice(0, 200).replace(/\s+/g, " ")}`,
    );
    if (hasRealCluster) {
      log("✓ 概览含真实集群名 ai-platform-dev-hyperpod");
    } else {
      warn("概览未检出 ai-platform-dev-hyperpod，可能未拿到真实集群数据");
      findings.push(
        "监控概览卡片未检出集群名「ai-platform-dev-hyperpod」（文本: " +
          (clusterText || "(空)").slice(0, 120).replace(/\s+/g, " ") +
          "）",
      );
    }

    const utilCard = page
      .locator('[class*="container"]')
      .filter({ has: page.getByRole("heading", { name: "资源利用率" }) });
    const utilText = await utilCard.textContent().catch(() => "");
    log(
      `资源利用率卡片文本片段: ${(utilText || "(空)").slice(0, 200).replace(/\s+/g, " ")}`,
    );

    await shot(page, "monitoring-overview.png", { fullPage: true });

    // (5) 指标趋势 Tab
    log("切到「指标趋势」Tab");
    await page.getByRole("tab", { name: "指标趋势" }).click();
    await page.waitForTimeout(800); // 图表渲染
    const chartCount = await page
      .locator('[data-testid="metrics-chart"]')
      .count();
    log(`指标趋势图表数量: ${chartCount}`);
    await shot(page, "monitoring-metrics.png", { fullPage: true });

    // (6) Grafana Tab —— 验证降级文案
    log("切到「Grafana」Tab");
    await page.getByRole("tab", { name: "Grafana" }).click();
    await page.waitForTimeout(500);
    const grafanaFallback = page.getByText("Grafana 监控大盘未启用");
    const hasGrafanaFallback = await grafanaFallback
      .isVisible()
      .catch(() => false);
    if (hasGrafanaFallback) {
      log("✓ Grafana 降级文案可见: 「Grafana 监控大盘未启用」");
    } else {
      warn("未检出 Grafana 降级文案「Grafana 监控大盘未启用」");
      findings.push("Grafana Tab 未检出降级文案「Grafana 监控大盘未启用」");
    }
    await shot(page, "monitoring-grafana-degraded.png", { fullPage: true });

    // (7) 告警 Tab —— 验证空态
    log("切到「告警」Tab");
    await page.getByRole("tab", { name: /^告警/ }).click();
    await page.waitForTimeout(500);
    const alertsEmpty = page.getByText("暂无告警");
    const hasAlertsEmpty = await alertsEmpty.isVisible().catch(() => false);
    if (hasAlertsEmpty) {
      log("✓ 告警空态可见: 「暂无告警」");
    } else {
      warn("未检出告警空态「暂无告警」（可能存在告警或文案不同）");
      findings.push("告警 Tab 未检出空态文案「暂无告警」");
    }
    await shot(page, "monitoring-alerts-empty.png", { fullPage: true });

    // ============================================================
    // 总结
    // ============================================================
    log("==================== 取证总结 ====================");
    if (consoleErrors.length) {
      warn(`页面控制台错误 ${consoleErrors.length} 条（前 5 条）:`);
      consoleErrors.slice(0, 5).forEach((e) => warn(`  - ${e}`));
    } else {
      log("无页面控制台错误");
    }
    if (findings.length) {
      warn("发现以下需关注项:");
      findings.forEach((f) => warn(`  - ${f}`));
    } else {
      log("✓ 所有关键交互与文案均符合预期，未发现异常");
    }
  } catch (err) {
    console.error("[capture][ERROR] 脚本执行异常:", err);
    // 异常时尽量截当前页面留证
    await shot(page, "ERROR-last-state.png", { fullPage: true }).catch(
      () => {},
    );
    process.exitCode = 1;
  } finally {
    await browser.close();
    log("浏览器已关闭");
  }
}

main();
