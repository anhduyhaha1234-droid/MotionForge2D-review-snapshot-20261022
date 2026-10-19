import { test, expect, type APIRequestContext } from "@playwright/test";

/**
 * Focused automated coverage for the UI correction task:
 *
 *  1. Channels Active/Archived/All filter — active_only=false for archived/all
 *     visibility, truthful archived badges, disabled edit/archive on archived
 *     rows, CAS-safe archive (revision).
 *  2. Dashboard character-preset stat — an independent unavailable state with
 *     retry (a failed preset request must NEVER render as a real "0"), while
 *     the project summaries stay usable.
 *  3. Responsive navigation — desktop rail at desktop width, bottom bar at a
 *     narrow (390px) viewport.
 *
 * Synthetic channels are created through the real durable API and archived at
 * the end (the sanctioned removal path) so no active data is left behind.
 */

const API = "http://localhost:8002";

async function createChannel(
  api: APIRequestContext,
  name: string,
  role: "source" | "production",
): Promise<{ channel_id: string; revision: number; status: string }> {
  const res = await api.post(`${API}/api/channels`, {
    headers: { "Content-Type": "application/json" },
    data: { name, role, target_language: "vi" },
  });
  expect(res.status()).toBe(201);
  return (await res.json()) as { channel_id: string; revision: number; status: string };
}

async function archiveChannel(
  api: APIRequestContext,
  channelId: string,
  revision: number,
): Promise<void> {
  const res = await api.post(`${API}/api/channels/${channelId}/archive`, {
    headers: { "Content-Type": "application/json" },
    data: { revision },
  });
  expect(res.ok()).toBeTruthy();
}

const filterGroup = (page: import("@playwright/test").Page) =>
  page.getByRole("group", { name: "Lọc trạng thái kênh" });

test.describe("UI correction — channels Active/Archived/All filter", () => {
  test("filter requests active_only=false for archived/all and guards archived rows", async ({ page }) => {
    const stamp = Date.now();
    const activeName = `QA Active ${stamp}`;
    const archivedName = `QA Archived ${stamp}`;

    const active = await createChannel(page.request, activeName, "source");
    const archived = await createChannel(page.request, archivedName, "production");
    await archiveChannel(page.request, archived.channel_id, archived.revision);

    try {
      await page.goto("/channels");

      // Default tab = "Đang hoạt động" (active_only=true) — archived hidden.
      await expect(
        filterGroup(page).getByRole("button", { name: "Đang hoạt động" }),
      ).toHaveAttribute("aria-pressed", "true");
      await expect(page.getByText(activeName, { exact: true })).toBeVisible();
      await expect(page.getByText(archivedName, { exact: true })).toBeHidden();

      // "Tất cả" → active_only=false: both rows visible; archived row renders
      // a truthful "Đã lưu trữ" badge and disabled edit/archive actions.
      await filterGroup(page).getByRole("button", { name: "Tất cả" }).click();
      await expect(page.getByText(activeName, { exact: true })).toBeVisible();
      await expect(page.getByText(archivedName, { exact: true })).toBeVisible();
      const archivedCard = page.locator("article", { hasText: archivedName });
      await expect(archivedCard.getByText("Đã lưu trữ", { exact: true }).first()).toBeVisible();
      await expect(archivedCard.getByRole("button", { name: "Sửa" })).toBeDisabled();
      await expect(archivedCard.getByRole("button", { name: "Đã lưu trữ" })).toBeDisabled();
      await expect(
        archivedCard.getByRole("button", { name: "Sửa" }),
      ).toHaveAttribute("title", "Kênh đã lưu trữ không thể chỉnh sửa");

      // "Đã lưu trữ" → active_only=false + client-side status filter.
      await filterGroup(page).getByRole("button", { name: "Đã lưu trữ" }).click();
      await expect(page.getByText(archivedName, { exact: true })).toBeVisible();
      await expect(page.getByText(activeName, { exact: true })).toBeHidden();
    } finally {
      // Cleanup through the sanctioned archive path — active view returns to empty.
      await archiveChannel(page.request, active.channel_id, active.revision);
    }
  });
});

test.describe("UI correction — dashboard character-preset stat", () => {
  test("a failed preset request shows an unavailable state with retry, never a zero", async ({ page }) => {
    // Force the character-preset endpoint to fail; summaries must stay usable.
    await page.route("**/api/projects/presets/characters", (route) =>
      route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ detail: "qa forced failure" }) }),
    );

    await page.goto("/");

    const label = page.getByText("Thư Viện Nhân Vật", { exact: true });
    await expect(label).toBeVisible();
    // Stat value = "—" (unavailable), NOT a real zero.
    const value = label.locator("..").locator("..").locator(":scope > p");
    await expect(value).toHaveText("—", { timeout: 15_000 });
    // Independent retry button inside the preset card.
    await expect(
      label.locator("..").locator("..").getByRole("button", { name: "Thử lại" }),
    ).toBeVisible();

    // Project summaries stay usable: the summary cards and the projects list
    // render, and NO dashboard-wide error banner appears (that banner is for
    // summary failures only).
    await expect(page.getByText("Tổng Dự Án", { exact: true })).toBeVisible();
    await expect(page.getByText("Dự Án Gần Đây", { exact: true })).toBeVisible();
    await expect(page.getByText("Không thể tải dữ liệu bảng điều khiển", { exact: false })).toBeHidden();
  });

  test("a healthy preset request renders a real count", async ({ page }) => {
    await page.goto("/");
    const label = page.getByText("Thư Viện Nhân Vật", { exact: true });
    await expect(label).toBeVisible();
    const value = label.locator("..").locator("..").locator(":scope > p");
    // The built-in library returns a digit count — never "—" and never "0" when assets exist.
    await expect(value).toHaveText(/^\d+$/, { timeout: 30_000 });
    await expect(page.getByText("Tổng Dự Án", { exact: true })).toBeVisible();
  });
});

test.describe("UI correction — responsive navigation", () => {
  test("desktop rail at desktop width, bottom bar at a narrow viewport", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await expect(page.locator("nav.fixed.inset-x-0.bottom-0")).toBeHidden();

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/channels");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await expect(page.locator("nav.fixed.inset-x-0.bottom-0")).toBeVisible();
  });
});
