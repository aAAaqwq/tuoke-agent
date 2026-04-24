import { test, expect } from "@playwright/test";

test("submits prospect filters and opens report page", async ({ page }) => {
  await page.goto("/prospects");

  await page.getByLabel("行业").fill("跨境电商");
  await page.getByLabel("地区").fill("深圳,杭州");
  await page.getByLabel("角色").fill("创始人,销售总监");
  await page.getByLabel("数量").fill("20");
  await page.getByRole("button", { name: /生成线索报告/i }).click();

  await expect(page).toHaveURL(/industry=%E8%B7%A8%E5%A2%83%E7%94%B5%E5%95%86/);
  await expect(page).toHaveURL(/region=%E6%B7%B1%E5%9C%B3%2C%E6%9D%AD%E5%B7%9E/);
  await expect(page.getByRole("heading", { name: /线索采集任务/i })).toBeVisible();
  await expect(page.getByText(/深圳云帆 SaaS 科技/i)).toBeVisible();

  await page.getByRole("link", { name: /查看报告/i }).first().click();

  await expect(page).toHaveURL(/\/prospects\//);
  await expect(page.getByRole("heading", { name: /企业画像报告/i })).toBeVisible();
  await expect(page.getByText(/深圳云帆 SaaS 科技|深圳增长引擎软件/i)).toBeVisible();
});
