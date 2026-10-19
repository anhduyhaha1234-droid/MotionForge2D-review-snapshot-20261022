import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { execSync } from "child_process";

const FIXTURE_DIR = path.join(__dirname, "fixtures");
const VIDEO_PATH = path.join(FIXTURE_DIR, "test-2s.mp4");

/* ── Setup ─────────────────────────────────────────────────────────────── */

test.beforeAll(() => {
  if (!fs.existsSync(FIXTURE_DIR)) fs.mkdirSync(FIXTURE_DIR, { recursive: true });
  if (!fs.existsSync(VIDEO_PATH)) {
    try {
      execSync(
        `ffmpeg -y -f lavfi -i "color=c=blue:s=320x240:d=2" -vf "drawtext=text='Test':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -pix_fmt yuv420p "${VIDEO_PATH}"`,
        { stdio: "ignore" },
      );
    } catch {
      console.warn("ffmpeg not available — fixture video not created");
    }
  }
});

/* ── GPU / SAM2 workflow ────────────────────────────────────────────────── */

test.describe("MotionForge 2D — GPU SAM2 Workflow @slow", () => {
  test("full SAM2 segmentation and propagation", async ({ page }) => {
    // Step 1: Open the app
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("MotionForge 2D");

    // Step 2: Create project and upload
    const nameInput = page.locator('input[type="text"]');
    await nameInput.clear();
    await nameInput.fill("GPU SAM2 Test");

    const fileInput = page.locator('input[type="file"][accept*=".mp4"]');
    await fileInput.setInputFiles(VIDEO_PATH);

    await page.getByRole("button", { name: /Bắt đầu/i }).click();

    // Step 3: Wait for ingest
    await expect(page.locator("text=Hoàn tất!")).toBeVisible({
      timeout: 120_000,
    });

    // Step 4: Should be on selection screen
    await expect(page.locator("text=Chọn vật thể")).toBeVisible({
      timeout: 10_000,
    });

    // Step 5: Click on canvas center to select object
    const canvas = page.locator("canvas");
    await expect(canvas).toBeVisible();
    await canvas.click({ position: { x: 160, y: 120 } });

    // Step 6: Preview mask — triggers SAM2 on GPU
    await page
      .getByRole("button", { name: /Xem mask/i })
      .click({ timeout: 5_000 });

    // Step 7: Wait for SAM2 to return mask (can be slow on GPU)
    // The button should show loading state
    await expect(page.locator("text=Đang tạo mask...")).toBeVisible({
      timeout: 5_000,
    });

    // Wait for mask to be generated (SAM2 can take 30-60s on first load)
    await expect(page.locator("text=Đang tạo mask...")).not.toBeVisible({
      timeout: 120_000,
    });

    // Step 8: Accept mask and propagate
    await page
      .getByRole("button", { name: /Chấp nhận/i })
      .click({ timeout: 5_000 });

    // Step 9: Wait for propagation (SAM2 video propagation)
    await expect(page.locator("text=Đang tách object...")).toBeVisible({
      timeout: 10_000,
    });

    // Wait for propagation to complete
    await expect(page.locator("text=Kết quả tách object")).toBeVisible({
      timeout: 300_000, // 5 minutes for full propagation
    });

    // Step 10: Verify gallery has tracked frames
    await expect(
      page.locator("text=Gallery frame đại diện"),
    ).toBeVisible({ timeout: 10_000 });

    // Step 11: Navigate to replacement and verify Konva preview
    await page
      .getByRole("button", { name: /Thay ảnh/i })
      .click({ timeout: 5_000 });

    await expect(page.locator("text=Thay thế vật thể")).toBeVisible();

    // Verify composite canvas exists
    await expect(
      page.locator('[data-testid="composite-canvas"]'),
    ).toBeVisible();

    // Step 12: Verify motion data is displayed
    await expect(page.locator("text=Motion data")).toBeVisible();

    // Step 13: Verify centroid and bbox info
    await expect(page.locator("text=Centroid:")).toBeVisible();
    await expect(page.locator("text=BBox:")).toBeVisible();

    // Step 14: Test preview modes
    for (const modeLabel of ["Ảnh gốc", "Mask", "Kết quả", "So sánh"]) {
      await page.getByRole("button", { name: modeLabel }).click();
      // Canvas should still be visible after mode change
      await expect(
        page.locator('[data-testid="composite-canvas"]'),
      ).toBeVisible();
    }
  });
});
